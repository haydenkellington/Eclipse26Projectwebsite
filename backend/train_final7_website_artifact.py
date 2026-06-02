from __future__ import annotations

import json
import pickle
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from export_q_artifacts import export_augmented_q_table


CACHE_DIR = Path.home() / ".pybaseball" / "cache"
START_DATE = "2024-03-15"
END_DATE = "2025-11-01"
RANDOM_STATE = 68
N_EPOCHS = 8
ALPHA = 0.1
GAMMA = 0.95
INIT_Q = -0.01
WEBSITE_PITCHES = ["FF", "SI", "FC", "SL", "ST", "CU", "CH", "FS"]
OUTPUT_PATH = Path("model/q_table_final7_website.pkl")


class QLearningAgent:
    def __init__(self, n_actions: int, alpha: float = ALPHA, gamma: float = GAMMA, init_q: float = INIT_Q):
        self.n_actions = n_actions
        self.alpha = alpha
        self.gamma = gamma
        self.init_q = init_q
        self.Q = defaultdict(lambda: self.init_q)
        self.N = defaultdict(int)

    def _alpha_t(self, state: tuple[int, ...], action: int) -> float:
        return self.alpha / np.sqrt(max(1, self.N[(state, action)]))

    def best_q(self, state: tuple[int, ...]) -> float:
        return max(self.Q[(state, action)] for action in range(self.n_actions))

    def train_from_arrays(
        self,
        state_arr: np.ndarray,
        action_arr: np.ndarray,
        reward_arr: np.ndarray,
        next_state_arr: np.ndarray,
        done_arr: np.ndarray,
    ) -> None:
        n = len(action_arr)
        indices = np.arange(n, dtype=np.int64)

        for epoch in range(N_EPOCHS):
            np.random.shuffle(indices)
            epoch_loss = 0.0

            for row_index in indices:
                state = tuple(state_arr[row_index])
                action = int(action_arr[row_index])
                reward = float(reward_arr[row_index])
                next_state = tuple(next_state_arr[row_index])
                done = bool(done_arr[row_index])

                self.N[(state, action)] += 1
                alpha_t = self._alpha_t(state, action)
                old_q = self.Q[(state, action)]
                target = reward if done else reward + self.gamma * self.best_q(next_state)
                self.Q[(state, action)] += alpha_t * (target - old_q)
                epoch_loss += (self.Q[(state, action)] - old_q) ** 2

            print(f"epoch {epoch + 1}/{N_EPOCHS}: mse_delta={epoch_loss / n:.8f}", flush=True)


def cache_records() -> list[tuple[str, str, Path]]:
    records: list[tuple[str, str, Path]] = []

    for record_path in CACHE_DIR.glob("get_statcast_data_from_csv_url*.cache_record.json"):
        try:
            record = json.loads(record_path.read_text())
        except Exception:
            continue

        args = record.get("args") or []
        url = args[0] if args else ""
        start_match = re.search(r"game_date_gt=([0-9-]+)", url)
        end_match = re.search(r"game_date_lt=([0-9-]+)", url)
        dataframe_path = Path(record.get("dataframe", ""))

        if (
            start_match
            and end_match
            and dataframe_path.exists()
            and START_DATE <= start_match.group(1) <= END_DATE
        ):
            records.append((start_match.group(1), end_match.group(1), dataframe_path))

    records.sort(key=lambda item: item[0])
    return records


def load_cached_statcast() -> pd.DataFrame:
    records = cache_records()
    if not records:
        raise FileNotFoundError(f"No cached Statcast parquet chunks found in {CACHE_DIR}")

    columns = [
        "game_date",
        "game_pk",
        "at_bat_number",
        "pitch_number",
        "pitch_type",
        "description",
        "events",
        "balls",
        "strikes",
        "outs_when_up",
        "stand",
        "p_throws",
        "on_1b",
        "on_2b",
        "on_3b",
        "delta_run_exp",
    ]
    frames = []

    for _, _, parquet_path in records:
        frame = pd.read_parquet(parquet_path, columns=columns)
        frames.append(frame)

    df = pd.concat(frames, ignore_index=True)
    df = df.drop_duplicates()
    print(f"loaded cached statcast rows: {len(df):,} from {len(records)} day chunks", flush=True)
    return df


