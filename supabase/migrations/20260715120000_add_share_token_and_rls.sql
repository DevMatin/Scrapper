ALTER TABLE public.seo_audits
  ADD COLUMN IF NOT EXISTS share_token text UNIQUE,
  ADD COLUMN IF NOT EXISTS published_at timestamptz;

CREATE INDEX IF NOT EXISTS idx_seo_audits_share_token ON public.seo_audits(share_token);

ALTER TABLE public.seo_audits ENABLE ROW LEVEL SECURITY;

REVOKE SELECT ON public.seo_audits FROM anon;
GRANT INSERT ON public.seo_audits TO anon;

DROP POLICY IF EXISTS "auth_read_audits" ON public.seo_audits;
CREATE POLICY "auth_read_audits" ON public.seo_audits
  FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "auth_update_audits" ON public.seo_audits;
CREATE POLICY "auth_update_audits" ON public.seo_audits
  FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

GRANT SELECT, UPDATE ON public.seo_audits TO authenticated;
