"use client";
// Model dropdown for the playground. Native <select> can't render a logo per option, so this
// is a small custom listbox: the trigger and every row show the provider's real mark
// (ProviderIcon) beside the model name. No rank/price metadata — just the logo and the name.
import { useEffect, useRef, useState } from "react";
import { ProviderIcon } from "@/components/provider-icon";
import type { OpenRouterModel } from "@/lib/market-data";

function resolve(models: OpenRouterModel[], id: string) {
  const m = models.find((item) => item.id === id);
  return { id, label: m?.label ?? id, brand: m?.creator ?? id.split(/[-/]/)[0] };
}

export function ModelPicker({ models, value, onChange }: {
  models: OpenRouterModel[]; value: string; onChange: (id: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const sel = resolve(models, value);
  const [query, setQuery] = useState("");
  const filtered = models.filter((m) => `${m.label} ${m.creator}`.toLowerCase().includes(query.toLowerCase()));

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("mousedown", onDoc); document.removeEventListener("keydown", onKey); };
  }, [open]);

  return (
    <div ref={ref} className="relative w-full sm:w-auto">
      <button type="button" onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox" aria-expanded={open}
        className="flex items-center gap-2 border border-line bg-surface rounded-lg pl-2.5 pr-2 py-2 text-[13px] font-semibold w-full sm:w-auto sm:min-w-[188px]">
        <ProviderIcon brand={sel.brand} size={16} />
        <span className="truncate flex-1 text-left">{sel.label}</span>
        <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden className="text-faint shrink-0">
          <path d="M2.5 4.5L6 8l3.5-3.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      {open && (
        <ul role="listbox" aria-label="Model"
          className="absolute left-0 sm:left-auto sm:right-0 z-30 mt-1.5 w-full min-w-[248px] max-w-[min(100vw-2rem,248px)] max-h-[300px] overflow-auto rounded-xl border border-line bg-surface p-1 shadow-xl">
          <li className="sticky top-0 bg-surface p-1"><input autoFocus value={query} onChange={(e) => setQuery(e.target.value)} placeholder={`Search ${models.length} OpenRouter models…`} aria-label="Search OpenRouter models" className="w-full rounded-md border border-line bg-surface px-2 py-1.5 text-[12px] outline-none" /></li>
          {filtered.map((item) => {
            const id = item.id;
            const m = resolve(models, id);
            const on = id === value;
            return (
              <li key={id} role="option" aria-selected={on}>
                <button type="button" onClick={() => { onChange(id); setOpen(false); }}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[13px] text-left ${on ? "bg-surface-2 font-semibold" : "hover:bg-surface-2"}`}>
                  <ProviderIcon brand={m.brand} size={17} />
                  <span className="truncate flex-1">{m.label}</span>
                  {on && (
                    <svg width="13" height="13" viewBox="0 0 13 13" aria-hidden className="text-accent shrink-0">
                      <path d="M2.5 6.8l2.7 2.7L10.5 4" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </button>
              </li>
            );
          })}
          {!filtered.length && <li className="px-3 py-2 text-[12px] text-muted">No models found.</li>}
        </ul>
      )}
    </div>
  );
}
