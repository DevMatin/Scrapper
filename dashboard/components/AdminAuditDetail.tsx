import type { AdminAuditRow } from "@/lib/types";
import { ScoreBars } from "@/components/ScoreBars";
import { IssuesList } from "@/components/IssuesList";
import { QuickWins } from "@/components/QuickWins";
import Link from "next/link";

interface AdminAuditDetailProps {
  row: AdminAuditRow;
  pending: boolean;
  copied: boolean;
  onPublish: () => void;
  onCopy: () => void;
}

export function AdminAuditDetail({
  row,
  pending,
  copied,
  onPublish,
  onCopy,
}: AdminAuditDetailProps) {
  const quickWins = row.llm_analysis?.summary?.quick_wins ?? [];
  const narrative = row.llm_analysis?.summary?.narrative;

  const scores = [
    { label: "On-Page SEO", value: row.on_page_score },
    { label: "Content", value: row.content_score },
    { label: "Technik", value: row.technical_score },
    { label: "Schema", value: row.schema_score },
    { label: "Bilder", value: row.images_score },
  ];

  return (
    <div className="space-y-5 border-t border-slate-100 bg-slate-50/60 px-5 py-5">
      <div className="grid gap-5 lg:grid-cols-2">
        <div>
          <h4 className="mb-3 text-sm font-semibold text-slate-700">Teilscores</h4>
          <ScoreBars scores={scores} />
        </div>
        <div>
          <h4 className="mb-3 text-sm font-semibold text-slate-700">Wichtigste Probleme</h4>
          <IssuesList issues={row.issues} />
        </div>
      </div>

      {narrative && (
        <div>
          <h4 className="mb-2 text-sm font-semibold text-slate-700">Zusammenfassung</h4>
          <p className="text-sm leading-relaxed text-slate-600">{narrative}</p>
        </div>
      )}

      {quickWins.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-semibold text-slate-700">Quick Wins</h4>
          <QuickWins items={quickWins} />
        </div>
      )}

      <div className="flex flex-wrap gap-2 pt-1">
        <Link
          href={`/admin/preview/${row.id}`}
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
        >
          Vollständige Vorschau
        </Link>
        {!row.share_token && (
          <button
            type="button"
            disabled={pending}
            onClick={onPublish}
            className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            Veröffentlichen
          </button>
        )}
        {row.share_token && (
          <>
            <Link
              href={`/report/${row.share_token}`}
              target="_blank"
              className="rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-100"
            >
              Kunden-Report öffnen
            </Link>
            <button
              type="button"
              onClick={onCopy}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
            >
              {copied ? "Kopiert!" : "Link kopieren"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
