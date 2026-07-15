import type { ActionPhase } from "@/lib/types";

interface ActionPlanProps {
  phases: ActionPhase[];
}

export function ActionPlan({ phases }: ActionPlanProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {phases.map((phase, i) => (
        <div
          key={phase.name}
          className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <div className="mb-3 flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-100 text-sm font-bold text-indigo-700">
              {i + 1}
            </span>
            <div>
              <h4 className="font-semibold text-slate-800">{phase.name}</h4>
              <p className="text-xs text-slate-500">{phase.timeframe}</p>
            </div>
          </div>
          <ul className="space-y-2">
            {phase.items.map((item, j) => (
              <li key={j} className="flex gap-2 text-sm text-slate-700">
                <span className="mt-0.5 text-slate-300">☐</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
