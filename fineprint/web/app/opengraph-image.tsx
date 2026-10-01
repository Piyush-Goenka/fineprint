import { ImageResponse } from "next/og";
import { marketData } from "@/lib/market-data";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "FinePrint: Flexprice Model Intelligence and contract extraction";

export default function OpengraphImage() {
  const top = marketData.rows[0];
  const mono = 'ui-monospace, "SF Mono", Menlo, monospace';
  return new ImageResponse(
    <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", background: "#0a0e1a", color: "#f2eee1", padding: 64, justifyContent: "space-between" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}><div style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 40, height: 40, borderRadius: 10, background: "#e84e1f", fontSize: 22, fontFamily: mono, color: "#fff", fontWeight: 600 }}>F</div><div style={{ fontSize: 26, fontWeight: 600 }}>FinePrint</div></div>
      <div style={{ display: "flex", flexDirection: "column" }}><div style={{ display: "flex", fontSize: 15, letterSpacing: 3, color: "#f15a2b", fontFamily: mono }}>FLEXPRICE MODEL INTELLIGENCE</div><div style={{ display: "flex", fontSize: 68, fontWeight: 700, letterSpacing: -2, marginTop: 18 }}>{top?.label ?? "Model rankings"}</div><div style={{ display: "flex", fontSize: 22, color: "#9299a3", marginTop: 20 }}>Ranked #{top?.rank ?? "—"} of {marketData.n_ranked} · Flexprice Index</div></div>
      <div style={{ display: "flex", justifyContent: "space-between", borderTop: "1px solid #23252a", paddingTop: 30, color: "#9299a3", fontSize: 16, fontFamily: mono }}><div style={{ display: "flex" }}>Capability · Preference · Adoption</div><div style={{ display: "flex" }}>fineprint by flexprice</div></div>
    </div>, { ...size }
  );
}
