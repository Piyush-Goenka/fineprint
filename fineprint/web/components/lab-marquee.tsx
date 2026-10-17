"use client";

import { ProviderIcon } from "@/components/provider-icon";
import { marketData } from "@/lib/market-data";

// Major providers represented across the model catalog.
const LABS = [
  "openai", "google", "anthropic", "xai", "meta", "mistral",
  "deepseek", "qwen", "moonshot", "zhipu", "amazon", "cohere",
  "perplexity", "minimax", "nvidia",
] as const;

const LABELS: Record<string, string> = {
  openai: "OpenAI", google: "Google", anthropic: "Anthropic", xai: "xAI",
  meta: "Meta", mistral: "Mistral", deepseek: "DeepSeek", qwen: "Qwen",
  moonshot: "Kimi", zhipu: "Zhipu", amazon: "Amazon", cohere: "Cohere",
  perplexity: "Perplexity", minimax: "MiniMax", nvidia: "NVIDIA",
};

export function LabMarquee() {
  const sourceLabs = [...new Set(marketData.catalog.map((m) => m.creator))];
  const row = sourceLabs.length ? [...sourceLabs, ...sourceLabs] : [...LABS, ...LABS];
  return (
    <div className="fp-marquee" aria-label="Model providers">
      <div className="fp-marquee-track">
        {row.map((brand, i) => (
          <span key={`${brand}-${i}`} className="fp-marquee-item">
            <ProviderIcon brand={brand} size={30} />
            <span className="text-[14.5px] text-muted font-medium tracking-[-.01em]">
              {LABELS[brand] ?? brand}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}
