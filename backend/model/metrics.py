from __future__ import annotations

from hashlib import sha256


def _stable_unit_interval(key: str) -> float:
    digest = sha256(key.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def get_pitch_metrics(state_key: str, pitch: str, q_value: float) -> dict[str, float | int | bool]:
    """Placeholder for a precomputed metrics[(state, pitch)] lookup.

    Swap this function for a table lookup once notebook metrics are exported.
    The current values are deterministic so the UI behaves like a real app
    during early development.
    """
    seed = _stable_unit_interval(f"{state_key}:{pitch}")
    whiff_rate = min(0.62, max(0.08, 0.22 + seed * 0.28 + q_value * 0.8))
    baa = min(0.34, max(0.08, 0.265 - seed * 0.08 - q_value * 0.9))
    mlb_frequency = min(0.72, max(0.04, 0.11 + seed * 0.48))
    sample_size = int(240 + seed * 5200)

    return {
        "expected_delta_run_exp": round(-q_value, 3),
        "sample_size": sample_size,
        "whiff_rate": round(whiff_rate, 3),
        "baa": round(baa, 3),
        "mlb_frequency": round(mlb_frequency, 3),
        "low_sample_warning": sample_size < 500,
    }
