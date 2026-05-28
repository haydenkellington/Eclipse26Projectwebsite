from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import pybaseball as pyb
from pybaseball import statcast
from sklearn.model_selection import train_test_split
import pickle

from export_q_artifacts import export_augmented_q_table


START_DATE = "2024-03-03"
END_DATE = "2025-11-30"
RANDOM_STATE = 68
N_EPOCHS = 8
ALPHA = 0.05
GAMMA = 0.95
OUTS_VALUES = (0, 1, 2)

WHIFF_DESCRIPTIONS = {
    "swinging_strike",
    "swinging_strike_blocked",
    "missed_bunt",
}

SWING_DESCRIPTIONS = {
    "swinging_strike",
    "swinging_strike_blocked",
    "foul",
    "foul_tip",
    "foul_bunt",
    "missed_bunt",
    "bunt_foul_tip",
    "hit_into_play",
}

HIT_EVENTS = {"single", "double", "triple", "home_run"}

AB_EVENTS = {
    "field_out",
    "strikeout",
    "strikeout_double_play",
    "single",
    "double",
    "triple",
    "home_run",
    "force_out",
    "grounded_into_double_play",
    "field_error",
    "fielders_choice",
    "fielders_choice_out",
    "double_play",
    "triple_play",
    "sac_fly",
    "sac_bunt",
}


class QLearningAgent:
    def __init__(self, n_actions: int, alpha: float = ALPHA, gamma: float = GAMMA):
        self.n_actions = n_actions
        self.alpha = alpha
        self.gamma = gamma
        self.Q = defaultdict(float)

    def best_q(self, state_tuple: tuple[int, ...]) -> float:
        return max(self.Q[(state_tuple, a)] for a in range(self.n_actions))

    def train_from_arrays(
        self,
        s_arr: np.ndarray,
        a_arr: np.ndarray,
        r_arr: np.ndarray,
        ns_arr: np.ndarray,
        done_arr: np.ndarray,
        n_epochs: int = N_EPOCHS,
    ) -> list[float]:
        n = len(a_arr)
        idx = np.arange(n, dtype=np.int64)
        losses: list[float] = []

        for epoch in range(n_epochs):
            np.random.shuffle(idx)
            epoch_loss = 0.0

            for i in idx:
                s = tuple(s_arr[i])
                a = int(a_arr[i])
                r = float(r_arr[i])
                ns = tuple(ns_arr[i])
                done = bool(done_arr[i])

                old_q = self.Q[(s, a)]
                target = r if done else r + self.gamma * self.best_q(ns)
                self.Q[(s, a)] += self.alpha * (target - old_q)
                epoch_loss += (self.Q[(s, a)] - old_q) ** 2

            loss = epoch_loss / n
            losses.append(loss)
            print(f"epoch {epoch + 1}/{n_epochs}: mse_delta={loss:.8f}", flush=True)

        return losses


def _state_key_from_row(row: pd.Series, prev_pitch_type: str | None, outs: int) -> str:
    prev = "NONE" if pd.isna(prev_pitch_type) else str(prev_pitch_type)
    bases = f"{int(row['on_1b'])}{int(row['on_2b'])}{int(row['on_3b'])}"
    batter_hand = "R" if int(row["batter_righty"]) == 1 else "L"
    pitcher_hand = "R" if int(row["pitcher_righty"]) == 1 else "L"

    return "|".join(
        [
            f"b{int(row['balls'])}",
            f"s{int(row['strikes'])}",
            f"o{int(outs)}",
            f"bases{bases}",
            f"bh{batter_hand}",
            f"ph{pitcher_hand}",
            f"prev{prev}",
        ]
    )


