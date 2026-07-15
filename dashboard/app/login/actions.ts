"use server";

import { redirect } from "next/navigation";
import { setSessionCookie } from "@/lib/auth";
import { verifyCredentials } from "@/lib/session";

export async function loginAction(
  _prev: { error?: string } | null,
  formData: FormData,
): Promise<{ error?: string } | null> {
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;

  if (!process.env.ADMIN_EMAIL || !process.env.ADMIN_PASSWORD) {
    return { error: "ADMIN_EMAIL und ADMIN_PASSWORD fehlen in .env.local" };
  }

  if (!verifyCredentials(email, password)) {
    return { error: "E-Mail oder Passwort falsch" };
  }

  await setSessionCookie(email);
  redirect("/admin");
}
