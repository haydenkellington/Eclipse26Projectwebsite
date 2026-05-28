"use client";

const DEFINITIONS = [
  {
    term: "Q",
    description: "Model reward for the pitcher in this exact state. Higher is better.",
  },
  {
    term: "Model Seq dRE",
    description: "Delta run expectancy implied by the learned Q-value. Lower is better for the pitcher.",
  },
  {
    term: "Emp dRE",
    description: "Observed average Statcast delta run expectancy for that state and pitch.",
  },
  {
    term: "MLB%",
    description: "How often MLB pitchers threw that pitch in matching states.",
  },
  {
    term: "Weight",
    description: "Normalized model preference from Q-values. Useful for comparison, not a true probability.",
  },
  {
    term: "Whiff%",
    description: "Whiffs divided by swings for matching state and pitch samples.",
  },
  {
    term: "Pitch N",
    description: "Number of Statcast pitches behind the observed metrics for that row.",
  },
];

export function ValueKey() {
  return (
    <section className="border-t border-line bg-white px-5 py-5 lg:px-8">
      <div className="mx-auto max-w-[1500px]">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-clay">Key</p>
            <h2 className="text-lg font-black text-savant">How To Read The Outputs</h2>
          </div>
          <p className="max-w-2xl text-sm leading-6 text-slate-600">
            The bar chart ranks the top displayed pitches by Q-value. In the table, available pitches use darker text;
            unavailable pitches are muted but still show what the model likes overall.
          </p>
        </div>

        <dl className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {DEFINITIONS.map((item) => (
            <div key={item.term} className="border border-line bg-ink px-4 py-3">
              <dt className="font-mono text-xs font-black uppercase tracking-[0.12em] text-savant">{item.term}</dt>
              <dd className="mt-1 text-sm leading-5 text-slate-700">{item.description}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