def export_statcast_metrics(df: pd.DataFrame, output_path: str | Path = "model/metrics.pkl") -> dict:
    metric_df = df.dropna(subset=["pitch_type", "delta_run_exp", "balls", "strikes"]).copy()
    metric_df["_is_whiff"] = metric_df["description"].isin(WHIFF_DESCRIPTIONS)
    metric_df["_is_swing"] = metric_df["description"].isin(SWING_DESCRIPTIONS)
    metric_df["_is_hit"] = metric_df["events"].isin(HIT_EVENTS)
    metric_df["_is_ab"] = metric_df["events"].isin(AB_EVENTS)

    metrics_table: dict[str, dict[str, dict[str, float | int | bool]]] = {}

    state_cols = [
        "balls",
        "strikes",
        "on_1b",
        "on_2b",
        "on_3b",
        "batter_righty",
        "pitcher_righty",
        "prev_pitch_type",
    ]

    metric_df["_state_sample_size"] = metric_df.groupby(state_cols, dropna=False)["pitch_type"].transform("size")
    pitch_groups = metric_df.groupby(state_cols + ["pitch_type"], dropna=False)

    for group_key, rows in pitch_groups:
        *state_values, pitch = group_key
        state_sample_size = int(rows["_state_sample_size"].iloc[0])
        pitch_sample_size = int(len(rows))
        swings = int(rows["_is_swing"].sum())
        whiffs = int(rows["_is_whiff"].sum())
        at_bats = int(rows["_is_ab"].sum())
        hits = int(rows["_is_hit"].sum())

        whiff_rate = whiffs / swings if swings else 0.0
        baa = hits / at_bats if at_bats else 0.0
        mlb_frequency = pitch_sample_size / state_sample_size if state_sample_size else 0.0
        empirical_delta_run_exp = float(rows["delta_run_exp"].mean())

        row = rows.iloc[0]
        prev_pitch_type = state_values[-1]
        values = {
            "sample_size": pitch_sample_size,
            "state_sample_size": state_sample_size,
            "swing_count": swings,
            "whiff_count": whiffs,
            "whiff_rate": round(whiff_rate, 3),
            "baa": round(baa, 3),
            "mlb_frequency": round(mlb_frequency, 3),
            "empirical_delta_run_exp": round(empirical_delta_run_exp, 3),
            "low_sample_warning": pitch_sample_size < 25 or swings < 10,
        }

        for outs in OUTS_VALUES:
            state_key = _state_key_from_row(row, prev_pitch_type, outs)
            metrics_table.setdefault(state_key, {})[str(pitch)] = values

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as file:
        pickle.dump(metrics_table, file)

    return metrics_table


def load_and_clean_data() -> pd.DataFrame:
    pyb.cache.enable()
    print(f"Downloading Statcast data: {START_DATE} to {END_DATE}", flush=True)
    df = statcast(start_dt=START_DATE, end_dt=END_DATE)
    print(f"raw shape: {df.shape}", flush=True)

    deprecated = [
        "break_angle_deprecated",
        "break_length_deprecated",
        "spin_dir",
        "spin_rate_deprecated",
        "umpire",
        "sv_id",
        "tfs_deprecated",
        "tfs_zulu_deprecated",
    ]
    df = df.drop(columns=[c for c in deprecated if c in df.columns])

    for col in ["on_1b", "on_2b", "on_3b"]:
        if col in df.columns:
            # Statcast stores runner IDs in these columns. Convert to 0/1 base occupancy.
            df[col] = df[col].notna().astype(int)

    critical = ["pitch_type", "delta_run_exp", "balls", "strikes"]
    df = df.dropna(subset=[c for c in critical if c in df.columns])

    for col in ["plate_x", "plate_z"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median())

    if "release_speed" in df.columns:
        df["release_speed"] = pd.to_numeric(df["release_speed"], errors="coerce")
        df = df[
            (df["release_speed"].isna())
            | ((df["release_speed"] >= 40) & (df["release_speed"] <= 105))
        ]

    base_cols = [
        "game_date",
        "game_pk",
        "at_bat_number",
        "pitch_number",
        "pitch_type",
        "description",
        "events",
        "balls",
        "strikes",
        "stand",
        "p_throws",
        "plate_x",
        "plate_z",
        "release_speed",
        "release_pos_x",
        "release_pos_z",
        "on_1b",
        "on_2b",
        "on_3b",
        "delta_run_exp",
    ]
    df_clean = df[[c for c in base_cols if c in df.columns]].copy()

    df_clean["at_bat_id"] = (
        df_clean["game_pk"].astype(str).fillna("")
        + "_"
        + df_clean["at_bat_number"].astype(str).fillna("")
    )

    for col in ["game_pk", "at_bat_number", "pitch_number"]:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")

    df_clean = df_clean.sort_values(
        [c for c in ["game_pk", "at_bat_number", "pitch_number"] if c in df_clean.columns],
        kind="stable",
    ).reset_index(drop=True)

    df_clean["balls"] = df_clean["balls"].astype(int)
    df_clean["strikes"] = df_clean["strikes"].astype(int)
    df_clean["prev_pitch_type"] = df_clean.groupby("at_bat_id")["pitch_type"].shift(1)
    df_clean["batter_righty"] = (df_clean["stand"] == "R").astype(int)
    df_clean["pitcher_righty"] = (df_clean["p_throws"] == "R").astype(int)

    for col in ["on_1b", "on_2b", "on_3b"]:
        df_clean[col] = (pd.to_numeric(df_clean[col], errors="coerce").fillna(0) > 0).astype(int)

    print(f"clean shape: {df_clean.shape}", flush=True)
    return df_clean


