export type PitchCode = "FF" | "SI" | "FC" | "SL" | "ST" | "CU" | "CH" | "FS";

export type RecommendationRequest = {
  balls: number;
  strikes: number;
  outs: number;
  on_1b: boolean;
  on_2b: boolean;
  on_3b: boolean;
  batter_hand: "L" | "R";
  pitcher_hand: "L" | "R";
  prev_pitch: PitchCode | null;
  available_pitches: PitchCode[];
};

export type PitchComparison = {
  pitch: PitchCode;
  pitch_name: string;
  available: boolean;
  q_value: number;
  expected_delta_run_exp: number;
  expected_delta_run_exp_from_q: number;
  empirical_delta_run_exp?: number;
  q_observed: boolean;
  sample_size: number;
  state_sample_size: number;
  swing_count: number;
  whiff_count: number;
  whiff_rate: number;
  baa: number;
  mlb_frequency: number;
  model_weight: number;
  metrics_source: "statcast" | "deterministic_fallback";
  low_sample_warning: boolean;
};

export type RecommendationResponse = {
  state_key: string;
  q_source: "q_table" | "deterministic_fallback";
  interpretation: string;
  recommended_pitch: PitchCode;
  recommended_pitch_name: string;
  best_q_value: number;
  best_expected_delta_run_exp: number;
  empirical_delta_run_exp?: number;
  sample_size: number;
  state_sample_size: number;
  swing_count: number;
  whiff_count: number;
  whiff_rate: number;
  baa: number;
  mlb_frequency: number;
  model_weight: number;
  metrics_source: "statcast" | "deterministic_fallback";
  q_observed: boolean;
  low_sample_warning: boolean;
  best_overall_pitch: PitchCode;
  best_overall_pitch_name: string;
  best_overall_q_value: number;
  best_overall_expected_delta_run_exp: number;
  best_unavailable_pitch: PitchCode | null;
  best_unavailable_pitch_name: string | null;
  best_unavailable_q_value: number | null;
  best_unavailable_expected_delta_run_exp: number | null;
  comparison: PitchComparison[];
};
