from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from model.recommend import recommend_pitch


NOTEBOOK_PATH = Path("/Users/haydenkellington/Downloads/Spring26BaseballProj_FINAL_(7).ipynb")
WEBSITE_PITCHES = ["FF", "SI", "FC", "SL", "ST", "CU", "CH", "FS"]


def read_notebook_outputs() -> str:
    nb = json.loads(NOTEBOOK_PATH.read_text())
    chunks: list[str] = []
    for cell in nb.get("cells", []):
        for output in cell.get("outputs", []):
            if "text" in output:
                chunks.append("".join(output["text"]))
            data = output.get("data", {})
            if "text/plain" in data:
                chunks.append("".join(data["text/plain"]))
    return "\n".join(chunks)


def parse_final7_tunneling_table(outputs: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pitch_pattern = "|".join(re.escape(pitch) for pitch in WEBSITE_PITCHES)
    pattern = re.compile(
        rf"^({pitch_pattern})\s+"
        r"(?P<memoryless>[A-Z]+)\s+(?P<memoryless_q>-?\d+\.\d+)\s+"
        r"(?P<augmented>[A-Z]+)\s+(?P<augmented_q>-?\d+\.\d+)",
        flags=re.MULTILINE,
    )

    for match in pattern.finditer(outputs):
        rows.append(
            {
                "prev_pitch": match.group(1),
                "final7_recommended_pitch": match.group("augmented"),
                "final7_q": float(match.group("augmented_q")),
                "final7_memoryless_pitch": match.group("memoryless"),
                "final7_memoryless_q": float(match.group("memoryless_q")),
            }
        )

    return rows


def current_dashboard_recommendation(prev_pitch: str) -> dict[str, Any]:
    payload = {
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
    return recommend_pitch(payload)


def main() -> int:
    outputs = read_notebook_outputs()
    final7_rows = parse_final7_tunneling_table(outputs)

    if not final7_rows:
        print("No FINAL_(7) tunneling table rows found in notebook outputs.")
        return 1

    print("Dashboard recommendation comparison")
    print("State: 0-2 count, 0 outs, bases empty, RHB vs RHP")
    print("Available pitches:", ", ".join(WEBSITE_PITCHES))
    print("FS policy: treated as allowed for the website and future FINAL_(7) export.")
    print()
    print(
        f"{'Prev':<6} {'Current':<9} {'Final7':<8} {'Same?':<6} "
        f"{'Current Q':>10} {'Final7 Q':>10} {'Current dRE':>12}"
    )
    print("-" * 78)

    same = 0
    differences: list[dict[str, Any]] = []
    for row in final7_rows:
        current = current_dashboard_recommendation(row["prev_pitch"])
        current_pitch = current["recommended_pitch"]
        final7_pitch = row["final7_recommended_pitch"]
        is_same = current_pitch == final7_pitch
        same += int(is_same)
        if not is_same:
            differences.append(
                {
                    "prev_pitch": row["prev_pitch"],
                    "current": current_pitch,
                    "final7": final7_pitch,
                }
            )
        print(
            f"{row['prev_pitch']:<6} {current_pitch:<9} {final7_pitch:<8} "
            f"{'yes' if is_same else 'no':<6} "
            f"{current['best_q_value']:>10.4f} {row['final7_q']:>10.4f} "
            f"{current['best_expected_delta_run_exp']:>12.3f}"
        )

    total = len(final7_rows)
    print()
    print(f"Same recommendation: {same}/{total}")
    print(f"Different recommendation: {total - same}/{total}")
    if differences:
        print("Differences:", differences)

    print()
    print("Notes:")
    print("- FINAL_(7) values come from the notebook's printed tunneling table, not a saved full q_table artifact.")
    print("- The parser includes FS when FS rows exist in the notebook output.")
    print("- The current FINAL_(7) printed table has no FS row, so this is not a full FS-inclusive dashboard comparison yet.")
    print("- Current values come from the live backend q_table.pkl through recommend_pitch().")
    print("- A full FS-inclusive dashboard-vs-dashboard comparison requires exporting FINAL_(7) to q_table_final7.pkl first.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