def build_arrays(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[int, str]]:
    mdp_cols = [
        "game_pk",
        "at_bat_number",
        "pitch_number",
        "at_bat_id",
        "balls",
        "strikes",
        "on_1b",
        "on_2b",
        "on_3b",
        "batter_righty",
        "pitcher_righty",
        "prev_pitch_type",
        "pitch_type",
        "delta_run_exp",
        "description",
        "events",
    ]
    mdp_df = df[[c for c in mdp_cols if c in df.columns]].copy()
    mdp_df = mdp_df.dropna(subset=["pitch_type", "delta_run_exp", "balls", "strikes"])

    pitch_types = sorted(mdp_df["pitch_type"].unique())
    pitch_to_idx = {p: i for i, p in enumerate(pitch_types)}
    idx_to_pitch = {i: p for p, i in pitch_to_idx.items()}
    mdp_df["action"] = mdp_df["pitch_type"].map(pitch_to_idx)

    state_cols = ["balls", "strikes", "on_1b", "on_2b", "on_3b", "batter_righty", "pitcher_righty"]
    mdp_df["_ab_key"] = mdp_df["game_pk"].astype(str) + "_" + mdp_df["at_bat_number"].astype(str)
    grp = mdp_df.groupby("_ab_key", sort=False)
    ab_sizes = grp["_ab_key"].transform("size")
    ab_rank = grp.cumcount()
    mdp_df["_done"] = (ab_rank == ab_sizes - 1).astype(int)
    mdp_df["_reward"] = -mdp_df["delta_run_exp"]

    for col in state_cols + ["action"]:
        shifted = grp[col].shift(-1)
        mdp_df[f"_next_{col}"] = shifted.where(mdp_df["_done"] == 0, mdp_df[col])

    mdp_df["_prev_action"] = grp["action"].shift(1).fillna(-1).astype(int)

    state_arr = mdp_df[state_cols].values.astype(np.int32)
    next_state_arr = mdp_df[[f"_next_{c}" for c in state_cols]].values.astype(np.int32)
    prev_act_arr = mdp_df["_prev_action"].values.astype(np.int32)
    action_arr = mdp_df["action"].values.astype(np.int32)
    reward_arr = mdp_df["_reward"].values.astype(np.float32)
    done_arr = mdp_df["_done"].values.astype(bool)

    aug_state_arr = np.hstack([state_arr, prev_act_arr.reshape(-1, 1)])
    aug_next_state_arr = np.hstack([next_state_arr, action_arr.reshape(-1, 1)])

    unique_abs = mdp_df["_ab_key"].unique()
    train_abs, _test_abs = train_test_split(unique_abs, test_size=0.2, random_state=RANDOM_STATE)
    train_set = set(train_abs)
    train_mask = mdp_df["_ab_key"].isin(train_set).values

    print(f"actions: {len(pitch_types)} {pitch_types}", flush=True)
    print(f"transitions: {len(action_arr):,}; train transitions: {train_mask.sum():,}", flush=True)

    return (
        aug_state_arr[train_mask],
        action_arr[train_mask],
        reward_arr[train_mask],
        aug_next_state_arr[train_mask],
        done_arr[train_mask],
        idx_to_pitch,
    )


def main() -> None:
    np.random.seed(RANDOM_STATE)
    df = load_and_clean_data()
    s_arr, a_arr, r_arr, ns_arr, done_arr, idx_to_pitch = build_arrays(df)

    agent_aug = QLearningAgent(n_actions=len(idx_to_pitch), alpha=ALPHA, gamma=GAMMA)
    agent_aug.train_from_arrays(s_arr, a_arr, r_arr, ns_arr, done_arr, n_epochs=N_EPOCHS)

    output = Path("model/q_table.pkl")
    q_table = export_augmented_q_table(agent_aug, idx_to_pitch, output_path=output)
    print(f"exported {len(q_table):,} state keys to {output}", flush=True)

    metrics_output = Path("model/metrics.pkl")
    metrics_table = export_statcast_metrics(df, output_path=metrics_output)
    print(f"exported {len(metrics_table):,} metric state keys to {metrics_output}", flush=True)


if __name__ == "__main__":
    main()
