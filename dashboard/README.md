# SEO Kunden-Dashboard

Next.js Dashboard für Website-Health-Reports. Liest Audits aus Supabase, zeigt Kunden-Reports unter `/report/[token]`.

## Lokal starten

```bash
cd dashboard
cp .env.local.example .env.local
# Werte aus Supabase Dashboard → Settings → API eintragen
npm install
npm run dev
```

**Wichtig:** Login-Daten (`ADMIN_EMAIL`, `ADMIN_PASSWORD`) müssen in `dashboard/.env.local` stehen — die Root-`.env` des Scrapers wird **nicht** gelesen.

Öffne `http://localhost:3000/admin` (Login erforderlich).

## Vercel Deployment

1. Neues Vercel-Projekt, **Root Directory:** `dashboard`
2. Environment Variables setzen:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY` (nur Server)
   - `ADMIN_EMAIL` + `ADMIN_PASSWORD` (Login)
3. Deploy

## Login

Einfacher E-Mail/Passwort-Login über `ADMIN_EMAIL` und `ADMIN_PASSWORD` in `.env.local` — kein Supabase Auth nötig.

## Workflow

1. Lokal scannen: `scrapling seo pipeline "Zahnarzt in Nürnberg" --llm`
2. `/admin` → Audit → **Veröffentlichen** → **Link kopieren**
3. Link an Kunden senden: `https://dein-projekt.vercel.app/report/abc123`

## Supabase Auth

Nicht mehr nötig. Login läuft über `ADMIN_EMAIL` + `ADMIN_PASSWORD`.

## Sicherheit

- Kunden-Reports nur über `share_token` (Service Role serverseitig)
- `seo_audits` hat kein öffentliches SELECT für anon
- Lokale Pipeline kann weiterhin per anon INSERT schreiben
