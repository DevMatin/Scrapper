-- SEO audit results from scrapling seo integration
CREATE TABLE IF NOT EXISTS public.seo_audits (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid REFERENCES public.leads(id),
  url text NOT NULL,
  scanned_at timestamptz DEFAULT now(),
  health_score int,
  on_page_score int,
  content_score int,
  technical_score int,
  schema_score int,
  images_score int,
  issues jsonb DEFAULT '[]'::jsonb,
  report jsonb NOT NULL,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_seo_audits_url ON public.seo_audits(url);
CREATE INDEX IF NOT EXISTS idx_seo_audits_lead ON public.seo_audits(lead_id);
