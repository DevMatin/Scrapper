# SEO Kunden-Dashboard

Next.js Dashboard für Website-Health-Reports. Liest Audits aus Supabase, zeigt Kunden-Reports unter `/report/[token]`.

## Lokal starten

```bash
cp .env.local.example .env.local
# SUPABASE_SERVICE_ROLE_KEY aus Supabase Dashboard → Settings → API
npm install
npm run dev
```

Öffne `http://localhost:3000/admin` (Login erforderlich).

## Vercel Deployment

1. Neues Vercel-Projekt, **Root Directory:** `dashboard`
2. Environment Variables setzen:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY` (nur Server, nicht `NEXT_PUBLIC_`)
   - `ADMIN_EMAIL` (optional)
3. Deploy

## Workflow

1. Lokal scannen: `scrapling seo pipeline "Zahnarzt in Nürnberg" --llm`
2. `/admin` → Audit → **Veröffentlichen** → **Link kopieren**
3. Link an Kunden senden: `https://dein-projekt.vercel.app/report/abc123`

## Supabase Auth

Admin-Login benötigt einen User in Supabase Auth (Dashboard → Authentication → Users).

## Sicherheit

- Kunden-Reports nur über `share_token` (Service Role serverseitig)
- `seo_audits` hat kein öffentliches SELECT für anon
- Lokale Pipeline kann weiterhin per anon INSERT schreiben
