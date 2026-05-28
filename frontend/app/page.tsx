"use client";

import { useEffect, useMemo, useState } from "react";
import { ComparisonPanel } from "@/components/ComparisonPanel";
import { ControlPanel } from "@/components/ControlPanel";
import { RecommendationPanel } from "@/components/RecommendationPanel";
import { ValueKey } from "@/components/ValueKey";
import { fetchRecommendation } from "@/lib/api";
import type { RecommendationRequest, RecommendationResponse } from "@/lib/types";

const DEFAULT_REQUEST: RecommendationRequest = {
  balls: 1,
  strikes: 2,
  outs: 1,
  on_1b: true,
  on_2b: false,
  on_3b: false,
  batter_hand: "R",
  pitcher_hand: "L",
  prev_pitch: "FF",
  available_pitches: ["FF", "SL", "CH"],
};

export default function Home() {
  const [request, setRequest] = useState<RecommendationRequest>(DEFAULT_REQUEST);
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const requestKey = useMemo(() => JSON.stringify(request), [request]);
  const hasPitchInAtBat = request.balls + request.strikes > 0 && request.prev_pitch !== null;

  useEffect(() => {
    const controller = new AbortController();

    if (!hasPitchInAtBat) {
      setRecommendation(null);
      setLoading(false);
      setError(null);
      return () => controller.abort();
    }

    setLoading(true);
    setError(null);

    fetchRecommendation(request)
      .then((data) => {
        if (!controller.signal.aborted) {
          setRecommendation(data);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setError("Backend unavailable. Start FastAPI on port 8000, then refresh or change an input.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, [requestKey, hasPitchInAtBat]);

  return (
    <div className="min-h-screen bg-ink">
      <header className="border-b border-savant bg-savant px-5 py-4 text-white lg:px-8">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-200">Pitch Sequencing Analytics</p>
            <h1 className="mt-1 text-2xl font-black leading-tight md:text-3xl">
              Expected Run Value Pitch Recommender
            </h1>
          </div>
          <p className="max-w-2xl text-sm leading-6 text-slate-200">
            Compare available pitch choices by learned Q-value, model sequence dRE, empirical dRE, MLB usage, and whiff profile.
          </p>
        </div>
      </header>
      <div className="grid lg:grid-cols-[320px_minmax(0,1fr)_480px]">
        <ControlPanel value={request} onChange={setRequest} onReset={() => setRequest(DEFAULT_REQUEST)} />
        <RecommendationPanel
          recommendation={recommendation}
          loading={loading}
          error={error}
          hasPitchInAtBat={hasPitchInAtBat}
        />
        <ComparisonPanel recommendation={recommendation} />
      </div>
      <ValueKey />
    </div>
  );
}
