"""Build Flexprice model metrics from publicly accessible model ranking portals.

No model calls are made here. The OpenRouter catalog and public monthly rankings feed,
Artificial Analysis, and Arena provide the inputs. A source failure stops the
refresh so the previous public snapshot remains in place. The paid Data API is not required.
"""
from __future__ import annotations

import json
import math
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = HERE / "web" / "lib" / "market-data.json"
FLEXPRICE_TASKS_PATH = HERE / "data" / "flexprice-tasks.json"
OPENROUTER_MODELS = "https://openrouter.ai/api/v1/models"
OPENROUTER_RANKINGS = "https://openrouter.ai/rankings"
OPENROUTER_RANKINGS_FEED = "https://openrouter.ai/api/frontend/v1/rankings/models?view=month"
AA_URL = "https://artificialanalysis.ai/leaderboards/models"
ARENA_URL = "https://arena.ai/leaderboard"
SOURCES = {
    "artificial_analysis": {"label": "Artificial Analysis", "url": AA_URL},
    "arena": {"label": "LMArena", "url": ARENA_URL},
    "openrouter": {"label": "OpenRouter", "url": "https://openrouter.ai/rankings"},
    "openrouter_catalog": {"label": "OpenRouter model catalog", "url": OPENROUTER_MODELS},
}
WEIGHTS = {"capability": 0.40, "preference": 0.35, "adoption": 0.25}
TASK_WEIGHTS = {"capability": 0.30, "preference": 0.25, "adoption": 0.20, "flexprice_tasks": 0.25}

FLEX_METRICS = {
    "intelligence": {"label": "Capability", "unit": "points", "higher_is_better": True},
    "preference": {"label": "User preference", "unit": "rating", "higher_is_better": True},
    "adoption": {"label": "Adoption", "unit": "/ 100", "higher_is_better": True},
    "overall": {"label": "Flexprice Index", "unit": "/ 100", "higher_is_better": True},
}


def build_methodology() -> dict:
    """Describe both Index formulas without changing the score calculation."""
    def formula(weights: dict[str, float]) -> str:
        labels = {"flexprice_tasks": "Flexprice tasks"}
        return " + ".join(f"{weight * 100:g}% {labels.get(name, name)}" for name, weight in weights.items())

    return {
        "weights": WEIGHTS,
        "task_weights": TASK_WEIGHTS,
        "weight_selection": "Use task_weights when a model has sources.flexprice_tasks; otherwise use weights.",
        "index_description": f"Models with Flexprice task results: {formula(TASK_WEIGHTS)}. Models without task results: {formula(WEIGHTS)}.",
        "normalization": "Capability uses the Artificial Analysis Intelligence Index when published, otherwise a catalog-feature estimate calibrated against benchmarked models with a 10-point text capability floor. Preference combines Arena ratings (70%) and developer request activity (30%) where Arena is available; otherwise it uses request activity. Adoption is log-scaled OpenRouter token volume. Models with no published usage receive zero for request activity and adoption.",
        "task_normalization": "The local Flexprice task composite is 0.35 × accuracy + 0.30 × extraction + 0.20 × convention + 0.15 × max(0, 100 − hallucination) − 0.20 × consistency, clamped to 0–100 and rounded to one decimal. With two or more matched models, composites are min-max normalized to 0–100; if all composites are equal, they normalize to 100. A single matched model keeps its composite score. The Index uses this normalized task score.",
        "metrics": FLEX_METRICS,
        "attribution": SOURCES,
        "caveat": "Flexprice Index combines public signals with local task results where available. It is not a standalone contract-extraction accuracy score and does not imply that every model has Flexprice task results.",
    }


