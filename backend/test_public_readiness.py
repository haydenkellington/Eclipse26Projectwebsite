from __future__ import annotations

from copy import deepcopy

from fastapi import HTTPException
from pydantic import ValidationError

from app import RecommendationRequest, health, pitches, recommend as app_recommend
from model.pitch_mappings import PITCHES


WEBSITE_PITCHES = ["FF", "SI", "FC", "SL", "ST", "CU", "CH", "FS"]

BASE_PAYLOAD = {
    "balls": 1,
    "strikes": 2,
    "outs": 1,
    "on_1b": True,
    "on_2b": False,
    "on_3b": False,
    "batter_hand": "R",
    "pitcher_hand": "L",
    "prev_pitch": "FF",
    "available_pitches": ["FF", "SL", "CH"],
}


def recommend(payload: dict) -> tuple[int, dict]:
    try:
        request = RecommendationRequest.model_validate(payload)
        return 200, app_recommend(request)
    except ValidationError as exc:
        return 422, {"detail": exc.errors()}
    except HTTPException as exc:
        return exc.status_code, {"detail": exc.detail}


def assert_valid_recommendation(label: str, payload: dict) -> dict:
    status, body = recommend(payload)
    assert status == 200, f"{label}: expected 200, got {status}: {body}"

    available = set(payload["available_pitches"])
    assert body["recommended_pitch"] in available, f"{label}: recommendation outside selected arsenal"
    assert body["recommended_pitch"] in PITCHES, f"{label}: unsupported recommended pitch"
    assert body["best_overall_pitch"] in PITCHES, f"{label}: unsupported best overall pitch"
    assert body["q_source"] in {"q_table", "deterministic_fallback"}, f"{label}: unexpected q_source"
    assert len(body["comparison"]) == len(PITCHES), f"{label}: comparison pitch count changed"

    comparison_pitches = {row["pitch"] for row in body["comparison"]}
    assert comparison_pitches == set(PITCHES), f"{label}: comparison missing pitch rows"

    q_values = [row["q_value"] for row in body["comparison"]]
    assert q_values == sorted(q_values, reverse=True), f"{label}: comparison not sorted by Q-value"

    weights = sum(row["model_weight"] for row in body["comparison"])
    assert 0.98 <= weights <= 1.02, f"{label}: model weights should sum near 1, got {weights}"

    for row in body["comparison"]:
        assert row["expected_delta_run_exp_from_q"] == round(-row["q_value"], 3), (
            f"{label}: model dRE should be negative Q for {row['pitch']}"
        )
        assert 0 <= row["whiff_rate"] <= 1, f"{label}: whiff rate out of range for {row['pitch']}"
        assert 0 <= row["mlb_frequency"] <= 1, f"{label}: MLB frequency out of range for {row['pitch']}"
        assert row["sample_size"] >= 0, f"{label}: negative sample size for {row['pitch']}"
        state_sample_size = row.get("state_sample_size", row["sample_size"])
        assert state_sample_size >= row["sample_size"], (
            f"{label}: state sample smaller than pitch sample for {row['pitch']}"
        )

    return body


