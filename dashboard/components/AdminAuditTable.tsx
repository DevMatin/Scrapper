"use client";

import { useMemo, useState, useTransition } from "react";
import type { AdminAuditRow } from "@/lib/types";
import { formatDate, scoreColor } from "@/lib/scores";
import { publishAuditAction } from "@/app/admin/actions";
import { AdminAuditDetail } from "@/components/AdminAuditDetail";

interface AdminAuditTableProps {
  audits: AdminAuditRow[];
}

export function AdminAuditTable({ audits }: AdminAuditTableProps) {
  const [rows, setRows] = useState(audits);
  const [openId, setOpenId] = useState<string | null>(null);
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

  function toggleRow(id: string) {
    setOpenId((prev) => (prev === id ? null : id));
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

      <div className="space-y-3">
        {filtered.map((row) => {
          const isOpen = openId === row.id;
          return (
            <div
              key={row.id}
              className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"
            >
              <button
                type="button"
                onClick={() => toggleRow(row.id)}
                className="flex w-full items-center gap-4 px-5 py-4 text-left hover:bg-slate-50/80"
              >
                <span className="text-slate-400">{isOpen ? "▾" : "▸"}</span>
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-slate-800">{row.lead_name ?? "–"}</p>
                  <p className="truncate text-xs text-slate-500">{row.url}</p>
                </div>
                <div className="hidden text-sm text-slate-500 sm:block">{row.lead_ort ?? "–"}</div>
                <div className={`text-lg font-bold ${scoreColor(row.health_score)}`}>
                  {row.health_score ?? "–"}
                </div>
                <div className="hidden text-sm text-slate-500 md:block">
                  {formatDate(row.scanned_at)}
                </div>
                {row.share_token ? (
                  <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-700">
                    Live
                  </span>
                ) : (
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                    Entwurf
                  </span>
                )}
              </button>

              {isOpen && (
                <AdminAuditDetail
                  row={row}
                  pending={pending}
                  copied={copied === row.share_token}
                  onPublish={() => handlePublish(row.id)}
                  onCopy={() => row.share_token && handleCopy(row.share_token)}
                />
              )}
            </div>
          );
        })}
      </div>

      {!filtered.length && (
        <p className="rounded-xl border border-slate-200 bg-white px-4 py-8 text-center text-sm text-slate-500">
          Keine Audits gefunden.
        </p>
      )}
    </div>
  );
}
