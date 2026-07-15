"use server";

import { redirect } from "next/navigation";
import { createAuthClient } from "@/lib/supabase/server";

export async function loginAction(
  _prev: { error?: string } | null,
  formData: FormData,
): Promise<{ error?: string } | null> {
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;
  const supabase = await createAuthClient();

  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) return { error: error.message };

  redirect("/admin");
}
