"use client";

import { useMemo, useState, useTransition } from "react";
import type { AdminAuditRow } from "@/lib/types";
import { formatDate, scoreColor } from "@/lib/scores";
import { publishAuditAction } from "@/app/admin/actions";

interface AdminAuditTableProps {
  audits: AdminAuditRow[];
}

export function AdminAuditTable({ audits }: AdminAuditTableProps) {
  const [rows, setRows] = useState(audits);
  const [ortFilter, setOrtFilter] = useState("");
  const [brancheFilter, setBrancheFilter] = useState("");
  const [minScore, setMinScore] = useState("");
  const [pending, startTransition] = useTransition();
  const [copied, setCopied] = useState<string | null>(null);

  const filtered = useMemo(() => {
    return rows.filter((r) => {
      if (ortFilter && !(r.lead_ort ?? "").toLowerCase().includes(ortFilter.toLowerCase())) {
        return false;
      }
      if (brancheFilter && !(r.lead_branche ?? "").toLowerCase().includes(brancheFilter.toLowerCase())) {
        return false;
      }
      if (minScore && (r.health_score ?? 0) < Number(minScore)) return false;
      return true;
    });
  }, [rows, ortFilter, brancheFilter, minScore]);

  function reportUrl(token: string) {
    return `${window.location.origin}/report/${token}`;
  }

  function handlePublish(id: string) {
    startTransition(async () => {
      const token = await publishAuditAction(id);
      setRows((prev) =>
        prev.map((r) =>
          r.id === id
            ? { ...r, share_token: token, published_at: new Date().toISOString() }
            : r,
        ),
      );
    });
  }

  async function handleCopy(token: string) {
    await navigator.clipboard.writeText(reportUrl(token));
    setCopied(token);
    setTimeout(() => setCopied(null), 2000);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Ort filtern"
          value={ortFilter}
          onChange={(e) => setOrtFilter(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <input
          type="text"
          placeholder="Branche filtern"
          value={brancheFilter}
          onChange={(e) => setBrancheFilter(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <input
          type="number"
          placeholder="Min. Score"
          value={minScore}
          onChange={(e) => setMinScore(e.target.value)}
          className="w-28 rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Firma</th>
              <th className="px-4 py-3 font-medium">Ort</th>
              <th className="px-4 py-3 font-medium">Score</th>
              <th className="px-4 py-3 font-medium">Datum</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Aktionen</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtered.map((row) => (
              <tr key={row.id} className="hover:bg-slate-50/50">
                <td className="px-4 py-3">
                  <p className="font-medium text-slate-800">{row.lead_name ?? "–"}</p>
                  <p className="text-xs text-slate-500 truncate max-w-[200px]">{row.url}</p>
                </td>
                <td className="px-4 py-3 text-slate-600">{row.lead_ort ?? "–"}</td>
                <td className={`px-4 py-3 font-semibold ${scoreColor(row.health_score)}`}>
                  {row.health_score ?? "–"}
                </td>
                <td className="px-4 py-3 text-slate-600">{formatDate(row.scanned_at)}</td>
                <td className="px-4 py-3">
                  {row.share_token ? (
                    <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-700">
                      Veröffentlicht
                    </span>
                  ) : (
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                      Entwurf
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    {!row.share_token && (
                      <button
                        type="button"
                        disabled={pending}
                        onClick={() => handlePublish(row.id)}
                        className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                      >
                        Veröffentlichen
                      </button>
                    )}
                    {row.share_token && (
                      <button
                        type="button"
                        onClick={() => handleCopy(row.share_token!)}
                        className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                      >
                        {copied === row.share_token ? "Kopiert!" : "Link kopieren"}
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!filtered.length && (
          <p className="px-4 py-8 text-center text-sm text-slate-500">Keine Audits gefunden.</p>
        )}
      </div>
    </div>
  );
}