def fetch_json(url: str, token: str | None = None) -> dict:
    headers = {"User-Agent": "FinePrint model-rankings/1.0", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.load(response)


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "FinePrint model-rankings/1.0"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read().decode("utf-8", errors="replace")


def normalize(raw: str) -> str:
    """Conservative model key normalization across provider and leaderboard naming."""
    value = raw.lower().split("/", 1)[-1]
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(r"[-_]20\d{6}\b", " ", value)
    value = re.sub(r"\b(?:xhigh|high|medium|low|free|text|harness|adaptive|default|fallback|effort)\b", " ", value)
    parts = [p for p in re.split(r"[-\s_]+", value) if p]
    value = "-".join(parts).strip("-")
    return re.sub(r"(?<=\d)-(?=\d)", ".", value)


def _flight_payload(html: str) -> str:
    chunks = re.findall(r'self\.__next_f\.push\(\[1,("(?:\\.|[^"\\])*")\]\)', html, re.DOTALL)
    return "\n".join(json.loads(chunk) for chunk in chunks)


def _balanced_object(text: str, at: int) -> dict | None:
    start = text.rfind("{", 0, at)
    while start >= 0:
        depth, quoted, escaped = 0, False, False
        for i in range(start, len(text)):
            c = text[i]
            if quoted:
                if escaped: escaped = False
                elif c == "\\": escaped = True
                elif c == '"': quoted = False
                continue
            if c == '"': quoted = True
            elif c == "{": depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try: return json.loads(text[start:i + 1])
                    except json.JSONDecodeError: break
        start = text.rfind("{", 0, start)
    return None


def parse_aa(html: str) -> dict[str, dict]:
    text, rows = _flight_payload(html), {}
    for match in re.finditer(r'"intelligenceIndex"\s*:', text):
        obj = _balanced_object(text, match.start())
        if not obj or not isinstance(obj.get("intelligenceIndex"), (int, float)) or obj["intelligenceIndex"] <= 0:
            continue
        slug = obj.get("slug") or obj.get("modelSlug")
        if not slug: continue
        key = normalize(str(slug))
        if obj.get("deprecated"): continue
        old = rows.get(key)
        if old is None or obj["intelligenceIndex"] > old["score"]:
            rows[key] = {"score": float(obj["intelligenceIndex"]), "label": obj.get("name") or obj.get("modelName")}
    if not rows:
        raise ValueError("Artificial Analysis page did not contain parseable Intelligence Index rows")
    return rows


def parse_arena(html: str) -> dict[str, dict]:
    text, rows = _flight_payload(html), {}
    excluded = ("-webdev", "-vision", "-search", "-document")
    for match in re.finditer(r'"modelKey"\s*:', text):
        obj = _balanced_object(text, match.start())
        if not obj or not isinstance(obj.get("rating"), (int, float)): continue
        key_raw = str(obj.get("modelKey") or "")
        if not key_raw or any(key_raw.lower().endswith(x) for x in excluded) or any(x in key_raw.lower() for x in ("harness", "codex")): continue
        if obj.get("pricePerImage") is not None or obj.get("pricePerSecond") is not None or obj.get("contextLength") is None: continue
        key = normalize(key_raw)
        if not key: continue
        old = rows.get(key)
        if old is None or obj["rating"] > old["score"]:
            rows[key] = {"score": float(obj["rating"]), "votes": obj.get("votes"), "label": obj.get("modelDisplayName")}
    if not rows:
        raise ValueError("Arena page did not contain parseable text/chat ratings")
    return rows


def parse_openrouter_rankings(html: str) -> tuple[list[dict], str]:
    """Read the public weekly rankings embedded in OpenRouter's server-rendered page.

    OpenRouter's separate Data API requires bearer authentication, but the published
    rankings page includes the same weekly ranking rows in its public hydration payload.
    Use the page data rather than inventing values or requiring an inference API key.
    """
    text, rows = _flight_payload(html), None
    for match in re.finditer(r'"queryKey"\s*:', text):
        at = text.rfind('"dehydratedAt"', 0, match.start())
        query = _balanced_object(text, at) if at >= 0 else None
        key = query.get("queryKey") if query else None
        if not (isinstance(key, list) and len(key) >= 3 and key[:2] == ["rankings", "models"] and (key[2] or {}).get("view") == "week"):
            continue
        data = (query.get("state") or {}).get("data")
        if isinstance(data, list):
            rows = data
            break
    if not rows:
        raise ValueError("OpenRouter public rankings page did not contain weekly model rows")

    usage, dates = [], []
    for row in rows:
        slug = row.get("model_permaslug")
        if not slug or slug == "other":
            continue
        total = int(row.get("total_prompt_tokens") or 0) + int(row.get("total_completion_tokens") or 0)
        if total <= 0:
            continue
        usage.append({"model_permaslug": slug, "total_tokens": total, "count": int(row.get("count") or 0)})
        if row.get("date"):
            dates.append(str(row["date"])[:10])
    if not usage:
        raise ValueError("OpenRouter public rankings page contained no usable weekly model totals")
    as_of = max(dates) + "T00:00:00Z" if dates else datetime.now(timezone.utc).isoformat()
    return usage, as_of


def parse_openrouter_feed(payload: dict) -> tuple[list[dict], str]:
    """Use all publicly listed model-day rows in the trailing monthly window."""
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise ValueError("OpenRouter rankings feed did not contain model rows")
    usage, dates = [], []
    for row in rows:
        slug = row.get("model_permaslug")
        if not slug or slug == "other":
            continue
        total = int(row.get("total_prompt_tokens") or 0) + int(row.get("total_completion_tokens") or 0)
        if total <= 0:
            continue
        usage.append({"model_permaslug": slug, "total_tokens": total, "count": int(row.get("count") or 0)})
        if row.get("date"):
            dates.append(str(row["date"])[:10])
    if not usage:
        raise ValueError("OpenRouter rankings feed contained no usable token totals")
    return usage, max(dates) + "T00:00:00Z" if dates else datetime.now(timezone.utc).isoformat()


def _minmax(values: list[float], log: bool = False) -> dict[float, float]:
    transformed = {v: math.log10(v + 1) if log else v for v in values}
    lo, hi = min(transformed.values()), max(transformed.values())
    return {v: (100.0 if hi == lo else round((t - lo) / (hi - lo) * 100, 1)) for v, t in transformed.items()}


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def flexprice_task_score(entry: dict) -> float:
    """Compute a 0–100 composite score from locally evaluated FinePrint task metrics."""
    accuracy = float(entry.get("accuracy", 0.0))
    extraction = float(entry.get("extraction", accuracy))
    convention = float(entry.get("convention", accuracy))
    halluc = float(entry.get("halluc", 0.0))
    consistency = float(entry.get("consistency", 0.0))
    raw = (
        0.35 * accuracy
        + 0.30 * extraction
        + 0.20 * convention
        + 0.15 * max(0.0, 100.0 - halluc)
        - 0.20 * consistency
    )
    return round(_clamp(raw), 1)


def load_flexprice_tasks(path: Path = FLEXPRICE_TASKS_PATH) -> dict[str, dict]:
    """Load local Flexprice task scores keyed by normalized model ID."""
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    entries = payload.get("models", payload) if isinstance(payload, dict) else {}
    if not isinstance(entries, dict):
        return {}
    rows: dict[str, dict] = {}
    for raw_key, entry in entries.items():
        if not isinstance(entry, dict) or "accuracy" not in entry:
            continue
        key = normalize(str(raw_key))
        if not key:
            continue
        score = flexprice_task_score(entry)
        old = rows.get(key)
        if old is None or score > old["score"]:
            rows[key] = {"score": score, "label": entry.get("label") or str(raw_key)}
    return rows



def catalog_capability(item: dict) -> float:
    """A fixed, reproducible feature envelope from public model-card fields."""
    params = set(item.get("supported_parameters") or [])
    inputs = set((item.get("architecture") or {}).get("input_modalities") or [])
    context = max(4096, int(item.get("context_length") or 4096))
    output = max(1024, int((item.get("top_provider") or {}).get("max_completion_tokens") or 1024))
    feature_points = (
        25 * min(math.log2(context / 4096) / 8, 1)
        + 15 * min(math.log2(output / 1024) / 7, 1)
        + 10 * ("image" in inputs)
        + 5 * ("file" in inputs)
        + 10 * ("tools" in params)
        + 10 * ("structured_outputs" in params)
        + 10 * bool({"reasoning", "reasoning_effort"} & params)
    )
    return _clamp(feature_points / 85 * 100)


def _capability_calibration(profiles: dict[str, float], aa: dict[str, dict], aa_norm: dict[float, float]):
    """Calibrate catalog-feature estimates to the observed benchmark scale."""
    points = [(profiles[key], aa_norm[record["score"]]) for key, record in aa.items() if key in profiles]
    if len(points) < 8:
        return lambda profile: profile
    mean_x = sum(x for x, _ in points) / len(points)
    mean_y = sum(y for _, y in points) / len(points)
    variance = sum((x - mean_x) ** 2 for x, _ in points)
    covariance = sum((x - mean_x) * (y - mean_y) for x, y in points)
    slope = covariance / (variance * 1.15) if variance else 0
    return lambda profile: _clamp(mean_y + slope * (profile - mean_x))


def build(catalog: list[dict], usage_data: list[dict], aa: dict[str, dict], arena: dict[str, dict], as_of: str,
          flexprice_tasks: dict[str, dict] | None = None) -> dict:
    usage: dict[str, int] = {}
    requests: dict[str, int] = {}
    usage_labels: dict[str, str] = {}
    for row in usage_data:
        slug = row.get("model_permaslug", "")
        if not slug or slug == "other": continue
        key = normalize(slug)
        usage[key] = usage.get(key, 0) + int(row.get("total_tokens") or 0)
        requests[key] = requests.get(key, 0) + int(row.get("count") or 0)
        usage_labels[key] = slug

    models: dict[str, dict] = {}
    catalog_items: dict[str, dict] = {}
    for item in catalog:
        model_id = item.get("canonical_slug") or item.get("id")
        if not model_id or ":" in model_id: continue
        arch = item.get("architecture") or {}
        inputs, outputs = arch.get("input_modalities") or [], arch.get("output_modalities") or []
        if inputs and ("text" not in inputs or "text" not in outputs): continue
        if outputs and any(modality != "text" for modality in outputs): continue
        key = normalize(model_id)
        catalog_items.setdefault(key, item)
        model = models.setdefault(key, {
            "id": model_id, "label": item.get("name") or model_id, "creator": model_id.split("/", 1)[0],
            "openrouter_ids": [], "sources": {},
        })
        if model_id not in model["openrouter_ids"]: model["openrouter_ids"].append(model_id)

    picker_models = models
    # Moving aliases and routers do not identify one underlying model and cannot
    # receive a stable model score. They remain available in the scan picker.
    models = {key: model for key, model in models.items()
              if not (model["id"].startswith("~") or model["id"].startswith("openrouter/")
                      or model["id"].endswith("-router") or model["id"] == "nvidia/switchyard")}

    # Ranking portals often publish a family slug or display name while the catalog uses a
    # dated deployment ID. Match those portal labels against catalog names as a fallback to the
    # exact normalized ID. Only accept aliases that identify one catalog model unambiguously.
    alias_targets: dict[str, set[str]] = {}
    for model_key, model in models.items():
        labels = [model["label"], *(item.get("name") for item in catalog if normalize(item.get("canonical_slug") or item.get("id") or "") == model_key)]
        for label in labels:
            if not label: continue
            label = str(label).split(":", 1)[-1].strip()
            alias_targets.setdefault(normalize(label), set()).add(model_key)
    aliases = {alias: next(iter(targets)) for alias, targets in alias_targets.items() if alias and len(targets) == 1}

    def map_records(records: dict[str, dict]) -> dict[str, dict]:
        mapped = {}
        for key, record in records.items():
            target = key if key in models else aliases.get(normalize(str(record.get("label") or "").split(":", 1)[-1].strip()))
            if target is None: continue
            previous = mapped.get(target)
            if previous is None or float(record["score"]) > float(previous["score"]):
                mapped[target] = record
        return mapped

    aa = map_records(aa)
    arena = map_records(arena)
    tasks = map_records(flexprice_tasks or {})

    aa_norm = _minmax([v["score"] for v in aa.values()]) if aa else {}
    arena_norm = _minmax([v["score"] for v in arena.values()]) if arena else {}
    tasks_norm = (
        _minmax([v["score"] for v in tasks.values()])
        if len(tasks) >= 2
        else {v["score"]: round(_clamp(float(v["score"])), 1) for v in tasks.values()}
    )
    # Log-scaling keeps heavy-tail usage from dominating the relative 0–100 range.
    usage_norm = _minmax([float(v) for v in usage.values()], log=True) if usage else {}
    usage_records = {k: {"score": v, "label": usage_labels[k]} for k, v in usage.items()}
    usage_records = map_records(usage_records)
    request_records = map_records({k: {"score": v, "label": usage_labels[k]} for k, v in requests.items() if v > 0})
    request_norm = _minmax([float(v) for v in requests.values() if v > 0], log=True) if any(requests.values()) else {}
    profiles = {key: catalog_capability(item) for key, item in catalog_items.items()}
    estimate_capability = _capability_calibration(profiles, aa, aa_norm)
    source_maps = {
        "artificial_analysis": (aa, aa_norm),
        "arena": (arena, arena_norm),
        "openrouter": (usage_records, usage_norm),
        "flexprice_tasks": (tasks, tasks_norm),
    }
    result_rows = []
    for key, model in models.items():
        for source, (records, norms) in source_maps.items():
            record = records.get(key)
            if record is None: continue
            raw = record["score"]
            score = norms[raw]
            model["sources"][source] = {"raw": raw, "normalized": score, **({"votes": record.get("votes")} if record.get("votes") is not None else {})}
        model["source_count"] = len(model["sources"])
        benchmark = model["sources"].get("artificial_analysis", {}).get("normalized")
        arena_rating = model["sources"].get("arena", {}).get("normalized")
        task_score = model["sources"].get("flexprice_tasks", {}).get("normalized")
        usage_record = usage_records.get(key)
        request_count = request_records.get(key, {}).get("score", 0)
        request_score = request_norm.get(float(request_count), 0.0)
        capability = benchmark if benchmark is not None else max(10.0, estimate_capability(profiles[key]))
        # Request count measures model selection; Arena contributes human comparisons
        # where published. Both are real activity, with no invented midpoint.
        preference = (0.7 * arena_rating + 0.3 * request_score) if arena_rating is not None else request_score
        adoption = model["sources"].get("openrouter", {}).get("normalized", 0.0)
        model["metric_basis"] = {
            "capability": "observed" if benchmark is not None else "derived",
            "preference": "observed" if arena_rating is not None else "derived",
            "adoption": "observed" if usage_record is not None else "derived",
        }
        model["metrics"] = {"capability": round(capability, 1), "preference": round(preference, 1), "adoption": round(adoption, 1)}
        model["ranked"] = True
        if task_score is not None:
            model["overall"] = round(
                model["metrics"]["capability"] * TASK_WEIGHTS["capability"]
                + model["metrics"]["preference"] * TASK_WEIGHTS["preference"]
                + model["metrics"]["adoption"] * TASK_WEIGHTS["adoption"]
                + round(task_score, 1) * TASK_WEIGHTS["flexprice_tasks"],
                1,
            )
        else:
            model["overall"] = round(sum(model["metrics"][name] * weight for name, weight in WEIGHTS.items()), 1)
        result_rows.append(model)
    result_rows.sort(key=lambda row: (-row["overall"], row["label"].lower()))
    rank = 0
    for row in result_rows:
        rank += 1
        row["rank"] = rank
    return {
        "schema_version": 4, "as_of": as_of, "window": "Public monthly model usage and current ranking signals",
        "methodology": build_methodology(),
        "sources": SOURCES, "n_models": len(result_rows), "n_ranked": sum(row["ranked"] for row in result_rows), "rows": result_rows,
        "catalog": sorted(({"id": m["id"], "label": m["label"], "creator": m["creator"], "openrouter_ids": m["openrouter_ids"]} for m in picker_models.values()), key=lambda m: m["label"].lower()),
    }


def sync(output: Path = DEFAULT_OUTPUT, offline: bool = False,
         fixture_path: Path | None = None, catalog_only: bool = False,
         catalog_path: Path | None = None, tasks_path: Path = FLEXPRICE_TASKS_PATH) -> dict:
    """Fetch sources and write JSON. --offline expects a fixture bundle for repeatable local review."""
    flexprice_tasks = load_flexprice_tasks(tasks_path)
    if offline:
        fixture = json.loads((fixture_path or HERE / "data" / "market-fixture.json").read_text())
        catalog = fixture["catalog"]
        if catalog_path:
            catalog_snapshot = json.loads(catalog_path.read_text())
            catalog = [{"id": item["id"], "canonical_slug": item["id"], "name": item["label"], "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]}} for item in catalog_snapshot["catalog"]]
        payload = build(catalog, fixture["usage"], fixture["artificial_analysis"], fixture["arena"], fixture["as_of"],
                        flexprice_tasks=flexprice_tasks)
        if catalog_path:
            payload["window"] = "Local preview fixture; full OpenRouter catalog refreshed separately"
            payload["preview_fixture"] = True
    else:
        catalog_payload = fetch_json(OPENROUTER_MODELS)
        if catalog_only:
            # Refreshing the scan model selector must not erase a good external ranking snapshot.
            try:
                existing = json.loads(output.read_text())
            except (OSError, json.JSONDecodeError):
                existing = {}
            payload = {"schema_version": existing.get("schema_version", 4), "as_of": existing.get("as_of") or datetime.now(timezone.utc).isoformat(),
                       "window": existing.get("window", "Ranking refresh pending"), "methodology": existing.get("methodology", {"weights": WEIGHTS}),
                       "sources": SOURCES, "n_models": existing.get("n_models", 0), "n_ranked": existing.get("n_ranked", 0), "rows": existing.get("rows", []), "source_errors": existing.get("source_errors", {}),
                       "catalog": catalog_for_playground(catalog_payload.get("data", []))}
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
            return payload
        failures = {}
        try: aa = parse_aa(fetch_text(AA_URL))
        except (OSError, ValueError, urllib.error.URLError) as exc: aa = {}; failures["artificial_analysis"] = str(exc)
        try: arena = parse_arena(fetch_text(ARENA_URL))
        except (OSError, ValueError, urllib.error.URLError) as exc: arena = {}; failures["arena"] = str(exc)
        try:
            usage_data, as_of = parse_openrouter_feed(fetch_json(OPENROUTER_RANKINGS_FEED))
        except (OSError, ValueError, urllib.error.URLError) as feed_exc:
            try:
                usage_data, as_of = parse_openrouter_rankings(fetch_text(OPENROUTER_RANKINGS))
                failures["openrouter_feed"] = f"Monthly feed unavailable; using public page: {feed_exc}"
            except (OSError, ValueError, urllib.error.URLError) as page_exc:
                usage_data, as_of = [], datetime.now(timezone.utc).isoformat()
                failures["openrouter"] = f"Feed: {feed_exc}; page: {page_exc}"
        if failures or len(usage_data) < 100 or len(aa) < 40 or len(arena) < 30:
            raise RuntimeError(f"Ranking inputs are incomplete; keeping the previous published snapshot. Coverage: OpenRouter {len(usage_data)}, Artificial Analysis {len(aa)}, Arena {len(arena)}. Errors: {failures}")
        payload = build(catalog_payload.get("data", []), usage_data, aa, arena, as_of,
                        flexprice_tasks=flexprice_tasks)
        payload["source_errors"] = failures
        payload["openrouter_usage_coverage"] = len(usage_data)
        payload["window"] = "OpenRouter public monthly usage and current public model signals"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return payload


def catalog_for_playground(catalog: list[dict]) -> list[dict]:
    """Reduce OpenRouter catalog entries to chat models the document scan can use."""
    out = []
    excluded = ("whisper", "tts", "embed", "moderation", "rerank", "dall-e", "sora", "video", "audio", "ocr", "image", "translation", "-mt2", "nllb", "madlad")
    for item in catalog:
        model_id = item.get("canonical_slug") or item.get("id")
        if not model_id or ":" in model_id: continue
        arch = item.get("architecture") or {}
        inputs, outputs = arch.get("input_modalities") or [], arch.get("output_modalities") or []
        if inputs and "text" not in inputs: continue
        if outputs and "text" not in outputs: continue
        if outputs and any(modality != "text" for modality in outputs): continue
        if any(token in model_id.lower() for token in excluded): continue
        out.append({"id": model_id, "label": item.get("name") or model_id,
                    "creator": model_id.split("/", 1)[0], "openrouter_ids": [model_id]})
    return sorted(out, key=lambda row: row["label"].lower())


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Refresh FinePrint's third-party model rankings and OpenRouter catalog")
    parser.add_argument("--offline", action="store_true", help="build from the checked-in deterministic fixture")
    parser.add_argument("--fixture", type=Path, help="use a local JSON source snapshot")
    parser.add_argument("--catalog-only", action="store_true", help="refresh the OpenRouter scan model catalog without requiring ranking API auth")
    parser.add_argument("--catalog", type=Path, help="use the catalog from an existing market data JSON snapshot (with --offline)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = sync(args.output, offline=args.offline, fixture_path=args.fixture, catalog_only=args.catalog_only, catalog_path=args.catalog)
    print(f"Wrote {args.output}: {result['n_models']} models, {result.get('n_ranked', 0)} ranked; catalog {len(result['catalog'])}; as of {result['as_of']}")
    if result.get("source_errors"): print(f"Source errors: {result['source_errors']}")
