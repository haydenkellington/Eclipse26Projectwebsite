from model.recommend import recommend_pitch


def main() -> None:
    response = recommend_pitch(
        {
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
    )

    assert response["recommended_pitch"] in {"FF", "SL", "CH"}
    assert response["comparison"]
    assert response["sample_size"] > 0
    assert abs(response["best_expected_delta_run_exp"] + response["best_q_value"]) < 0.001
    print("smoke test passed")


if __name__ == "__main__":
    main()
