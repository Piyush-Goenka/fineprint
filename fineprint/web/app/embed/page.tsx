import { marketData, marketDataUpdatedDate } from "@/lib/market-data";
import { ProviderIcon } from "@/components/provider-icon";

const SITE = process.env.NEXT_PUBLIC_SITE_URL || "https://fineprint.flexprice.io";

// Compact, standalone leaderboard sized to read cleanly at ~520px wide inside an iframe.
export default function EmbedPage() {
  const rows = marketData.rows.filter((model) => model.ranked);

  return (
    <div className="card overflow-hidden mx-auto" style={{ maxWidth: 640 }}>
      <header className="flex items-center gap-2.5 border-b border-line px-4 py-3">
        <span className="grid place-items-center rounded-md font-mono font-semibold text-white"
          style={{ width: 20, height: 20, background: "var(--primary-strong)", fontSize: 10 }}>
          F
        </span>
        <div className="leading-tight">
          <div className="text-[13px] font-semibold tracking-tight">FinePrint</div>
          <div className="font-mono text-[10px] text-faint">Flexprice Model Intelligence</div>
        </div>
        <span className="ml-auto inline-flex items-center gap-1.5 font-mono text-[10px] text-muted">
          <span className="size-1.5 rounded-full" style={{ background: "var(--success)" }} />
          updated {marketDataUpdatedDate}
        </span>
      </header>

      <table className="w-full border-collapse text-[13px]">
        <thead>
          <tr>
            <th className="px-4 py-2 text-left font-mono text-[10px] uppercase tracking-[.06em] text-faint">#</th>
            <th className="px-2 py-2 text-left font-mono text-[10px] uppercase tracking-[.06em] text-faint">Model</th>
            <th className="px-2 py-2 text-right font-mono text-[10px] uppercase tracking-[.06em] text-faint">Capability</th>
            <th className="px-2 py-2 text-right font-mono text-[10px] uppercase tracking-[.06em] text-faint">Preference</th>
            <th className="px-4 py-2 text-right font-mono text-[10px] uppercase tracking-[.06em] text-faint">Flexprice Index</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((m) => (
            <tr key={m.id} className="border-t border-line">
              <td className="px-4 py-2.5 text-left font-mono text-faint tnum">{m.rank}</td>
              <td className="px-2 py-2.5 text-left">
                <span className="flex items-center gap-2">
                  <ProviderIcon brand={m.creator} size={14} />
                  <b className="font-semibold">{m.label}</b>
                </span>
              </td>
              <td className="px-2 py-2.5 text-right tnum">{m.metrics?.capability == null ? "—" : m.metrics.capability.toFixed(1)}</td>
              <td className="px-2 py-2.5 text-right tnum">{m.metrics?.preference == null ? "—" : m.metrics.preference.toFixed(1)}</td>
              <td className="px-4 py-2.5 text-right tnum">{m.overall == null ? "—" : m.overall.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <footer className="flex items-center justify-between border-t border-line px-4 py-2.5">
        <span className="font-mono text-[10px] text-faint">Flexprice Index · general model signals</span>
        <a href={SITE} target="_blank" rel="noopener noreferrer"
          className="font-mono text-[11px] font-medium text-accent hover:underline">
          FinePrint by Flexprice ↗
        </a>
      </footer>
    </div>
  );
}
