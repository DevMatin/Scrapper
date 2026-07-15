import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { getSessionEmail } from "@/lib/auth";
import { getAuditById } from "@/lib/supabase/admin";
import { formatDate } from "@/lib/scores";
import { ScoreRing } from "@/components/ScoreRing";
import { ScoreBars } from "@/components/ScoreBars";
import { IssuesList } from "@/components/IssuesList";
import { QuickWins } from "@/components/QuickWins";
import { EeatBars } from "@/components/EeatBars";
import { CategoryAccordion } from "@/components/CategoryAccordion";
import { ActionPlan } from "@/components/ActionPlan";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function AdminPreviewPage({ params }: PageProps) {
  const email = await getSessionEmail();
  if (!email) redirect("/login");

  const { id } = await params;
  const audit = await getAuditById(id);
  if (!audit) notFound();

  const lead = audit.leads;
  const llm = audit.llm_analysis;
  const summary = llm?.summary;
  const narrative =
    summary?.narrative ??
    (audit.issues.length
      ? `Die Website wurde analysiert. Es wurden ${audit.issues.length} Verbesserungspunkte identifiziert.`
      : "Die Website wurde analysiert. Keine kritischen Probleme gefunden.");

  const scoreItems = [
    { label: "On-Page SEO", value: audit.on_page_score },
    { label: "Content", value: audit.content_score },
    { label: "Technik", value: audit.technical_score },
    { label: "Schema / Strukturierte Daten", value: audit.schema_score },
    { label: "Bilder", value: audit.images_score },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-amber-600">Admin Vorschau</p>
            <h1 className="text-xl font-bold text-slate-900">{lead?.name ?? "Website-Analyse"}</h1>
          </div>
          <Link
            href="/admin"
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
          >
            Zurück
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-4xl space-y-6 px-6 py-8">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex flex-wrap gap-3 text-sm text-slate-600">
            <a href={audit.url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">
              {audit.url}
            </a>
            <span>{formatDate(audit.scanned_at)}</span>
          </div>
          <div className="flex flex-col items-center gap-6 md:flex-row md:items-start">
            <ScoreRing score={audit.health_score} />
            <div className="w-full flex-1">
              <ScoreBars scores={scoreItems} />
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-slate-800">Wichtigste Probleme</h2>
          <IssuesList issues={audit.issues} />
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-slate-800">Zusammenfassung</h2>
          <p className="leading-relaxed text-slate-700">{narrative}</p>
        </section>

        {summary?.quick_wins && summary.quick_wins.length > 0 && (
          <section className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-6">
            <h2 className="mb-4 text-lg font-semibold text-emerald-900">Schnelle Verbesserungen</h2>
            <QuickWins items={summary.quick_wins} />
          </section>
        )}

        {llm?.eeat && (
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-slate-800">E-E-A-T</h2>
            <EeatBars eeat={llm.eeat} />
          </section>
        )}

        {llm?.categories && llm.categories.length > 0 && (
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-slate-800">Detailanalyse</h2>
            <CategoryAccordion categories={llm.categories} />
          </section>
        )}

        {llm?.action_plan?.phases && llm.action_plan.phases.length > 0 && (
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-slate-800">Maßnahmenplan</h2>
            <ActionPlan phases={llm.action_plan.phases} />
          </section>
        )}
      </main>
    </div>
  );
}
