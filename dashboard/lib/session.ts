const COOKIE_NAME = "admin_session";
const MAX_AGE_SEC = 60 * 60 * 24 * 7;

function getSecret(): string {
  return (
    process.env.ADMIN_SECRET ||
    process.env.SUPABASE_SERVICE_ROLE_KEY ||
    "dashboard-dev-secret"
  );
}

async function sign(payload: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(getSecret()),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(payload));
  return Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export function getSessionCookieName(): string {
  return COOKIE_NAME;
}

export function getSessionMaxAge(): number {
  return MAX_AGE_SEC;
}

export async function createSessionToken(email: string): Promise<string> {
  const exp = Date.now() + MAX_AGE_SEC * 1000;
  const payload = `${email.toLowerCase()}:${exp}`;
  const signature = await sign(payload);
  return `${payload}:${signature}`;
}

export async function verifySessionToken(token: string): Promise<string | null> {
  const parts = token.split(":");
  if (parts.length < 3) return null;

  const signature = parts.pop()!;
  const expStr = parts.pop()!;
  const email = parts.join(":");

  if (!email || !expStr || !signature) return null;
  if (Date.now() > Number(expStr)) return null;

  const payload = `${email}:${expStr}`;
  const expected = await sign(payload);
  if (signature.length !== expected.length) return null;

  let match = true;
  for (let i = 0; i < signature.length; i++) {
    if (signature[i] !== expected[i]) match = false;
  }
  if (!match) return null;

  return email;
}

export function verifyCredentials(email: string, password: string): boolean {
  const adminEmail = process.env.ADMIN_EMAIL?.trim().toLowerCase();
  const adminPassword = process.env.ADMIN_PASSWORD?.trim();
  if (!adminEmail || !adminPassword) return false;
  return email.trim().toLowerCase() === adminEmail && password.trim() === adminPassword;
}
