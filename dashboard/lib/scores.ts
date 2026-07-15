import type { Issue, Severity } from "./types";

const SEVERITY_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

export function scoreColor(score: number | null): string {
  if (score === null) return "text-slate-400";
  if (score < 50) return "text-red-600";
  if (score < 75) return "text-amber-600";
  return "text-emerald-600";
}

export function scoreBg(score: number | null): string {
  if (score === null) return "bg-slate-200";
  if (score < 50) return "bg-red-500";
  if (score < 75) return "bg-amber-500";
  return "bg-emerald-500";
}

export function scoreRingStroke(score: number | null): string {
  if (score === null) return "#94a3b8";
  if (score < 50) return "#dc2626";
  if (score < 75) return "#d97706";
  return "#059669";
}

export function scoreLabel(score: number | null): string {
  if (score === null) return "Keine Daten";
  if (score < 50) return "Verbesserungsbedarf";
  if (score < 75) return "Solide Basis";
  return "Gut aufgestellt";
}

export function severityStyle(severity: Severity): {
  badge: string;
  dot: string;
} {
  const s = severity.toLowerCase();
  if (s === "critical" || s === "high") {
    return { badge: "bg-red-50 text-red-700 border-red-200", dot: "bg-red-500" };
  }
  if (s === "medium") {
    return { badge: "bg-amber-50 text-amber-800 border-amber-200", dot: "bg-amber-500" };
  }
  if (s === "low") {
    return { badge: "bg-slate-50 text-slate-700 border-slate-200", dot: "bg-slate-400" };
  }
  return { badge: "bg-blue-50 text-blue-700 border-blue-200", dot: "bg-blue-400" };
}

export function sortIssues(issues: Issue[]): Issue[] {
  return [...issues].sort((a, b) => {
    const ao = SEVERITY_ORDER[a.severity.toLowerCase()] ?? 99;
    const bo = SEVERITY_ORDER[b.severity.toLowerCase()] ?? 99;
    return ao - bo;
  });
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("de-DE", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}
