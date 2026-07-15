"use client";

import { useActionState } from "react";
import { loginAction } from "./actions";

export default function LoginPage() {
  const [state, formAction, pending] = useActionState(loginAction, null);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <form
        action={formAction}
        className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-8 shadow-sm"
      >
        <h1 className="mb-6 text-xl font-bold text-slate-900">Admin Login</h1>

        {state?.error && (
          <p className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{state.error}</p>
        )}

        <label className="mb-4 block">
          <span className="mb-1 block text-sm text-slate-600">E-Mail</span>
          <input
            name="email"
            type="email"
            required
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
        </label>

        <label className="mb-6 block">
          <span className="mb-1 block text-sm text-slate-600">Passwort</span>
          <input
            name="password"
            type="password"
            required
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
        </label>

        <button
          type="submit"
          disabled={pending}
          className="w-full rounded-lg bg-indigo-600 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {pending ? "Anmelden…" : "Anmelden"}
        </button>
      </form>
    </div>
  );
}
