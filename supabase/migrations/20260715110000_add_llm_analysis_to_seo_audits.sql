-- Add LLM enrichment column to seo_audits
ALTER TABLE public.seo_audits
  ADD COLUMN IF NOT EXISTS llm_analysis jsonb;
