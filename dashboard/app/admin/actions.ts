"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { clearSessionCookie, getSessionEmail } from "@/lib/auth";
import { publishAudit } from "@/lib/supabase/admin";

export async function publishAuditAction(auditId: string): Promise<string> {
  const email = await getSessionEmail();
  if (!email) throw new Error("Nicht angemeldet");

  const token = await publishAudit(auditId);
  revalidatePath("/admin");
  return token;
}

export async function logoutAction() {
  await clearSessionCookie();
  redirect("/login");
}
