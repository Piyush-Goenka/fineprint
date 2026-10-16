import raw from "./market-data.json";

export type SourceKey = "artificial_analysis" | "arena" | "openrouter" | "openrouter_catalog";
export type ExternalModel = {
  id: string;
  label: string;
  creator: string;
  openrouter_ids: string[];
  rank?: number;
  overall?: number | null;
  source_count?: number;
  ranked?: boolean;
  metrics?: { capability?: number | null; preference?: number | null; adoption?: number | null };
  metric_basis?: { capability?: "observed" | "derived"; preference?: "observed" | "derived"; adoption?: "observed" | "derived" };
  sources: Partial<Record<SourceKey, { raw: number; normalized: number; votes?: number }>>;
};
export type OpenRouterModel = { id: string; label: string; creator: string; openrouter_ids: string[] };
export type MarketData = {
  schema_version: number;
  as_of: string;
  window: string;
  n_models: number;
  n_ranked: number;
  rows: ExternalModel[];
  catalog: OpenRouterModel[];
  sources: Record<SourceKey, { label: string; url: string }>;
  source_errors?: Partial<Record<SourceKey, string>>;
  openrouter_usage_coverage?: number;
  preview_fixture?: boolean;
  methodology: { weights: Record<string, number>; normalization?: string; caveat?: string };
};

export const marketData = raw as MarketData;

// Keep server rendering and browser hydration independent of the user's locale and time zone.
export const marketDataUpdatedDate = new Date(marketData.as_of).toLocaleDateString("en-US", {
  year: "numeric",
  month: "short",
  day: "numeric",
  timeZone: "UTC",
});
