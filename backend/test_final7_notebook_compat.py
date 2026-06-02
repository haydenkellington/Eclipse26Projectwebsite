from __future__ import annotations

import importlib.util
import json
import pickle
import re
import tempfile
from pathlib import Path
from typing import Any

from model.pitch_mappings import PITCHES


NOTEBOOK_PATH = Path("/Users/haydenkellington/Downloads/Spring26BaseballProj_FINAL_(7).ipynb")
EXPORT_MODULE_PATH = Path(__file__).resolve().parent / "export_q_artifacts.py"
CURRENT_Q_TABLE_PATH = Path(__file__).resolve().parent / "model" / "q_table.pkl"
WEBSITE_PITCH_SET = set(PITCHES)


def load_export_module() -> Any:
    spec = importlib.util.spec_from_file_location("export_q_artifacts", EXPORT_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load export_q_artifacts.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_notebook() -> dict[str, Any]:
    return json.loads(NOTEBOOK_PATH.read_text())


def notebook_text(nb: dict[str, Any]) -> str:
    return "\n".join("".join(cell.get("source", [])) for cell in nb.get("cells", []))


def notebook_outputs(nb: dict[str, Any]) -> str:
    chunks: list[str] = []
    for cell in nb.get("cells", []):
        for output in cell.get("outputs", []):
            if "text" in output:
                chunks.append("".join(output["text"]))
            data = output.get("data", {})
            if "text/plain" in data:
                chunks.append("".join(data["text/plain"]))
    return "\n".join(chunks)


def result(name: str, status: str, detail: str) -> dict[str, str]:
    return {"test": name, "status": status, "detail": detail}


def hand_from_righty(value: int) -> str:
    return "R" if int(value) == 1 else "L"


def final7_state_key(state: tuple[Any, ...]) -> str:
    balls, strikes, outs, on_1b, on_2b, on_3b, batter_righty, pitcher_righty, prev_pitch = state
    prev = "NONE" if prev_pitch == -1 or prev_pitch == "-1" else str(prev_pitch)
    bases = f"{int(on_1b)}{int(on_2b)}{int(on_3b)}"

    return "|".join(
        [
            f"b{int(balls)}",
            f"s{int(strikes)}",
            f"o{int(outs)}",
            f"bases{bases}",
            f"bh{hand_from_righty(batter_righty)}",
            f"ph{hand_from_righty(pitcher_righty)}",
            f"prev{prev}",
        ]
    )


def main() -> int:
    nb = read_notebook()
    source = notebook_text(nb)
    outputs = notebook_outputs(nb)
    export_module = load_export_module()

    results: list[dict[str, str]] = []

    results.append(
        result(
            "notebook_loads",
            "PASS",
            f"Loaded {NOTEBOOK_PATH.name} with {len(nb.get('cells', []))} cells.",
        )
    )

    state_includes_outs = bool(
        re.search(
            r"STATE_COLS\s*=\s*\[.*?'balls'.*?'strikes'.*?'outs'",
            source,
            flags=re.DOTALL,
        )
    )
    results.append(
        result(
            "final7_augmented_state_shape",
            "PASS" if state_includes_outs and "aug_state_arr.shape[1]}D" in source else "WARN",
            "Final notebook state includes outs before appending previous pitch, so augmented states are 9D.",
        )
    )

    action_matches = re.findall(r"^\s+\d+:\s+([A-Z]+)\s*$", outputs, flags=re.MULTILINE)
    notebook_pitch_types = sorted(set(action_matches))
    website_pitch_types = sorted(PITCHES)
    unsupported = sorted(set(notebook_pitch_types) - set(website_pitch_types))
    missing_from_notebook = sorted(set(website_pitch_types) - set(notebook_pitch_types))
    results.append(
        result(
            "pitch_set_compatibility",
            "WARN" if unsupported or missing_from_notebook else "PASS",
            (
                f"Notebook actions={notebook_pitch_types}; website supports={website_pitch_types}; "
                f"unsupported in website={unsupported}; website-only={missing_from_notebook}."
            ),
        )
    )

    results.append(
        result(
            "website_pitch_selection_keeps_fs",
            "PASS" if "FS" in WEBSITE_PITCH_SET else "FAIL",
            f"Website pitch filter for the upgrade keeps {sorted(WEBSITE_PITCH_SET)}, including FS.",
        )
    )

    primary_match = re.search(r"Primary pitch types for display.*?:\s*(\[[^\]]+\])", outputs)
    primary_detail = primary_match.group(1) if primary_match else "not found"
    results.append(
        result(
            "display_pitch_filter",
            "WARN" if "FS" not in primary_detail else "PASS",
            f"Notebook primary display pitches are {primary_detail}; website currently includes FS.",
        )
    )

    class DummyAgent8D:
        Q = {
            ((1, 2, 1, 0, 0, 1, 0, 6), 14): 0.123,
        }

    class DummyAgent9D:
        Q = {
            ((1, 2, 1, 1, 0, 0, 1, 0, 6), 14): 0.123,
            ((1, 2, 1, 1, 0, 0, 1, 0, 6), 8): 0.111,
            ((1, 2, 1, 1, 0, 0, 1, 0, 6), 10): 0.999,
            ((1, 2, 1, 1, 0, 0, 1, 0, 10), 14): 0.777,
        }

    idx_to_pitch = {6: "FF", 8: "FS", 10: "KN", 14: "SL"}

    with tempfile.TemporaryDirectory() as tmpdir:
        old_path = Path(tmpdir) / "old.pkl"
        old_table = export_module.export_augmented_q_table(DummyAgent8D(), idx_to_pitch, old_path)
        old_keys = list(old_table)
        results.append(
            result(
                "current_export_accepts_old_state",
                "PASS" if old_keys and old_path.exists() else "FAIL",
                f"Old 8D augmented state exported to key {old_keys[0] if old_keys else 'none'}.",
            )
        )

        new_path = Path(tmpdir) / "q_table_final7_preview.pkl"
        try:
            final7_table = export_module.export_augmented_q_table(DummyAgent9D(), idx_to_pitch, new_path)
        except Exception as exc:  # noqa: BLE001 - diagnostic script reports exact incompatibility.
            results.append(
                result(
                    "current_export_accepts_final7_state",
                    "FAIL",
                    f"Current export helper rejects final notebook 9D state: {type(exc).__name__}: {exc}",
                )
            )
            final7_table = {}
        else:
            results.append(
                result(
                    "current_export_accepts_final7_state",
                    "PASS",
                    "Current export helper accepted a 9D final-notebook style state.",
                )
            )

        final7_pitches = sorted({pitch for rows in final7_table.values() for pitch in rows})
        final7_keys = list(final7_table)
        results.append(
            result(
                "final7_exporter_writes_api_state_key",
                "PASS" if new_path.exists() and "b1|s2|o1|bases100|bhR|phL|prevFF" in final7_table else "FAIL",
                f"Final7 exporter wrote {len(final7_table)} state key(s); keys={final7_keys}.",
            )
        )
        results.append(
            result(
                "final7_exporter_filters_pitches",
                "PASS" if final7_pitches == ["FS", "SL"] else "FAIL",
                f"Final7 exporter kept website pitches {final7_pitches} and dropped unsupported selected pitch KN.",
            )
        )
        results.append(
            result(
                "final7_exporter_filters_unsupported_prev_pitch",
                "PASS" if all("prevKN" not in key for key in final7_keys) else "FAIL",
                f"Final7 exporter skipped unsupported previous-pitch states; keys={final7_keys}.",
            )
        )
        preview_state = "b1|s2|o1|bases100|bhR|phL|prevFF"
        preview_available = {"FF", "SL", "FS"}
        preview_rows = final7_table.get(preview_state, {})
        preview_candidates = {
            pitch: q_value
            for pitch, q_value in preview_rows.items()
            if pitch in preview_available
        }
        preview_recommendation = max(preview_candidates, key=preview_candidates.get) if preview_candidates else None
        results.append(
            result(
                "final7_recommendation_preview",
                "PASS" if preview_recommendation == "SL" else "FAIL",
                (
                    f"For {preview_state} with available {sorted(preview_available)}, "
                    f"preview recommendation={preview_recommendation}; candidates={preview_candidates}."
                ),
            )
        )

    has_first_pitch_sentinel = "prev_pitch = -1 sentinel" in source and "fillna(-1)" in source
    results.append(
        result(
            "first_pitch_state_support",
            "PASS" if has_first_pitch_sentinel else "WARN",
            "Final notebook models first pitches with prev_pitch=-1 sentinel.",
        )
    )

    evaluation_uses_q_advantage = "q_advantages[i] = q_agent - q_mlb" in source
    results.append(
        result(
            "evaluation_metric_framing",
            "WARN" if evaluation_uses_q_advantage else "PASS",
            "Evaluation is fitted-Q advantage, not direct proof of real-world outperformance.",
        )
    )

    if CURRENT_Q_TABLE_PATH.exists():
        with CURRENT_Q_TABLE_PATH.open("rb") as file:
            current_q_table = pickle.load(file)
        current_pitches = sorted({pitch for rows in current_q_table.values() for pitch in rows})
        results.append(
            result(
                "current_site_artifact_pitch_set",
                "PASS" if set(current_pitches).issubset(WEBSITE_PITCH_SET) else "WARN",
                f"Current q_table.pkl has {len(current_q_table):,} states and pitches {current_pitches}.",
            )
        )
    else:
        results.append(
            result(
                "current_site_artifact_pitch_set",
                "WARN",
                "Current q_table.pkl was not found, so no current artifact comparison was possible.",
            )
        )

    print("Final notebook compatibility tests\n")
    for item in results:
        print(f"[{item['status']}] {item['test']}: {item['detail']}")

    failed = [item for item in results if item["status"] == "FAIL"]
    warned = [item for item in results if item["status"] == "WARN"]
    passed = len(results) - len(failed) - len(warned)
    print(f"\nSummary: {len(failed)} fail, {len(warned)} warn, {passed} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
