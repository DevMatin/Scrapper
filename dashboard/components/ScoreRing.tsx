import { scoreColor, scoreLabel, scoreRingStroke } from "@/lib/scores";

interface ScoreRingProps {
  score: number | null;
  size?: number;
}

export function ScoreRing({ score, size = 160 }: ScoreRingProps) {
  const value = score ?? 0;
  const stroke = 10;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#e2e8f0"
            strokeWidth={stroke}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={scoreRingStroke(score)}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-4xl font-bold ${scoreColor(score)}`}>
            {score ?? "–"}
          </span>
          <span className="text-xs text-slate-500">/ 100</span>
        </div>
      </div>
      <p className={`text-sm font-medium ${scoreColor(score)}`}>{scoreLabel(score)}</p>
    </div>
  );
}
