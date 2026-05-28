"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PitchComparison, RecommendationResponse } from "@/lib/types";

type Props = {
  recommendation: RecommendationResponse | null;
};

export function ComparisonPanel({ recommendation }: Props) {
  if (!recommendation) {
    return null;
  }

  const chartData = recommendation.comparison.slice(0, 6).map((row) => ({
    pitch: row.pitch,
    value: row.q_value,
    available: row.available ? "Yes" : "No",
  }));

  return (
    <aside className="border-l border-line bg-panel px-5 py-5 lg:min-h-[calc(100vh-89px)]">
      <div className="mb-5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-clay">Explainability</p>
        <h2 className="text-xl font-black text-savant">Pitch Comparison</h2>
      </div>

      <div className="h-52 border border-line bg-ink p-3">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 12, right: 8, left: -28, bottom: 0 }}>
            <CartesianGrid stroke="#d8e0e8" vertical={false} />
            <XAxis dataKey="pitch" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
            <Tooltip
              cursor={{ fill: "rgba(201, 33, 39, 0.08)" }}
              contentStyle={{ background: "#ffffff", border: "1px solid #d8e0e8", color: "#17212b" }}
            />
            <Bar dataKey="value" fill="#c92127" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-5 overflow-x-auto border border-line">
        <table className="w-full min-w-[620px] border-collapse text-sm">
          <thead className="bg-savant text-xs uppercase tracking-[0.12em] text-white">
            <tr>
              <Th>Pitch</Th>
              <Th>Q</Th>
              <Th>Model Exp dRE</Th>
              <Th>MLB%</Th>
              <Th>Weight</Th>
              <Th>Whiff%</Th>
              <Th>N</Th>
            </tr>
          </thead>
          <tbody>
            {recommendation.comparison.map((row) => (
              <ComparisonRow key={row.pitch} row={row} />
            ))}
          </tbody>
        </table>
      </div>
    </aside>
  );
}

function ComparisonRow({ row }: { row: PitchComparison }) {
  return (
    <tr className={row.available ? "border-t border-line bg-white text-slate-900" : "border-t border-line bg-slate-50 text-slate-500"}>
      <Td>
        <span className="inline-flex items-baseline gap-2">
          <span className={row.available ? "font-mono text-xs font-bold text-clay" : "font-mono text-xs font-bold text-slate-500"}>{row.pitch}</span>
          <span>{row.pitch_name}</span>
        </span>
      </Td>
      <Td>{signed(row.q_value)}</Td>
      <Td>{signed(row.expected_delta_run_exp_from_q)}</Td>
      <Td>{percent(row.mlb_frequency)}</Td>
      <Td>{percent(row.model_weight)}</Td>
      <Td>{percent(row.whiff_rate)}</Td>
      <Td>{row.sample_size.toLocaleString()}</Td>
    </tr>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-3 py-3 text-left font-semibold">{children}</th>;
}

function Td({ children }: { children: React.ReactNode }) {
  return <td className="px-3 py-3 align-middle">{children}</td>;
}

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function signed(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(3)}`;
}
