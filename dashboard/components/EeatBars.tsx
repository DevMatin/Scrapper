import type { EeatScores } from "@/lib/types";
import { scoreBg } from "@/lib/scores";

const LABELS: { key: keyof EeatScores; label: string }[] = [
  { key: "experience", label: "Erfahrung" },
  { key: "expertise", label: "Fachwissen" },
  { key: "authoritativeness", label: "Autorität" },
  { key: "trustworthiness", label: "Vertrauen" },
];

interface EeatBarsProps {
  eeat: EeatScores;
}

export function EeatBars({ eeat }: EeatBarsProps) {
  return (
    <div className="space-y-4">
      {LABELS.map(({ key, label }) => {
        const value = eeat[key];
        return (
          <div key={key}>
            <div className="mb-1 flex justify-between text-sm">
              <span className="font-medium text-slate-700">{label}</span>
              <span className="text-slate-500">{value}/100</span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full ${scoreBg(value)}`}
                style={{ width: `${value}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
