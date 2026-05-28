from typing import Any


def encode_state(payload: dict[str, Any]) -> str:
    """Stable state key for Q-table and metrics lookups."""
    bases = "".join(
        [
            "1" if payload["on_1b"] else "0",
            "1" if payload["on_2b"] else "0",
            "1" if payload["on_3b"] else "0",
        ]
    )
    prev_pitch = payload.get("prev_pitch") or "NONE"

    parts = [
        f"b{payload['balls']}",
        f"s{payload['strikes']}",
        f"o{payload['outs']}",
        f"bases{bases}",
        f"bh{payload['batter_hand']}",
        f"ph{payload['pitcher_hand']}",
        f"prev{prev_pitch}",
    ]
    return "|".join(parts)

