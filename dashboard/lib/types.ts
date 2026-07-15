export type Severity = "critical" | "high" | "medium" | "low" | "info" | string;

export interface Issue {
  severity: Severity;
  title: string;
  value?: unknown;
}

export interface EeatScores {
  experience: number;
  expertise: number;
  authoritativeness: number;
  trustworthiness: number;
}

export interface CategoryFinding {
  title: string;
  severity: Severity;
  description: string;
  recommendation: string;
}

export interface Category {
  name: string;
  score: number;
  findings: CategoryFinding[];
}

export interface ActionPhase {
  name: string;
  timeframe: string;
  items: string[];
}

export interface LlmSummary {
  narrative: string;
  top_findings: string[];
  quick_wins: string[];
}

export interface LlmAnalysis {
  business_type?: string;
  summary?: LlmSummary;
  eeat?: EeatScores;
  categories?: Category[];
  action_plan?: { phases: ActionPhase[] };
  error?: string;
}

export interface OnPageSeo {
  title?: string;
  title_length?: number;
  meta_description?: string;
  meta_description_length?: number;
  h1?: string[];
  word_count?: number;
}

export interface AuditReport {
  url?: string;
  status_code?: number;
  scores?: Record<string, number>;
  on_page_seo?: OnPageSeo;
  issues?: Issue[];
}

export interface Lead {
  id: string;
  name: string;
  website?: string | null;
  ort?: string | null;
  branche?: string | null;
}

export interface SeoAudit {
  id: string;
  lead_id: string | null;
  url: string;
  scanned_at: string;
  health_score: number | null;
  on_page_score: number | null;
  content_score: number | null;
  technical_score: number | null;
  schema_score: number | null;
  images_score: number | null;
  issues: Issue[];
  report: AuditReport;
  llm_analysis: LlmAnalysis | null;
  share_token: string | null;
  published_at: string | null;
  leads?: Lead | null;
}

export interface AdminAuditRow {
  id: string;
  lead_id: string | null;
  url: string;
  scanned_at: string;
  health_score: number | null;
  share_token: string | null;
  published_at: string | null;
  lead_name: string | null;
  lead_ort: string | null;
  lead_branche: string | null;
}
