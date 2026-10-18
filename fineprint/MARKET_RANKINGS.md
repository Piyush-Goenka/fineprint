# External model rankings and catalog refresh

The PDF scan stays available as a live extraction demo. Flexprice Model Intelligence presents capability, preference, adoption, and a Flexprice Index for every distinct OpenRouter chat model. Moving aliases and routers remain in the playground picker; their underlying model can change, so they do not have a stable ranking entry.

## Local setup

Refresh the playground's model list or all ranking metrics from public pages; no OpenRouter API key or model inference is used:

```sh
python3 -m fineprint.market_data --catalog-only
```

Build a deterministic UI preview from the checked-in fixture:

```sh
python3 -m fineprint.market_data --offline
cd fineprint/web && npm run dev
```

For a complete local catalog with preview-only ranking values, refresh the catalog then join the local fixture:

```sh
python3 -m fineprint.market_data --catalog-only
python3 -m fineprint.market_data --offline --catalog fineprint/web/lib/market-data.json
```

Fetch the public ranking pages and catalog, then update `fineprint/web/lib/market-data.json`:

```sh
python3 -m fineprint.market_data
```

The catalog and monthly ranking feed are public. OpenRouter's separate documented Data API requires authentication, so the refresh reads the public rankings feed used by its website. The website feed is undocumented and may change. If source coverage drops below the minimum expected size or any ranking source fails, the refresh stops and keeps the prior snapshot. The refresh does not call models or require `OPENROUTER_API_KEY`. New catalog models immediately appear in the leaderboard and scan picker with scores from the fixed formula.

## Schedule

The GitHub Actions ranking workflow runs hourly, updates this snapshot, and dispatches the existing site deploy workflow only when the data changes. It needs no provider or model-inference secret. Do not invoke `fineprint.watch` or `fineprint.eval` for catalog/ranking updates; they are retired from automatic ranking refreshes. The PDF scan may still use a model call when a user explicitly submits a document.

## Data interpretation

The Flexprice Index uses two formulas. Models with a matched local Flexprice task result use **30% capability + 25% preference + 20% adoption + 25% Flexprice tasks**. Models without a task result use the public-only fallback: **40% capability + 35% preference + 25% adoption**. Capability uses Artificial Analysis when available and otherwise a calibrated model-card feature score. Preference uses OpenRouter request volume and also Arena ratings where available. Adoption uses OpenRouter token volume. Activity is log-scaled; absent usage is zero.

Local task results are read from `fineprint/data/flexprice-tasks.json`. The task composite is `0.35 × accuracy + 0.30 × extraction + 0.20 × convention + 0.15 × max(0, 100 − hallucination) − 0.20 × consistency`, clamped to 0–100 and rounded to one decimal. When at least two models have matched task results, their composites are min-max normalized to 0–100; equal composites normalize to 100. A single matched model keeps its composite. The Index uses this normalized value, not the raw composite. The JSON methodology records both weight sets and the selection rule; each model's `sources.flexprice_tasks` indicates whether task weights apply.

The Index is directional and is not a standalone measure of contract-extraction accuracy. Public ranking refreshes read saved task results without running evaluations. Local fixture metrics are deterministic preview data, not a live source refresh.
