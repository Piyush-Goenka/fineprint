// Lab marks. Eight labs render as their authentic full-color logo (public/icons/color/*.svg);
// OpenAI and xAI are genuinely monochrome brands, so they render as a theme-adaptive currentColor
// silhouette via CSS mask (dark on light, light on dark). brand id (registry) -> asset.
const COLOR: Record<string, string> = {
  anthropic: "anthropic", claude: "anthropic",
  google: "google", gemini: "google",
  meta: "meta", "meta-llama": "meta",
  mistral: "mistral", mistralai: "mistral",
  deepseek: "deepseek", qwen: "qwen", xiaomi: "xiaomi", tencent: "tencent.png",
  cohere: "cohere", perplexity: "perplexity",
  // moonshot / kimi: theme-split assets below (black K on light, light K on dark)
  zhipu: "zhipu", "z-ai": "zhipu", glm: "zhipu",
  amazon: "amazon", aws: "amazon", nova: "amazon",
  minimax: "minimax", nvidia: "nvidia", nemotron: "nvidia",
};
const MONO: Record<string, string> = {
  openai: "openai", xai: "xai", "x-ai": "xai", grok: "xai",
};

export function ProviderIcon({ brand, size = 17, className = "" }: { brand: string; size?: number; className?: string }) {
  const b = brand?.toLowerCase().trim().replace(/^~/, "");
  if (b === "space-bunny") {
    // Space Bunny is an anonymous OpenRouter model, so use its own model mark without
    // assigning it to a real provider.
    return (
      <span aria-hidden="true" className={`inline-flex shrink-0 items-center justify-center rounded-full ${className}`}
        style={{ width: size, height: size, background: "#7558d9", overflow: "hidden" }}>
        <svg width={size * 0.78} height={size * 0.78} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M7.1 11.1C5.7 6.7 6.1 2.4 8.3 2.4c2.1 0 2.7 4.1 2.9 7.1m5.7 1.6c1.4-4.4 1-8.7-1.2-8.7-2.1 0-2.7 4.1-2.9 7.1" stroke="white" strokeWidth="2.1" strokeLinecap="round" />
          <path d="M4.2 14.5c0-4 3.3-6.4 7.8-6.4s7.8 2.4 7.8 6.4-3.3 7-7.8 7-7.8-3-7.8-7Z" fill="white" />
          <circle cx="9.2" cy="14.2" r=".9" fill="#49318d" /><circle cx="14.8" cy="14.2" r=".9" fill="#49318d" />
          <path d="M11 16.2h2l-1 1.2-1-1.2Z" fill="#ef8b9f" />
        </svg>
      </span>
    );
  }
  // Kimi's mark uses a solid K — black on light, light on dark — so it needs both assets.
  if (b === "moonshot" || b === "moonshotai" || b === "kimi") {
    return (
      <span className={`inline-grid shrink-0 ${className}`} style={{ width: size, height: size }} aria-hidden>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/icons/color/moonshot.svg" alt="" width={size} height={size}
          className="fp-logo-light col-start-1 row-start-1" style={{ objectFit: "contain" }} />
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/icons/color/moonshot-dark.svg" alt="" width={size} height={size}
          className="fp-logo-dark col-start-1 row-start-1" style={{ objectFit: "contain" }} />
      </span>
    );
  }
  const color = COLOR[b];
  if (color) {
    // eslint-disable-next-line @next/next/no-img-element
    return (
      <img src={`/icons/color/${color.includes(".") ? color : `${color}.svg`}`} alt="" aria-hidden width={size} height={size}
        className={`inline-block shrink-0 ${className}`} style={{ objectFit: "contain" }} />
    );
  }
  const mono = MONO[b];
  if (mono) {
    const url = `url(/icons/${mono}.svg)`;
    return (
      <span
        aria-hidden
        className={`inline-block shrink-0 ${className}`}
        style={{
          width: size, height: size, color: "var(--text)", background: "currentColor",
          maskImage: url, WebkitMaskImage: url,
          maskSize: "contain", WebkitMaskSize: "contain",
          maskRepeat: "no-repeat", WebkitMaskRepeat: "no-repeat",
          maskPosition: "center", WebkitMaskPosition: "center",
        }}
      />
    );
  }
  // Unmapped lab (a stealth/cloaked model, or a new lab not yet added to COLOR/MONO above) — a
  // neutral initial badge, never a real competitor's logo. Misattributing an unknown model to
  // e.g. OpenAI's mark on a public leaderboard is actively misleading, not a harmless fallback.
  const initial = (brand || "?").trim().charAt(0).toUpperCase() || "?";
  return (
    <span
      aria-hidden
      className={`inline-flex items-center justify-center shrink-0 rounded-full ${className}`}
      style={{
        width: size, height: size, background: "var(--surface-2)", color: "var(--faint)",
        fontSize: size * 0.55, fontWeight: 700, lineHeight: 1, fontFamily: "var(--font-sans)",
      }}
    >
      {initial}
    </span>
  );
}
