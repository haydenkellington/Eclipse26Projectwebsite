import type { RecommendationRequest, RecommendationResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function fetchRecommendation(
  payload: RecommendationRequest,
): Promise<RecommendationResponse> {
  const response = await fetch(`${API_URL}/recommend`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Recommendation request failed with ${response.status}`);
  }

  return response.json();
}