def main() -> int:
    failures: list[str] = []
    checked: list[tuple[str, str, str, str | None, int]] = []

    def run_case(label: str, payload: dict) -> None:
        try:
            body = assert_valid_recommendation(label, payload)
            checked.append(
                (
                    label,
                    body["recommended_pitch"],
                    body["best_overall_pitch"],
                    body["best_unavailable_pitch"],
                    body["sample_size"],
                )
            )
        except AssertionError as exc:
            failures.append(str(exc))

    cases: list[tuple[str, dict]] = []

    for prev_pitch in WEBSITE_PITCHES:
        payload = deepcopy(BASE_PAYLOAD)
        payload.update(
            {
                "balls": 0,
                "strikes": 2,
                "outs": 0,
                "on_1b": False,
                "on_2b": False,
                "on_3b": False,
                "batter_hand": "R",
                "pitcher_hand": "R",
                "prev_pitch": prev_pitch,
                "available_pitches": WEBSITE_PITCHES,
            }
        )
        cases.append((f"0-2 empty R/R after {prev_pitch}, full arsenal", payload))

    varied_states = [
        ("default limited arsenal", {}),
        ("bases loaded full count L/R", {"balls": 3, "strikes": 2, "outs": 2, "on_1b": True, "on_2b": True, "on_3b": True, "batter_hand": "L", "pitcher_hand": "R", "prev_pitch": "CH", "available_pitches": WEBSITE_PITCHES}),
        ("runner on second 2-1 L/R", {"balls": 2, "strikes": 1, "outs": 0, "on_1b": False, "on_2b": True, "on_3b": False, "batter_hand": "L", "pitcher_hand": "R", "prev_pitch": "SL", "available_pitches": ["FF", "SL", "CH", "FS"]}),
        ("runner on third 1-1 R/R FS selected", {"balls": 1, "strikes": 1, "outs": 1, "on_1b": False, "on_2b": False, "on_3b": True, "batter_hand": "R", "pitcher_hand": "R", "prev_pitch": "FS", "available_pitches": ["FS"]}),
        ("0-0 with previous pitch FF", {"balls": 0, "strikes": 0, "outs": 0, "on_1b": False, "on_2b": False, "on_3b": False, "batter_hand": "R", "pitcher_hand": "R", "prev_pitch": "FF", "available_pitches": WEBSITE_PITCHES}),
        ("unavailable best pitch limited arsenal", {"balls": 1, "strikes": 2, "outs": 1, "on_1b": True, "on_2b": False, "on_3b": False, "batter_hand": "R", "pitcher_hand": "L", "prev_pitch": "FF", "available_pitches": ["FF", "SL", "CH"]}),
        ("single available CH", {"balls": 3, "strikes": 1, "outs": 0, "on_1b": True, "on_2b": False, "on_3b": True, "batter_hand": "L", "pitcher_hand": "L", "prev_pitch": "CU", "available_pitches": ["CH"]}),
    ]

    for label, overrides in varied_states:
        payload = deepcopy(BASE_PAYLOAD)
        payload.update(overrides)
        cases.append((label, payload))

    for label, payload in cases:
        run_case(label, payload)

    validation_cases = [
        ("no previous pitch is allowed by API for frontend message state", {**BASE_PAYLOAD, "prev_pitch": None}, 200),
        ("empty arsenal rejected", {**BASE_PAYLOAD, "available_pitches": []}, 422),
        ("unsupported-only arsenal rejected", {**BASE_PAYLOAD, "available_pitches": ["KN"]}, 400),
        ("invalid balls rejected", {**BASE_PAYLOAD, "balls": 4}, 422),
        ("invalid handedness rejected", {**BASE_PAYLOAD, "batter_hand": "S"}, 422),
    ]

    for label, payload, expected_status in validation_cases:
        status, body = recommend(payload)
        if status != expected_status:
            failures.append(f"{label}: expected {expected_status}, got {status}: {body}")
        else:
            checked.append((label, f"HTTP {status}", "-", None, 0))

    if health().get("status") != "ok":
        failures.append("health endpoint function failed")
    if {row["code"] for row in pitches()} != set(PITCHES):
        failures.append("pitches endpoint function returned an unexpected pitch set")

    print("Public readiness API matrix")
    print("-" * 88)
    print(f"{'Case':50} {'Rec':>5} {'Best':>5} {'Unavailable':>11} {'N':>7}")
    print("-" * 88)
    for label, rec, best, unavailable, sample_size in checked:
        print(f"{label[:50]:50} {rec:>5} {best:>5} {str(unavailable or '-'):>11} {sample_size:>7}")

    if failures:
        print("\nFailures")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"\nPASS: {len(checked)} cases checked, 0 failures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
