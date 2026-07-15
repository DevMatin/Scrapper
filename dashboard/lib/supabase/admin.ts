import type { AdminAuditRow, SeoAudit } from "../types";
import { createAuthClient, createServiceClient } from "./server";

export async function getAuditByToken(token: string): Promise<SeoAudit | null> {
  const supabase = createServiceClient();
  const { data, error } = await supabase
    .from("seo_audits")
    .select("*, leads(name, website, ort, branche)")
    .eq("share_token", token)
    .not("share_token", "is", null)
    .single();

  if (error || !data) return null;
  return data as SeoAudit;
}

export async function getAdminAudits(): Promise<AdminAuditRow[]> {
  const supabase = await createAuthClient();
  const { data, error } = await supabase
    .from("seo_audits")
    .select("id, lead_id, url, scanned_at, health_score, share_token, published_at, leads(name, ort, branche)")
    .order("scanned_at", { ascending: false });

  if (error) throw new Error(error.message);

  return (data ?? []).map((row) => {
    const lead = row.leads as { name?: string; ort?: string; branche?: string } | null;
    return {
      id: row.id,
      lead_id: row.lead_id,
      url: row.url,
      scanned_at: row.scanned_at,
      health_score: row.health_score,
      share_token: row.share_token,
      published_at: row.published_at,
      lead_name: lead?.name ?? null,
      lead_ort: lead?.ort ?? null,
      lead_branche: lead?.branche ?? null,
    };
  });
}

export async function publishAudit(auditId: string): Promise<string> {
  const supabase = await createAuthClient();
  const token = crypto.randomUUID().replace(/-/g, "").slice(0, 12);

  const { data, error } = await supabase
    .from("seo_audits")
    .update({ share_token: token, published_at: new Date().toISOString() })
    .eq("id", auditId)
    .select("share_token")
    .single();

  if (error) throw new Error(error.message);
  return data.share_token;
}
