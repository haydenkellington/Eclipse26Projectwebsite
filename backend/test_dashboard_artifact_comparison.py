from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

from model.encoder import encode_state
from model.pitch_mappings import PITCHES
from model.recommend import _fallback_q_value


CURRENT_Q_TABLE = Path("model/q_table.pkl")
FINAL7_Q_TABLE = Path("model/q_table_final7_website.pkl")
WEBSITE_PITCHES = list(PITCHES)


def load_q_table(path: Path) -> dict[str, dict[str, float]]:
    with path.open("rb") as file:
        return pickle.load(file)


def recommendation_from_table(q_table: dict[str, dict[str, float]], payload: dict[str, Any]) -> dict[str, Any]:
    state_key = encode_state(payload)
    available = payload["available_pitches"]
    rows = []

    for pitch in available:
        q_value = q_table.get(state_key, {}).get(pitch)
        observed = q_value is not None
        if q_value is None:
            q_value = _fallback_q_value(state_key, pitch)
        rows.append({"pitch": pitch, "q": float(q_value), "observed": observed})

    best = max(rows, key=lambda row: row["q"])
    return {
        "state_key": state_key,
        "pitch": best["pitch"],
        "q": best["q"],
        "expected_dre": round(-best["q"], 3),
        "observed": best["observed"],
        "rows": rows,
    }


def test_payloads() -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []

    # Direct tunneling check: same state the notebook table used, now with FS included.
    for prev_pitch in WEBSITE_PITCHES:
        payloads.append(
            {
                "label": f"0-2 empty R/R prev {prev_pitch}",
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

    # Broader common dashboard states.
    for balls, strikes, outs, bases, batter, pitcher, prev in [
        (1, 2, 1, (True, False, False), "R", "L", "FF"),
        (2, 1, 0, (False, True, False), "L", "R", "SL"),
        (3, 2, 2, (True, True, False), "R", "R", "CH"),
        (0, 1, 0, (False, False, False), "L", "L", "SI"),
        (1, 1, 1, (False, False, True), "R", "R", "FS"),
        (2, 2, 2, (True, False, True), "L", "L", "CU"),
    ]:
        on_1b, on_2b, on_3b = bases
        payloads.append(
            {
                "label": f"{balls}-{strikes} outs{outs} bases{int(on_1b)}{int(on_2b)}{int(on_3b)} {batter}/{pitcher} prev {prev}",
                "balls": balls,
                "strikes": strikes,
                "outs": outs,
                "on_1b": on_1b,
                "on_2b": on_2b,
                "on_3b": on_3b,
                "batter_hand": batter,
                "pitcher_hand": pitcher,
                "prev_pitch": prev,
                "available_pitches": WEBSITE_PITCHES,
            }
        )

    return payloads


def print_comparison(title: str, rows: list[dict[str, Any]]) -> None:
    print(title)
    print(
        f"{'State':<34} {'Current':<8} {'New':<8} {'Same?':<6} "
        f"{'Cur Q':>8} {'New Q':>8} {'Cur Obs':>7} {'New Obs':>7}"
    )
    print("-" * 96)
    for row in rows:
        print(
            f"{row['label']:<34} {row['current_pitch']:<8} {row['new_pitch']:<8} "
            f"{'yes' if row['same'] else 'no':<6} "
            f"{row['current_q']:>8.4f} {row['new_q']:>8.4f} "
            f"{str(row['current_observed']):>7} {str(row['new_observed']):>7}"
        )


def main() -> int:
    if not FINAL7_Q_TABLE.exists():
        print(f"Missing {FINAL7_Q_TABLE}. Run train_final7_website_artifact.py first.")
        return 1

    current = load_q_table(CURRENT_Q_TABLE)
    final7 = load_q_table(FINAL7_Q_TABLE)
    rows = []

    for payload in test_payloads():
        current_rec = recommendation_from_table(current, payload)
        new_rec = recommendation_from_table(final7, payload)
        rows.append(
            {
                "label": payload["label"],
                "current_pitch": current_rec["pitch"],
                "new_pitch": new_rec["pitch"],
                "same": current_rec["pitch"] == new_rec["pitch"],
                "current_q": current_rec["q"],
                "new_q": new_rec["q"],
                "current_observed": current_rec["observed"],
                "new_observed": new_rec["observed"],
            }
        )

    tunneling_rows = rows[: len(WEBSITE_PITCHES)]
    broad_rows = rows[len(WEBSITE_PITCHES) :]
    print_comparison("Current q_table.pkl vs FS-inclusive FINAL_(7) artifact", tunneling_rows)
    same_tunnel = sum(row["same"] for row in tunneling_rows)
    print(f"\nTunneling states same: {same_tunnel}/{len(tunneling_rows)}")
    print(f"Tunneling states different: {len(tunneling_rows) - same_tunnel}/{len(tunneling_rows)}\n")

    print_comparison("Broader common states", broad_rows)
    same_broad = sum(row["same"] for row in broad_rows)
    print(f"\nBroader states same: {same_broad}/{len(broad_rows)}")
    print(f"Broader states different: {len(broad_rows) - same_broad}/{len(broad_rows)}")
    print()
    print(f"Current artifact states: {len(current):,}")
    print(f"FS-inclusive FINAL_(7) artifact states: {len(final7):,}")
    print("New artifact is separate and does not replace the live dashboard model.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
