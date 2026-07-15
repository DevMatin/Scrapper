import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-6 text-center">
      <h1 className="text-2xl font-bold text-slate-900">Report nicht gefunden</h1>
      <p className="mt-2 text-slate-600">
        Dieser Link ist ungültig oder der Report wurde noch nicht veröffentlicht.
      </p>
      <Link href="/login" className="mt-6 text-sm text-indigo-600 hover:underline">
        Zum Admin-Bereich
      </Link>
    </div>
  );
}
