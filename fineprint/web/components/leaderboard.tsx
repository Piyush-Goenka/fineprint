"use client";

import { useMemo, useState } from "react";
import { marketData, type ExternalModel } from "@/lib/market-data";
import { ProviderIcon } from "@/components/provider-icon";
import Link from "next/link";

const PREVIEW = 20;
const metricValue = (model: ExternalModel, key: "capability" | "preference" | "adoption") => {
  const value = model.metrics?.[key];
  return value == null ? "—" : value.toFixed(1);
};
type SortKey = "rank" | "model" | "capability" | "preference" | "adoption" | "overall";
const SORT_LABELS: Record<SortKey, string> = {
  rank: "Rank", model: "Model", capability: "Capability", preference: "Preference", adoption: "Adoption", overall: "Flexprice Index",
};
const SORT_INFO: Partial<Record<SortKey, string>> = {
  capability: "Published benchmark result, or a calibrated score from model features when a benchmark is unavailable.",
  preference: "How often developers select the model, with Arena ratings included when available.",
  adoption: "Monthly token volume processed through OpenRouter.",
  overall: "Weighted score: 40% capability, 35% preference, and 25% adoption.",
};
const SOURCE_LABELS: Record<string, string> = { artificial_analysis: "Artificial Analysis", arena: "Arena", openrouter: "OpenRouter" };

export function Leaderboard() {
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState(false);
  const [sort, setSort] = useState<SortKey>("rank");
  const [direction, setDirection] = useState<"asc" | "desc">("asc");
  const rows = useMemo(() => marketData.rows.filter((m) => `${m.label} ${m.creator}`.toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => {
      const av = sort === "model" ? a.label.toLowerCase() : sort === "rank" ? a.rank : sort === "overall" ? a.overall : a.metrics?.[sort];
      const bv = sort === "model" ? b.label.toLowerCase() : sort === "rank" ? b.rank : sort === "overall" ? b.overall : b.metrics?.[sort];
      if (av == null && bv != null) return 1;
      if (av != null && bv == null) return -1;
      const order = typeof av === "string" && typeof bv === "string" ? av.localeCompare(bv) : (Number(av ?? -Infinity) - Number(bv ?? -Infinity));
      return (direction === "asc" ? order : -order) || (a.rank ?? Infinity) - (b.rank ?? Infinity);
    }), [query, sort, direction]);
  const visible = expanded ? rows : rows.slice(0, PREVIEW);
  const sortHeader = (key: SortKey, align: "left" | "right") => {
    const info = SORT_INFO[key];
    const active = sort === key;
    return <button type="button" onClick={() => { if (active) setDirection(direction === "asc" ? "desc" : "asc"); else { setSort(key); setDirection(key === "model" ? "asc" : "desc"); } }}
      className={`inline-flex items-center gap-1 hover:text-text ${align === "right" ? "justify-end" : "justify-start"}`} aria-label={`Sort by ${SORT_LABELS[key]}${info ? `. ${info}` : ""}`}>
      {SORT_LABELS[key]}{info && <span aria-hidden="true" className="normal-case text-faint" title={info}>ⓘ</span>}
      <span aria-hidden="true" className="w-2 text-accent">{active ? direction === "asc" ? "↑" : "↓" : ""}</span>
    </button>;
  };

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-b border-line">
        <div className="text-[12px] text-muted">Updated {new Date(marketData.as_of).toLocaleDateString()}</div>
        <input aria-label="Search models" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search models…" className="rounded-lg border border-line bg-surface px-3 py-2 text-[12px] outline-none focus:border-accent" />
      </div>
      {marketData.source_errors && Object.keys(marketData.source_errors).length > 0 && <p className="px-4 py-2 text-[12px] text-warning">{Object.keys(marketData.source_errors).map((key) => SOURCE_LABELS[key] ?? key).join(" and ")} did not respond during this refresh.</p>}
      <div className="overflow-x-auto">
        <table className="w-full text-[12.5px]">
          <thead><tr className="text-muted border-b border-line text-[11px] uppercase tracking-wide">
            <th aria-sort={sort === "rank" || sort === "model" ? (direction === "asc" ? "ascending" : "descending") : "none"} className="text-left px-4 py-3">{sortHeader("rank", "left")}<span className="mx-1">/</span>{sortHeader("model", "left")}</th>
            {(["capability", "preference", "adoption", "overall"] as const).map((key) => <th key={key} aria-sort={sort === key ? (direction === "asc" ? "ascending" : "descending") : "none"} className="text-right px-3 py-3">{sortHeader(key, "right")}</th>)}
          </tr></thead>
          <tbody>{visible.map((m: ExternalModel) => <tr key={m.id} className="border-b border-line/70 hover:bg-surface-2/50">
            <td className="px-4 py-3"><span className="text-faint mr-3 tabular-nums">{m.rank ?? "—"}</span><span className="inline-flex items-center gap-2"><ProviderIcon brand={m.id.toLowerCase().includes("space-bunny") ? "space-bunny" : m.creator} size={17} /><Link href={`/models/${encodeURIComponent(m.id)}`} className="font-medium hover:text-accent">{m.label}</Link></span></td>
            <td className="text-right px-3 py-3 tabular-nums">{metricValue(m, "capability")}</td>
            <td className="text-right px-3 py-3 tabular-nums">{metricValue(m, "preference")}</td>
            <td className="text-right px-3 py-3 tabular-nums">{metricValue(m, "adoption")}</td>
            <td className="text-right px-4 py-3 font-semibold tabular-nums">
              {m.overall == null ? "—" : m.overall.toFixed(1)}
            </td>
          </tr>)}</tbody>
        </table>
      </div>
      {!rows.length && <p className="p-8 text-center text-muted">No matching models.</p>}
      {rows.length > PREVIEW && <button className="w-full py-3 text-[12px] text-accent hover:bg-surface-2/50" onClick={() => setExpanded(!expanded)}>{expanded ? "Show fewer models" : `Show all ${rows.length} models`}</button>}
      <div className="px-4 py-3 border-t border-line text-[10.5px] leading-relaxed text-muted">Scores use a 0–100 scale and combine public benchmarks, model specifications, and developer activity. The Index describes the broader model landscape, not FinePrint contract-extraction accuracy. Read the <Link href="/methodology" className="text-accent hover:underline">methodology</Link>.</div>
    </div>
  );
}
