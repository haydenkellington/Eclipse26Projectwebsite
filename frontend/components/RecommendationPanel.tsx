"use client";

import { Activity, Ban, Gauge, LineChart, TriangleAlert } from "lucide-react";
import type { RecommendationResponse } from "@/lib/types";

type Props = {
  recommendation: RecommendationResponse | null;
  loading: boolean;
  error: string | null;
  hasPreviousPitch: boolean;
};

export function RecommendationPanel({ recommendation, loading, error, hasPreviousPitch }: Props) {
  if (loading && !recommendation) {
    return <main className="grid min-h-[calc(100vh-89px)] place-items-center p-6 text-slate-500">Loading recommendation...</main>;
  }

  if (error && !recommendation) {
    return <main className="grid min-h-[calc(100vh-89px)] place-items-center p-6 text-clay">{error}</main>;
  }

  if (!recommendation) {
    return null;
  }

  const unavailableText = recommendation.best_unavailable_pitch
    ? `${recommendation.best_unavailable_pitch_name} (${recommendation.best_unavailable_pitch})`
    : "None";
  const isFallback = recommendation.q_source === "deterministic_fallback";

  return (
    <main className="px-5 py-5 lg:px-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-line bg-white px-5 py-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-clay">Model-Recommended Pitch</p>
          <div className="mt-2 flex flex-wrap items-end gap-3">
            <h2 className="text-5xl font-black leading-none text-savant md:text-7xl">
              {recommendation.recommended_pitch}
            </h2>
            <p className="pb-1 text-lg font-bold text-slate-700">{recommendation.recommended_pitch_name}</p>
          </div>
        </div>
        <div className="border border-line bg-ink px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">State Key</p>
          <p className="mt-1 max-w-[48rem] break-all font-mono text-xs text-slate-700">{recommendation.state_key}</p>
        </div>
      </div>

      {error ? <p className="mb-4 text-sm text-amber">{error}</p> : null}
      {!hasPreviousPitch ? (
        <div className="mb-4 flex items-start gap-3 border border-amber/40 bg-orange-50 px-4 py-3 text-sm text-amber">
          <TriangleAlert className="mt-0.5 shrink-0" size={17} />
          <p>
            This model is designed for in-at-bat sequencing, so choose a previous pitch once at least one pitch has been thrown.
          </p>
        </div>
      ) : null}
      {isFallback || recommendation.low_sample_warning ? (
        <div className="mb-4 flex items-start gap-3 border border-amber/40 bg-orange-50 px-4 py-3 text-sm text-amber">
          <TriangleAlert className="mt-0.5 shrink-0" size={17} />
          <p>
            {isFallback
              ? "No exported notebook Q-table was found, so this view is using deterministic demo values."
              : "This recommendation is based on a low sample state. Treat the pitch ranking as directional."}
          </p>
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Metric icon={<Gauge size={18} />} label="Best Q-Value" value={signed(recommendation.best_q_value)} />
        <Metric
          icon={<LineChart size={18} />}
          label="Model Sequence dRE"
          value={signed(recommendation.best_expected_delta_run_exp)}
        />
        <Metric
          label="Empirical dRE"
          value={formatOptionalSigned(recommendation.empirical_delta_run_exp)}
        />
        <Metric icon={<Activity size={18} />} label="Whiff Rate" value={percent(recommendation.whiff_rate)} />
        <Metric label="Pitch Samples" value={recommendation.sample_size.toLocaleString()} />
      </div>

      <div className="mt-4 border border-line bg-white px-4 py-3 text-sm text-slate-700">
        This pitch appears in{" "}
        <span className="font-bold text-savant">{recommendation.sample_size.toLocaleString()}</span> of{" "}
        <span className="font-bold text-savant">{recommendation.state_sample_size.toLocaleString()}</span> matching
        state pitches. Whiff rate is{" "}
        <span className="font-bold text-savant">
          {recommendation.whiff_count.toLocaleString()} whiffs / {recommendation.swing_count.toLocaleString()} swings
        </span>
        .
      </div>

      <section className="mt-6 grid gap-4 lg:grid-cols-2">
        <div className="border border-line bg-panel p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-clay">Best Available</p>
          <p className="mt-3 flex flex-wrap items-baseline gap-2 text-3xl font-black text-savant">
            {recommendation.recommended_pitch_name}
            <span className="font-mono text-xl text-clay">{recommendation.recommended_pitch}</span>
          </p>
          <p className="mt-3 text-sm text-slate-600">
            Highest available Q, equivalent to lowest model expected delta run expectancy.
          </p>
        </div>
        <div className="border border-line bg-panel p-5">
          <div className="flex items-center gap-2 text-slate-600">
            <Ban size={16} />
            <p className="text-xs font-semibold uppercase tracking-[0.18em]">Best Unavailable Pitch</p>
          </div>
          <p className="mt-3 text-3xl font-black text-savant">{unavailableText}</p>
          {recommendation.best_unavailable_pitch ? (
            <p className="mt-3 text-sm text-slate-600">
              Q {signed(recommendation.best_unavailable_q_value ?? 0)} / model expected dRE{" "}
              {signed(recommendation.best_unavailable_expected_delta_run_exp ?? 0)}
            </p>
          ) : null}
        </div>
      </section>

      <section className="mt-6 border border-line bg-panel p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-clay">Model Interpretation</p>
        <p className="mt-3 text-sm leading-6 text-slate-700">{recommendation.interpretation}</p>
      </section>
    </main>
  );
}

function Metric({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="border border-line bg-panel p-4">
      <div className="flex items-center gap-2 text-slate-600">
        {icon}
        <p className="text-xs font-semibold uppercase tracking-[0.14em]">{label}</p>
      </div>
      <p className="mt-3 text-2xl font-black text-savant">{value}</p>
    </div>
  );
}

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function baa(value: number) {
  return value.toFixed(3).replace(/^0/, "");
}

function signed(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(3)}`;
}

function formatOptionalSigned(value?: number) {
  if (value === undefined || Number.isNaN(value)) {
    return "--";
  }

  return signed(value);
}