def build_training_arrays(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[int, str]]:
    df = df.dropna(subset=["pitch_type", "delta_run_exp", "balls", "strikes"]).copy()
    df = df[df["pitch_type"].isin(WEBSITE_PITCHES)].copy()

    for col in ["game_pk", "at_bat_number", "pitch_number", "balls", "strikes", "outs_when_up"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["game_pk", "at_bat_number", "pitch_number", "outs_when_up"])
    df = df.sort_values(["game_pk", "at_bat_number", "pitch_number"], kind="stable").reset_index(drop=True)
    df["at_bat_id"] = df["game_pk"].astype(int).astype(str) + "_" + df["at_bat_number"].astype(int).astype(str)

    df["balls"] = df["balls"].astype(int)
    df["strikes"] = df["strikes"].astype(int)
    df["outs"] = df["outs_when_up"].astype(int).clip(0, 2)
    for col in ["on_1b", "on_2b", "on_3b"]:
        df[col] = df[col].notna().astype(int)
    df["batter_righty"] = (df["stand"] == "R").astype(int)
    df["pitcher_righty"] = (df["p_throws"] == "R").astype(int)
    df["delta_run_exp"] = pd.to_numeric(df["delta_run_exp"], errors="coerce").clip(-0.5, 0.5)
    df = df.dropna(subset=["delta_run_exp"])

    pitch_to_idx = {pitch: index for index, pitch in enumerate(WEBSITE_PITCHES)}
    idx_to_pitch = {index: pitch for pitch, index in pitch_to_idx.items()}
    df["action"] = df["pitch_type"].map(pitch_to_idx).astype(int)

    state_cols = [
        "balls",
        "strikes",
        "outs",
        "on_1b",
        "on_2b",
        "on_3b",
        "batter_righty",
        "pitcher_righty",
    ]
    group = df.groupby("at_bat_id", sort=False)
    ab_sizes = group["at_bat_id"].transform("size")
    ab_rank = group.cumcount()
    df["_done"] = (ab_rank == ab_sizes - 1).astype(int)
    df["_reward"] = (-df["delta_run_exp"]).clip(-0.5, 0.5).astype(np.float32)

    for col in state_cols + ["action"]:
        shifted = group[col].shift(-1)
        df[f"_next_{col}"] = shifted.where(df["_done"] == 0, df[col])

    df["_prev_action"] = group["action"].shift(1).fillna(-1).astype(int)

    state_arr = df[state_cols].values.astype(np.int32)
    next_state_arr = df[[f"_next_{col}" for col in state_cols]].values.astype(np.int32)
    prev_action_arr = df["_prev_action"].values.astype(np.int32)
    action_arr = df["action"].values.astype(np.int32)
    reward_arr = df["_reward"].values.astype(np.float32)
    done_arr = df["_done"].values.astype(bool)

    augmented_state_arr = np.hstack([state_arr, prev_action_arr.reshape(-1, 1)])
    augmented_next_state_arr = np.hstack([next_state_arr, action_arr.reshape(-1, 1)])

    unique_abs = df["at_bat_id"].unique()
    train_abs, _ = train_test_split(unique_abs, test_size=0.2, random_state=RANDOM_STATE)
    train_set = set(train_abs)
    train_mask = df["at_bat_id"].isin(train_set).values

    print(f"website pitches: {WEBSITE_PITCHES}", flush=True)
    print(f"training rows after pitch filter: {train_mask.sum():,}", flush=True)
    print(f"total rows after pitch filter: {len(df):,}", flush=True)

    return (
        augmented_state_arr[train_mask],
        action_arr[train_mask],
        reward_arr[train_mask],
        augmented_next_state_arr[train_mask],
        done_arr[train_mask],
        idx_to_pitch,
    )


def main() -> None:
    np.random.seed(RANDOM_STATE)
    df = load_cached_statcast()
    state_arr, action_arr, reward_arr, next_state_arr, done_arr, idx_to_pitch = build_training_arrays(df)
    agent = QLearningAgent(n_actions=len(idx_to_pitch))
    agent.train_from_arrays(state_arr, action_arr, reward_arr, next_state_arr, done_arr)
    q_table = export_augmented_q_table(agent, idx_to_pitch, OUTPUT_PATH)
    print(f"exported {len(q_table):,} states to {OUTPUT_PATH}", flush=True)


if __name__ == "__main__":
    main()
