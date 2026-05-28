from __future__ import annotations

import pickle
from hashlib import sha256
from pathlib import Path
from typing import Any

from model.encoder import encode_state
from model.metrics import get_pitch_metrics
from model.pitch_mappings import PITCHES

MODEL_DIR = Path(__file__).resolve().parent
Q_TABLE_PATH = MODEL_DIR / "q_table.pkl"


def _load_q_table() -> dict[str, dict[str, float]]:
    if not Q_TABLE_PATH.exists():
        return {}

    with Q_TABLE_PATH.open("rb") as file:
        table = pickle.load(file)

    if not isinstance(table, dict):
        raise ValueError("q_table.pkl must contain dict[state_key][pitch_code] = q_value")

    return table


Q_TABLE = _load_q_table()


def _fallback_q_value(state_key: str, pitch: str) -> float:
    digest = sha256(f"{state_key}:{pitch}".encode("utf-8")).hexdigest()
    unit = int(digest[:8], 16) / 0xFFFFFFFF
    return round((unit - 0.5) * 0.18, 3)


def _q_values_for_state(state_key: str) -> dict[str, dict[str, float | bool]]:
    if state_key in Q_TABLE:
        learned = Q_TABLE[state_key]
        return {
            pitch: {
                "q_value": learned[pitch] if pitch in learned else _fallback_q_value(state_key, pitch),
                "q_observed": pitch in learned,
            }
            for pitch in PITCHES
        }

    return {
        pitch: {
            "q_value": _fallback_q_value(state_key, pitch),
            "q_observed": False,
        }
        for pitch in PITCHES
    }


def _model_frequencies(rows: list[dict[str, Any]]) -> None:
    positive_mass = sum(max(0.001, row["q_value"] + 0.11) for row in rows)
    for row in rows:
        row["model_weight"] = round(max(0.001, row["q_value"] + 0.11) / positive_mass, 3)


def recommend_pitch(payload: dict[str, Any]) -> dict[str, Any]:
    state_key = encode_state(payload)
    q_values = _q_values_for_state(state_key)
    q_source = "q_table" if state_key in Q_TABLE else "deterministic_fallback"
    available = [pitch for pitch in payload["available_pitches"] if pitch in PITCHES]

    if not available:
        raise ValueError("available_pitches must include at least one supported pitch code")

    comparison: list[dict[str, Any]] = []
    for pitch, q_info in q_values.items():
        q_value = float(q_info["q_value"])
        metrics = get_pitch_metrics(state_key, pitch, q_value)
        comparison.append(
            {
                "pitch": pitch,
                "pitch_name": PITCHES[pitch]["name"],
                "available": pitch in available,
                "q_value": q_value,
                "expected_delta_run_exp_from_q": round(-q_value, 3),
                "q_observed": bool(q_info["q_observed"]),
                **metrics,
            }
        )

    _model_frequencies(comparison)
    comparison.sort(key=lambda row: (row["q_observed"], row["q_value"]), reverse=True)

    available_rows = [row for row in comparison if row["available"]]
    best_available = available_rows[0]
    best_overall = comparison[0]
    best_unavailable = next((row for row in comparison if not row["available"]), None)

    return {
        "state_key": state_key,
        "q_source": q_source,
        "interpretation": "Q is expected pitcher reward. Because reward = -delta_run_exp, expected_delta_run_exp_from_q = -q_value. Higher Q is better; lower expected delta_run_exp is better.",
        "recommended_pitch": best_available["pitch"],
        "recommended_pitch_name": best_available["pitch_name"],
        "best_q_value": best_available["q_value"],
        "best_expected_delta_run_exp": best_available["expected_delta_run_exp_from_q"],
        "sample_size": best_available["sample_size"],
        "state_sample_size": best_available.get("state_sample_size", best_available["sample_size"]),
        "swing_count": best_available.get("swing_count", 0),
        "whiff_count": best_available.get("whiff_count", 0),
        "whiff_rate": best_available["whiff_rate"],
        "baa": best_available["baa"],
        "mlb_frequency": best_available["mlb_frequency"],
        "model_weight": best_available["model_weight"],
        "metrics_source": best_available["metrics_source"],
        "q_observed": best_available["q_observed"],
        "low_sample_warning": best_available["low_sample_warning"],
        "best_overall_pitch": best_overall["pitch"],
        "best_overall_pitch_name": best_overall["pitch_name"],
        "best_overall_q_value": best_overall["q_value"],
        "best_overall_expected_delta_run_exp": best_overall["expected_delta_run_exp_from_q"],
        "best_unavailable_pitch": best_unavailable["pitch"] if best_unavailable else None,
        "best_unavailable_pitch_name": best_unavailable["pitch_name"] if best_unavailable else None,
        "best_unavailable_q_value": best_unavailable["q_value"] if best_unavailable else None,
        "best_unavailable_expected_delta_run_exp": best_unavailable["expected_delta_run_exp_from_q"] if best_unavailable else None,
        "comparison": comparison,
    }
