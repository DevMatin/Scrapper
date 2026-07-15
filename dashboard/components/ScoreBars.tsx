import { scoreBg } from "@/lib/scores";

interface ScoreBar {
  label: string;
  value: number | null;
}

interface ScoreBarsProps {
  scores: ScoreBar[];
}

export function ScoreBars({ scores }: ScoreBarsProps) {
  return (
    <div className="space-y-4">
      {scores.map((s) => (
        <div key={s.label}>
          <div className="mb-1 flex justify-between text-sm">
            <span className="font-medium text-slate-700">{s.label}</span>
            <span className="text-slate-500">{s.value ?? "–"}</span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
            <div
              className={`h-full rounded-full transition-all ${scoreBg(s.value)}`}
              style={{ width: `${s.value ?? 0}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
