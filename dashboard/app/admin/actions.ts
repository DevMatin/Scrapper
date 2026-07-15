"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { publishAudit } from "@/lib/supabase/admin";
import { createAuthClient } from "@/lib/supabase/server";

export async function publishAuditAction(auditId: string): Promise<string> {
  const supabase = await createAuthClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) throw new Error("Nicht angemeldet");

  const token = await publishAudit(auditId);
  revalidatePath("/admin");
  return token;
}

export async function logoutAction() {
  const supabase = await createAuthClient();
  await supabase.auth.signOut();
  redirect("/login");
}
