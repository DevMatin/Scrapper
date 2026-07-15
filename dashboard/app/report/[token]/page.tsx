import { notFound } from "next/navigation";
import { getAuditByToken } from "@/lib/supabase/admin";
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
  params: Promise<{ token: string }>;
}

export default async function ReportPage({ params }: PageProps) {
  const { token } = await params;
  const audit = await getAuditByToken(token);
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
    <div className="min-h-screen bg-slate-50 print:bg-white">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-4xl px-6 py-8">
          <p className="text-sm font-medium uppercase tracking-wider text-indigo-600">
            Website Health Report
          </p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            {lead?.name ?? "Website-Analyse"}
          </h1>
          <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-600">
            {audit.url && (
              <a href={audit.url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">
                {audit.url}
              </a>
            )}
            {lead?.ort && <span>{lead.ort}</span>}
            {lead?.branche && <span>{lead.branche}</span>}
            <span>Analysiert am {formatDate(audit.scanned_at)}</span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl space-y-8 px-6 py-8">
        <section className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <h2 className="mb-6 text-lg font-semibold text-slate-800">Gesundheits-Score</h2>
          <div className="flex flex-col items-center gap-8 md:flex-row md:items-start">
            <ScoreRing score={audit.health_score} />
            <div className="flex-1 w-full">
              <ScoreBars scores={scoreItems} />
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-slate-800">Wichtigste Probleme</h2>
          <IssuesList issues={audit.issues} />
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-slate-800">Zusammenfassung</h2>
          <p className="leading-relaxed text-slate-700">{narrative}</p>
        </section>

        {summary?.quick_wins && summary.quick_wins.length > 0 && (
          <section className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-8">
            <h2 className="mb-4 text-lg font-semibold text-emerald-900">Schnelle Verbesserungen</h2>
            <QuickWins items={summary.quick_wins} />
          </section>
        )}

        {llm?.eeat && (
          <section className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-slate-800">E-E-A-T Bewertung</h2>
            <p className="mb-4 text-sm text-slate-500">
              Experience, Expertise, Authoritativeness, Trustworthiness
            </p>
            <EeatBars eeat={llm.eeat} />
          </section>
        )}

        {llm?.categories && llm.categories.length > 0 && (
          <section className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-slate-800">Detailanalyse</h2>
            <CategoryAccordion categories={llm.categories} />
          </section>
        )}

        {llm?.action_plan?.phases && llm.action_plan.phases.length > 0 && (
          <section className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-slate-800">Maßnahmenplan</h2>
            <ActionPlan phases={llm.action_plan.phases} />
          </section>
        )}

        {audit.report?.on_page_seo && (
          <section className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm print:break-inside-avoid">
            <h2 className="mb-4 text-lg font-semibold text-slate-800">On-Page Übersicht</h2>
            <dl className="grid gap-3 text-sm md:grid-cols-2">
              <div>
                <dt className="text-slate-500">Title</dt>
                <dd className="font-medium text-slate-800">{audit.report.on_page_seo.title ?? "–"}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Meta Description</dt>
                <dd className="font-medium text-slate-800">{audit.report.on_page_seo.meta_description ?? "–"}</dd>
              </div>
              <div>
                <dt className="text-slate-500">H1</dt>
                <dd className="font-medium text-slate-800">
                  {audit.report.on_page_seo.h1?.join(", ") ?? "–"}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Wortanzahl</dt>
                <dd className="font-medium text-slate-800">{audit.report.on_page_seo.word_count ?? "–"}</dd>
              </div>
            </dl>
          </section>
        )}
      </main>

      <footer className="border-t border-slate-200 bg-white py-6 text-center text-sm text-slate-500 print:mt-8">
        Erstellt am {formatDate(audit.scanned_at)} · SEO Website Health Report
      </footer>
    </div>
  );
}
