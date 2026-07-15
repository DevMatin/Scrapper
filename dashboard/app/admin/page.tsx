import { redirect } from "next/navigation";
import { getAdminAudits } from "@/lib/supabase/admin";
import { createAuthClient } from "@/lib/supabase/server";
import { AdminAuditTable } from "@/components/AdminAuditTable";
import { logoutAction } from "./actions";

export const dynamic = "force-dynamic";

export default async function AdminPage() {
  const supabase = await createAuthClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const adminEmail = process.env.ADMIN_EMAIL;
  if (adminEmail && user.email !== adminEmail) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-slate-600">Kein Zugriff.</p>
      </div>
    );
  }

  let audits;
  try {
    audits = await getAdminAudits();
  } catch {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-slate-600">Fehler beim Laden der Audits.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-bold text-slate-900">SEO Dashboard</h1>
            <p className="text-sm text-slate-500">{user.email}</p>
          </div>
          <form action={logoutAction}>
            <button
              type="submit"
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
            >
              Abmelden
            </button>
          </form>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <AdminAuditTable audits={audits} />
      </main>
    </div>
  );
}
