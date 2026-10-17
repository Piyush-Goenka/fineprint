# Model catalog and ranking automation

The hourly refresh is `.github/workflows/market-rankings.yml`. GitHub Actions runs it from `main` at minute 17 of each hour. It reads the public model catalog, OpenRouter's public monthly rankings feed, Artificial Analysis, and Arena, then updates `web/lib/market-data.json`. A push to `main` triggers the existing production website deployment. A manual run on another branch can inspect or test the refresh but cannot publish the snapshot.

The workflow compares stable model IDs with the previous snapshot and sends a Slack message when a new ranked model appears. A manual `test_slack` run sends a delivery test, even if there is no new model. Configure the `SLACK_WEBHOOK_URL` repository secret before merging. If delivery fails, the job fails before committing the snapshot so the next run retries the same new-model announcement. The webhook should point to the desired Slack channel. Once configured, run the workflow manually with `test_slack=true` and verify that the message appears in the channel.

The refresh requires no model-provider API key and makes no inference calls. OpenRouter's catalog and website rankings feed are public; its authenticated Data API is not used. The undocumented website feed can change, so the refresh checks source coverage and keeps the last good snapshot if a source fails. Every distinct model receives capability, preference, adoption, and an Index from the fixed scoring formula. Moving aliases and routers remain in the playground picker.

The PDF playground's `/extract` endpoint remains separate: it calls a model only when a user submits a scan. The retired `/eval` and `/watch` server routes reject requests; the legacy runner files remain only as code history and for resolving model metadata needed by the scan.

Run one refresh locally:

```sh
python3 -m fineprint.market_data
```

Build a deterministic UI fixture:

```sh
python3 -m fineprint.market_data --offline
```
