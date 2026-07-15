import type { Issue } from "@/lib/types";
import { severityStyle, sortIssues } from "@/lib/scores";

interface IssuesListProps {
  issues: Issue[];
}

export function IssuesList({ issues }: IssuesListProps) {
  const sorted = sortIssues(issues);
  if (!sorted.length) {
    return <p className="text-sm text-slate-500">Keine kritischen Probleme gefunden.</p>;
  }

  return (
    <ul className="space-y-3">
      {sorted.map((issue, i) => {
        const style = severityStyle(issue.severity);
        return (
          <li
            key={`${issue.title}-${i}`}
            className={`flex items-start gap-3 rounded-lg border px-4 py-3 ${style.badge}`}
          >
            <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${style.dot}`} />
            <div>
              <p className="font-medium">{issue.title}</p>
              {Array.isArray(issue.value) && issue.value.length > 0 && (
                <p className="mt-1 text-sm opacity-80">{issue.value.join(", ")}</p>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
