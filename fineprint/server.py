"""FinePrint's live PDF extraction API and retired benchmark endpoints.

The /extract and /lead routes power the playground. Public rankings are refreshed from
published sources by ``fineprint.market_data``; this service never scores models for them.
"""
import base64
import json
import os
import re
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from fineprint import config, leads, playground, store
from fineprint.config import PLAYGROUND_MODELS, SAMPLE_DIR, SITE_ORIGINS, all_models
from fineprint.ratelimit import Limiter

app = FastAPI(title="FinePrint", docs_url="/docs", redoc_url=None)

app.add_middleware(CORSMiddleware, allow_origins=SITE_ORIGINS,
                   allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"])


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    """Answer a crash in the same shape as a handled error — and WITH the CORS header.

    Starlette's stack is ServerErrorMiddleware -> CORSMiddleware -> router, so an uncaught
    exception is turned into a 500 by the OUTERMOST middleware and never passes back through the
    CORS wrapper. The browser then blocks the response and ``fetch`` rejects with a bare
    "Failed to fetch": the real status is invisible to the client, and every backend crash looks
    identical from the outside. (An OpenRouter 402 for exhausted credits hid behind this for a
    day.) Setting the header here restores the status to the caller. The detail stays generic on
    purpose — this endpoint is public; the traceback goes to the logs, where it belongs, because
    ServerErrorMiddleware still re-raises after we answer.
    """
    origin = request.headers.get("origin", "")
    headers = {"access-control-allow-origin": origin, "vary": "Origin"} if origin in SITE_ORIGINS else {}
    return JSONResponse({"detail": "the FinePrint service hit an internal error — please retry"},
                        status_code=500, headers=headers)
_limiter = Limiter(max_hits=int(os.environ.get("FINEPRINT_PLAYGROUND_RPM", "12")), window_s=60)
# The upload flow is the only public endpoint that spends money per call — live Datalab OCR plus a
# model call. The general per-minute limit is sized for the cheap sample path; at 12/min one IP
# could drive hundreds of paid runs an hour. Uploads get their own, far smaller hourly budget.
_upload_limiter = Limiter(max_hits=int(os.environ.get("FINEPRINT_UPLOADS_PER_HOUR", "3")), window_s=3600)

@app.get("/")            # /healthz is intercepted by Google's front-end on Cloud Run, so alias it.
@app.get("/status")
@app.get("/healthz")
def healthz() -> dict:
    n = None
    if Path(config.WEB_DATA).exists():
        n = json.loads(Path(config.WEB_DATA).read_text()).get("n_models")
    return {"ok": True, "catalog_models": len(config.all_models()), "published_models": n,
            "bucket": store.BUCKET or None}


@app.post("/eval")
def eval_model() -> None:
    raise HTTPException(410, "Per-model benchmark evaluations have been retired. Public rankings refresh from published model data.")


@app.post("/watch")
def watch_poll() -> None:
    raise HTTPException(410, "The paid benchmark watcher has been retired. Use the public rankings refresh workflow.")


# ── playground: /lead + /extract ───────────────────────────────────────────
def _client_id(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # Rightmost entry is appended by our trusted last hop (proxy/load balancer); every
        # entry to its left is client-supplied and can be spoofed to mint a fresh XFF (and
        # thus a fresh rate-limit bucket) on every request, defeating the cap.
        return xff.split(",")[-1].strip()
    return request.client.host if request.client else "anon"


def _resolve_model(model_id: str) -> dict:
    m = next((x for x in all_models() if x["id"] == model_id or x.get("openrouter_id") == model_id), None)
    if not m:
        # The playground picker uses full IDs from the OpenRouter catalog. Resolve them only
        # for live extraction; this path never evaluates, scores, or publishes a model.
        from fineprint.eval import resolve
        try:
            m = resolve(model_id)
        except SystemExit:
            raise HTTPException(400, f"unknown model {model_id}")
    return m


_SAMPLE_ID_RE = re.compile(r"^[a-z0-9_-]+$")


def _sample_catalog() -> list[dict]:
    """Sample metadata (id/title/type/source). On the deployed service this ships WITH the
    samples as SAMPLE_DIR/catalog.json (synced from GCS at boot) — the site's web/ dir is not
    in the container image, so we can't read it there. Locally it falls back to the site catalog."""
    for path in (SAMPLE_DIR / "catalog.json", config.HERE / "web" / "lib" / "playground-samples.json"):
        if path.exists():
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                continue
    return []


def _known_sample_ids() -> set[str]:
    """Allowlist of playground sample ids, sourced from the sample catalog."""
    return {s["id"] for s in _sample_catalog()}


def _load_sample_result(sample_id: str, model_id: str) -> dict:
    """Precomputed default extraction (instant) or live-run the model over cached sample OCR."""
    import pickle

    # sample_id comes straight from the request body — validate against an allowlist BEFORE
    # it ever touches a path or pickle.loads(), or a crafted id (e.g. "../secret") could read
    # arbitrary files / deserialize arbitrary pickles off disk.
    if not sample_id or not _SAMPLE_ID_RE.match(sample_id) or sample_id not in _known_sample_ids():
        raise HTTPException(404, f"unknown sample {sample_id!r}")
    base = SAMPLE_DIR / sample_id
    meta_path, doc_path, pages_path = base / "meta.json", base / "doc.pkl", base / "pages.json"
    if not meta_path.exists() or not doc_path.exists() or not pages_path.exists():
        # listed in the public sample catalog (playground-samples.json) but not (yet) prepped
        # on this deployment — a missing-data problem, not a client error.
        raise HTTPException(503, "sample not available")
    default_path = base / "result.json"
    if model_id == json.loads(meta_path.read_text())["default_model"] and default_path.exists():
        return json.loads(default_path.read_text())
    doc = pickle.loads(doc_path.read_bytes())
    pages = json.loads(pages_path.read_text())               # precomputed page images
    res = playground.extract_result(doc, _resolve_model(model_id))
    res["pages"] = pages
    return res


@app.get("/samples")
def list_samples(request: Request) -> dict:
    """The samples that are actually prepped on THIS deployment (their page renders exist). The
    site renders a chip only for these, so it never shows a dead/placeholder sample button. The
    catalog (title/type/source) comes from the site's playground-samples.json."""
    if not _limiter.allow(_client_id(request), time.time()):
        raise HTTPException(429, "rate limit — try again shortly")
    avail = [c for c in _sample_catalog() if (SAMPLE_DIR / c["id"] / "pages.json").exists()]
    return {"samples": avail}


@app.get("/models")
def list_playground_models(request: Request) -> dict:
    """Live text-in/text-out OpenRouter catalog for the scan picker; no ranking or eval scores."""
    from fineprint.market_data import catalog_for_playground, fetch_json, OPENROUTER_MODELS
    try:
        payload = fetch_json(OPENROUTER_MODELS)
    except Exception as exc:
        raise HTTPException(503, f"OpenRouter model catalog unavailable: {type(exc).__name__}")
    return {"models": catalog_for_playground(payload.get("data", [])), "as_of": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


@app.get("/sample/{sample_id}/pages")
def sample_pages(sample_id: str, request: Request) -> dict:
    """Rendered page images for a prepped sample — lets the site show the contract on the left
    the instant it's picked, before (and independent of) any model run. No OCR, no model, no
    gate: just the precomputed, public page renders. Same allowlist guard as /extract."""
    if not _limiter.allow(_client_id(request), time.time()):
        raise HTTPException(429, "rate limit — try again shortly")
    if not sample_id or not _SAMPLE_ID_RE.match(sample_id) or sample_id not in _known_sample_ids():
        raise HTTPException(404, f"unknown sample {sample_id!r}")
    pages_path = SAMPLE_DIR / sample_id / "pages.json"
    if not pages_path.exists():                       # in the catalog but not prepped on this deploy
        raise HTTPException(503, "sample not available")
    return {"pages": json.loads(pages_path.read_text())}


def _extract_upload(pdf: bytes, resolved_model: dict) -> dict:
    """Blocking upload pipeline (live Datalab OCR + model + page render). MUST run in a worker
    thread: the Datalab SDK calls asyncio.run() internally, which raises inside the async request
    handler's already-running event loop. The temp PDF is written and unlinked here so it never
    outlives the request (the upload is never persisted)."""
    import tempfile
    from pipeline.extractor import extract_document
    from pipeline.render import render_pages

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        tf.write(pdf)
        tmp = tf.name
    try:
        doc = extract_document(tmp, cache=False)         # live Datalab OCR — never cached to disk
        res = playground.extract_result(doc, resolved_model)
        res["pages"] = [{"image": "data:image/png;base64," + base64.b64encode(p["png"]).decode(),
                         "w": p["w"], "h": p["h"]} for p in render_pages(pdf)]
        return res
    finally:
        os.unlink(tmp)                                  # never persist the upload


@app.post("/lead")
async def lead(request: Request) -> dict:
    if not _limiter.allow(_client_id(request), time.time()):
        raise HTTPException(429, "rate limit — try again shortly")
    body = await request.json()
    try:
        tok = leads.record_lead(email=body.get("email"), name=body.get("name"),
                                context=body.get("context") or {})
    except ValueError as e:
        raise HTTPException(422, str(e) or "invalid lead")
    return {"session_token": tok}


@app.post("/extract")
async def extract(request: Request, file: UploadFile = File(None),
                  model: str = Form(None), session_token: str = Form(None)) -> dict:
    if not _limiter.allow(_client_id(request), time.time()):
        raise HTTPException(429, "rate limit — try again shortly")
    if file is None:                                   # JSON sample path
        try:
            body = await request.json()
        except (json.JSONDecodeError, ValueError):
            raise HTTPException(422, "invalid JSON body")
        sample_id = body.get("sample_id")
        if not sample_id:
            raise HTTPException(422, "sample_id is required")
        # off the event loop: a non-default model triggers a blocking provider call
        return await run_in_threadpool(_load_sample_result, sample_id, body.get("model", PLAYGROUND_MODELS[0]))
    # upload path — gated
    if not leads.valid_session_token(session_token or ""):
        raise HTTPException(401, "enter your work email to run your own contract")
    # Checked after the token gate (a rejected caller must not burn someone's quota) and before the
    # file is read or any OCR is billed.
    if not _upload_limiter.allow(_client_id(request), time.time()):
        raise HTTPException(429, "upload limit reached — try again in an hour")
    pdf = await file.read()
    if len(pdf) > 10 * 1024 * 1024:
        raise HTTPException(413, "PDF too large (max 10 MB)")
    resolved_model = _resolve_model(model or PLAYGROUND_MODELS[0])   # before any paid OCR spend
    return await run_in_threadpool(_extract_upload, pdf, resolved_model)
