"use client";

import { RotateCcw } from "lucide-react";
import type { PitchCode, RecommendationRequest } from "@/lib/types";

const PITCHES: { code: PitchCode; label: string }[] = [
  { code: "FF", label: "Four-seam" },
  { code: "SI", label: "Sinker" },
  { code: "FC", label: "Cutter" },
  { code: "SL", label: "Slider" },
  { code: "ST", label: "Sweeper" },
  { code: "CU", label: "Curve" },
  { code: "CH", label: "Changeup" },
  { code: "FS", label: "Splitter" },
];

type Props = {
  value: RecommendationRequest;
  onChange: (value: RecommendationRequest) => void;
  onReset: () => void;
};

export function ControlPanel({ value, onChange, onReset }: Props) {
  const update = <K extends keyof RecommendationRequest>(key: K, next: RecommendationRequest[K]) => {
    onChange({ ...value, [key]: next });
  };

  const togglePitch = (pitch: PitchCode) => {
    const current = value.available_pitches;
    const next = current.includes(pitch)
      ? current.filter((item) => item !== pitch)
      : [...current, pitch];

    if (next.length > 0) {
      update("available_pitches", next);
    }
  };

  return (
    <aside className="border-r border-line bg-panel px-5 py-5 lg:min-h-[calc(100vh-89px)]">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-clay">Game State</p>
          <h2 className="text-xl font-black text-savant">Pitch Context</h2>
        </div>
        <button
          type="button"
          aria-label="Reset inputs"
          title="Reset inputs"
          onClick={onReset}
          className="focus-ring grid h-9 w-9 place-items-center border border-line bg-ink text-savant hover:border-savant"
        >
          <RotateCcw size={17} />
        </button>
      </div>

      <div className="space-y-6">
        <section>
          <h2 className="mb-3 text-sm font-bold text-savant">Count</h2>
          <div className="grid grid-cols-3 gap-3">
            <NumberSelect label="Balls" value={value.balls} max={3} onChange={(next) => update("balls", next)} />
            <NumberSelect label="Strikes" value={value.strikes} max={2} onChange={(next) => update("strikes", next)} />
            <NumberSelect label="Outs" value={value.outs} max={2} onChange={(next) => update("outs", next)} />
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-sm font-bold text-savant">Bases</h2>
          <div className="grid grid-cols-3 gap-3">
            <Toggle label="1B" checked={value.on_1b} onChange={(next) => update("on_1b", next)} />
            <Toggle label="2B" checked={value.on_2b} onChange={(next) => update("on_2b", next)} />
            <Toggle label="3B" checked={value.on_3b} onChange={(next) => update("on_3b", next)} />
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-sm font-bold text-savant">Matchup</h2>
          <div className="grid grid-cols-2 gap-3">
            <Handedness label="Batter" value={value.batter_hand} onChange={(next) => update("batter_hand", next)} />
            <Handedness label="Pitcher" value={value.pitcher_hand} onChange={(next) => update("pitcher_hand", next)} />
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-sm font-bold text-savant">Previous Pitch</h2>
          <select
            value={value.prev_pitch ?? ""}
            onChange={(event) => update("prev_pitch", (event.target.value || null) as PitchCode | null)}
            className="focus-ring h-10 w-full border border-line bg-white px-3 text-sm text-slate-900"
          >
            <option value="">None</option>
            {PITCHES.map((pitch) => (
              <option key={pitch.code} value={pitch.code}>
                {pitch.code} - {pitch.label}
              </option>
            ))}
          </select>
          <p className="mt-2 border-l-2 border-amber bg-orange-50 px-3 py-2 text-xs leading-5 text-amber">
            Model recommendations are intended for situations where at least one pitch has already been thrown in the at-bat.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-sm font-bold text-savant">Arsenal</h2>
          <div className="grid grid-cols-2 gap-2">
            {PITCHES.map((pitch) => (
              <label
                key={pitch.code}
                className="flex h-10 items-center gap-2 border border-line bg-white px-3 text-sm text-slate-800"
              >
                <input
                  data-testid={`arsenal-${pitch.code}`}
                  type="checkbox"
                  checked={value.available_pitches.includes(pitch.code)}
                  onChange={() => togglePitch(pitch.code)}
                  className="h-4 w-4 accent-clay"
                />
                <span className="font-mono text-xs font-bold text-savant">{pitch.code}</span>
                <span className="truncate">{pitch.label}</span>
              </label>
            ))}
          </div>
        </section>
      </div>
    </aside>
  );
}

function NumberSelect({
  label,
  value,
  max,
  onChange,
}: {
  label: string;
  value: number;
  max: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-semibold text-slate-600">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="focus-ring h-10 w-full border border-line bg-white px-3 text-sm text-slate-900"
      >
        {Array.from({ length: max + 1 }, (_, index) => (
          <option key={index} value={index}>
            {index}
          </option>
        ))}
      </select>
    </label>
  );
}

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={checked}
      onClick={() => onChange(!checked)}
      className={`focus-ring h-10 border px-3 text-sm font-semibold ${
        checked ? "border-clay bg-clay text-white" : "border-line bg-white text-slate-700"
      }`}
    >
      {label}
    </button>
  );
}

function Handedness({
  label,
  value,
  onChange,
}: {
  label: string;
  value: "L" | "R";
  onChange: (value: "L" | "R") => void;
}) {
  return (
    <div>
      <span className="mb-1 block text-xs font-semibold text-slate-600">{label}</span>
      <div className="grid grid-cols-2 border border-line bg-white">
        {(["L", "R"] as const).map((hand) => (
          <button
            key={hand}
            type="button"
            aria-pressed={value === hand}
            onClick={() => onChange(hand)}
            className={`focus-ring h-10 text-sm font-semibold ${
              value === hand ? "bg-savant text-white" : "text-slate-700"
            }`}
          >
            {hand}
          </button>
        ))}
      </div>
    </div>
  );
}
