"use client";

import { useState } from "react";
import type { Category } from "@/lib/types";
import { severityStyle } from "@/lib/scores";

interface CategoryAccordionProps {
  categories: Category[];
}

export function CategoryAccordion({ categories }: CategoryAccordionProps) {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <div className="divide-y divide-slate-200 rounded-xl border border-slate-200">
      {categories.map((cat, i) => {
        const isOpen = open === i;
        return (
          <div key={cat.name}>
            <button
              type="button"
              onClick={() => setOpen(isOpen ? null : i)}
              className="flex w-full items-center justify-between px-5 py-4 text-left hover:bg-slate-50"
            >
              <div>
                <p className="font-semibold text-slate-800">{cat.name}</p>
                <p className="text-sm text-slate-500">{cat.findings.length} Erkenntnisse</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700">
                  {cat.score}/100
                </span>
                <span className="text-slate-400">{isOpen ? "▲" : "▼"}</span>
              </div>
            </button>
            {isOpen && (
              <div className="space-y-4 border-t border-slate-100 bg-slate-50/50 px-5 py-4">
                {cat.findings.map((f, fi) => {
                  const style = severityStyle(f.severity);
                  return (
                    <div key={fi} className="rounded-lg border border-slate-200 bg-white p-4">
                      <div className="mb-2 flex items-center gap-2">
                        <span className={`rounded px-2 py-0.5 text-xs font-medium border ${style.badge}`}>
                          {f.severity}
                        </span>
                        <h4 className="font-medium text-slate-800">{f.title}</h4>
                      </div>
                      <p className="mb-2 text-sm text-slate-600">{f.description}</p>
                      <p className="text-sm text-emerald-700">
                        <span className="font-medium">Empfehlung: </span>
                        {f.recommendation}
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
