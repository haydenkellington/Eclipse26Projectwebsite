"use client";

import { Activity, Ban, Gauge, LineChart, ShieldCheck, TriangleAlert } from "lucide-react";
import type { PitchCode, RecommendationRequest, RecommendationResponse } from "@/lib/types";

type Props = {
  request: RecommendationRequest;
  recommendation: RecommendationResponse | null;
  loading: boolean;
  error: string | null;
  hasPitchInAtBat: boolean;
};

const PITCH_FAMILIES: Record<PitchCode, string> = {
  FF: "hard fastball",
  SI: "hard fastball",
  FC: "hard fastball",
  SL: "breaking ball",
  ST: "breaking ball",
  CU: "breaking ball",
  CH: "offspeed pitch",
  FS: "offspeed pitch",
};

export function RecommendationPanel({ request, recommendation, loading, error, hasPitchInAtBat }: Props) {
  if (!hasPitchInAtBat) {
    return (
      <main className="grid min-h-[calc(100vh-89px)] place-items-center px-5 py-5 lg:px-8">
        <section className="max-w-xl border border-amber/40 bg-orange-50 p-6 text-amber">
          <div className="flex items-start gap-3">
            <TriangleAlert className="mt-1 shrink-0" size={22} />
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em]">Pitch Needed</p>
              <h2 className="mt-2 text-2xl font-black text-savant">Input at least one pitch</h2>
              <p className="mt-3 text-sm leading-6">
                This sequencing model only works once at least one pitch has already been thrown in the at-bat. Move
                the count off 0-0 and choose the previous pitch to generate a recommendation.
              </p>
            </div>
          </div>
        </section>
      </main>
    );
  }

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
  const confidence = getConfidence(recommendation);
  const whyThisPitch = getWhyThisPitch(request, recommendation);

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
            <span
              className={`mb-1 inline-flex items-center gap-2 border px-3 py-1 text-xs font-black uppercase tracking-[0.12em] ${confidence.className}`}
              title={confidence.detail}
            >
              <ShieldCheck size={14} />
              {confidence.label}
            </span>
          </div>
        </div>
        <div className="border border-line bg-ink px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">State Key</p>
          <p className="mt-1 max-w-[48rem] break-all font-mono text-xs text-slate-700">{recommendation.state_key}</p>
        </div>
      </div>

      {error ? <p className="mb-4 text-sm text-amber">{error}</p> : null}
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
            Of the pitches currently in the selected arsenal, this is the option the model expects to help the pitcher
            the most in this situation.
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
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-clay">Why This Pitch?</p>
        <p className="mt-3 text-sm leading-6 text-slate-700">{whyThisPitch}</p>
      </section>

      <section className="mt-6 border border-line bg-panel p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-clay">Model Interpretation</p>
        <p className="mt-3 text-sm leading-6 text-slate-700">
          The model is estimating which pitch is most likely to help the pitcher limit future runs from this count,
          base/out state, matchup, and previous pitch. A higher Q-value means the model likes that pitch more. A lower
          model sequence dRE means the pitch is expected to reduce the offense&apos;s run expectancy more.
        </p>
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

function formatOptionalSigned(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "--";
  }

  return signed(value);
}

function getConfidence(recommendation: RecommendationResponse) {
  if (
    !recommendation.low_sample_warning &&
    recommendation.q_observed &&
    recommendation.sample_size >= 500 &&
    recommendation.state_sample_size >= 1000 &&
    recommendation.swing_count >= 150
  ) {
    return {
      label: "High Confidence",
      detail: "Strong state sample, strong pitch sample, and an observed Q-value.",
      className: "border-emerald-200 bg-emerald-50 text-emerald-700",
    };
  }

  if (
    recommendation.q_observed &&
    recommendation.sample_size >= 150 &&
    recommendation.state_sample_size >= 500 &&
    recommendation.swing_count >= 50
  ) {
    return {
      label: "Medium Confidence",
      detail: "Usable sample size, but the recommendation should still be treated as directional.",
      className: "border-sky-200 bg-sky-50 text-sky-700",
    };
  }

  return {
    label: "Low Confidence",
    detail: "Limited sample size or missing learned Q-value. Use this as a directional signal.",
    className: "border-amber/30 bg-orange-50 text-amber",
  };
}

function getWhyThisPitch(request: RecommendationRequest, recommendation: RecommendationResponse) {
  const pitchFamily = PITCH_FAMILIES[recommendation.recommended_pitch];
  const previousPitch = request.prev_pitch;
  const previousFamily = previousPitch ? PITCH_FAMILIES[previousPitch] : null;
  const countText = `${request.balls}-${request.strikes}`;
  const whiffText =
    recommendation.whiff_rate >= 0.25
      ? "The whiff profile also supports it as a bat-missing option when the hitter has to protect."
      : recommendation.whiff_rate >= 0.18
        ? "The whiff profile is solid enough to make it useful when the pitcher needs a miss or weak contact."
        : "The model is leaning more on run prevention and sequencing value than pure swing-and-miss upside.";
  const runValueText =
    recommendation.best_expected_delta_run_exp < 0
      ? "The model expects the pitch to move the at-bat toward a lower run-scoring situation."
      : "Even though the run-value edge is smaller here, the model still prefers it over the other available choices.";

  if (previousPitch && previousPitch !== recommendation.recommended_pitch && previousFamily !== pitchFamily) {
    return `In a ${countText} count, this recommendation creates a different look after the previous ${previousFamily}. Moving to a ${pitchFamily} can change the hitter's timing window and make it harder to cover both speed and movement. ${whiffText} ${runValueText}`;
  }

  if (previousPitch && previousPitch !== recommendation.recommended_pitch) {
    return `In a ${countText} count, this keeps the hitter in a related pitch family while still changing the exact pitch shape. That can make the sequence harder to square up without giving the hitter a completely new speed band to identify. ${whiffText} ${runValueText}`;
  }

  return `In a ${countText} count, the model prefers staying with this pitch because the current state rewards run prevention more than simply showing a new pitch. ${whiffText} ${runValueText}`;
}
