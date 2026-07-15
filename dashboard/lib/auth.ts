import { cookies } from "next/headers";
import {
  createSessionToken,
  getSessionCookieName,
  getSessionMaxAge,
  verifySessionToken,
} from "./session";

export async function getSessionEmail(): Promise<string | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get(getSessionCookieName())?.value;
  if (!token) return null;
  return verifySessionToken(token);
}

export async function setSessionCookie(email: string): Promise<void> {
  const cookieStore = await cookies();
  const token = await createSessionToken(email);
  cookieStore.set(getSessionCookieName(), token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: getSessionMaxAge(),
    path: "/",
  });
}

export async function clearSessionCookie(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(getSessionCookieName());
}
