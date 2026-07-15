CREATE POLICY "Allow anon read leads" ON public.leads FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon insert leads" ON public.leads FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Allow authenticated read leads" ON public.leads FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated insert leads" ON public.leads FOR INSERT TO authenticated WITH CHECK (true);

GRANT SELECT, INSERT ON public.leads TO anon;
GRANT SELECT, INSERT ON public.leads TO authenticated;
GRANT SELECT, INSERT ON public.seo_audits TO anon;
GRANT SELECT, INSERT ON public.seo_audits TO authenticated;
