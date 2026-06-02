"""Export trained notebook Q-values into the backend artifact format.

Run this from a notebook after training `agent_aug` and creating the pitch maps:

    from export_q_artifacts import export_augmented_q_table
    export_augmented_q_table(agent_aug, IDX_TO_PITCH)

The API expects:

    model/q_table.pkl == dict[state_key][pitch_code] = q_value
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

DEFAULT_ALLOWED_PITCHES = ("FF", "SI", "FC", "SL", "ST", "CU", "CH", "FS")


def _hand_from_righty(value: int) -> str:
    return "R" if int(value) == 1 else "L"


def _state_key_from_augmented_state(state: tuple[Any, ...]) -> str:
    balls, strikes, outs, on_1b, on_2b, on_3b, batter_righty, pitcher_righty, prev_pitch = state
    bases = f"{int(on_1b)}{int(on_2b)}{int(on_3b)}"
    prev = "NONE" if prev_pitch == -1 or prev_pitch == "-1" else str(prev_pitch)

    return "|".join(
        [
            f"b{int(balls)}",
            f"s{int(strikes)}",
            f"o{int(outs)}",
            f"bases{bases}",
            f"bh{_hand_from_righty(batter_righty)}",
            f"ph{_hand_from_righty(pitcher_righty)}",
            f"prev{prev}",
        ]
    )


def _normalize_augmented_state(
    state: tuple[Any, ...],
    idx_to_pitch: dict[int, str],
    outs_values: tuple[int, ...],
) -> list[tuple[Any, ...]]:
    """Return API-shaped states from old 8D or FINAL_(7) 9D notebook states."""
    if len(state) == 8:
        balls, strikes, on_1b, on_2b, on_3b, batter_righty, pitcher_righty, prev_pitch = state
        prev = "NONE" if int(prev_pitch) == -1 else idx_to_pitch[int(prev_pitch)]
        return [
            (balls, strikes, outs, on_1b, on_2b, on_3b, batter_righty, pitcher_righty, prev)
            for outs in outs_values
        ]

    if len(state) == 9:
        balls, strikes, outs, on_1b, on_2b, on_3b, batter_righty, pitcher_righty, prev_pitch = state
        prev = "NONE" if int(prev_pitch) == -1 else idx_to_pitch[int(prev_pitch)]
        return [(balls, strikes, outs, on_1b, on_2b, on_3b, batter_righty, pitcher_righty, prev)]

    raise ValueError(f"Expected augmented state with 8 or 9 values, got {len(state)}")


def export_augmented_q_table(
    agent: Any,
    idx_to_pitch: dict[int, str],
    output_path: str | Path = "model/q_table.pkl",
    outs_values: tuple[int, ...] = (0, 1, 2),
    allowed_pitches: tuple[str, ...] | set[str] | None = DEFAULT_ALLOWED_PITCHES,
) -> dict[str, dict[str, float]]:
    """Convert notebook `agent_aug.Q` into `dict[state_key][pitch_code]`.

    Supports both:
      - older 8D augmented states without outs, copied across `outs_values`
      - FINAL_(7)-style 9D augmented states with outs already included

    By default, export is filtered to the website pitch set:
    FF, SI, FC, SL, ST, CU, CH, FS.
    """
    output = Path(output_path)
    q_table: dict[str, dict[str, float]] = {}
    allowed = set(allowed_pitches) if allowed_pitches is not None else None

    for key, q_value in agent.Q.items():
        state, action = key
        pitch = idx_to_pitch[int(action)]
        if allowed is not None and pitch not in allowed:
            continue

        for normalized_state in _normalize_augmented_state(tuple(state), idx_to_pitch, outs_values):
            prev_pitch = str(normalized_state[-1])
            if allowed is not None and prev_pitch != "NONE" and prev_pitch not in allowed:
                continue
            state_key = _state_key_from_augmented_state(normalized_state)
            q_table.setdefault(state_key, {})[pitch] = float(q_value)

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as file:
        pickle.dump(q_table, file)

    return q_table
