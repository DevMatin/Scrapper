CREATE POLICY "Allow anon insert audits" ON public.seo_audits
  FOR INSERT TO anon WITH CHECK (true);
