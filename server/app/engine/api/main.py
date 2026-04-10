"""FastAPI application — AI Decision Intelligence REST API v2.

Endpoints:
  GET /health          System health and uptime
  GET /analyze         Full multi-metric decision pipeline
  GET /forecast        Revenue forecast only (7-day)
  GET /decision        Alias for /analyze (executive-facing)
  GET /metrics         Returns the multi-metric scorecard only
"""
from __future__ import annotations

import os
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import Depends, FastAPI, File, HTTPException, Request, Security, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field

from run_pipeline import run_pipeline
from app.engine.forecasting.forecast import forecast_revenue
from app.engine.ingestion.ingest import load_or_create_raw
from app.engine.processing.transform import transform_data
from app.engine.utils.helpers import build_paths, load_config
from app.engine.utils.logger import get_logger

logger = get_logger(__name__)
_config = load_config()
_startup_time = time.time()


# ── Pydantic response models ─────────────────────────────────────────────────

class MetricSummary(BaseModel):
    metric:           str
    label:            str
    anomaly_detected: bool
    severity:         str
    change:           str
    change_pct:       float
    anomaly_count:    int
    anomaly_dates:    list[str]
    recent_value:     float
    prior_value:      float
    if_score_worst:   float


class RootCauseItem(BaseModel):
    driver:           str
    dimension:        str
    group_value:      str
    delta:            float
    contribution_pct: float


class RecommendationItem(BaseModel):
    action:          str
    priority:        str = Field(..., pattern="^(HIGH|MEDIUM|LOW)$")
    expected_impact: str
    timeline:        str
    owner:           str
    confidence:      float


class DecisionResponse(BaseModel):
    metric:           str
    anomaly_detected: bool
    severity:         str
    change:           str
    change_pct:       float
    anomaly_count:    int
    anomaly_dates:    list[str]
    per_metric:       dict[str, Any]
    root_cause:       list[Any]
    prediction:       str
    forecast_pct_change:       float
    forecast_values:           list[float]
    forecast_confidence_lower: list[float]
    forecast_confidence_upper: list[float]
    model:            str
    per_metric_forecast: dict[str, Any]
    recommendation:   list[Any]
    confidence:       float
    explanation:      str
    llm_powered:      bool
    processing_time_ms: float
    timestamp:        str
    pipeline_version: str


class ForecastResponse(BaseModel):
    prediction:          str
    forecast_pct_change: float
    forecast_values:     list[float]
    confidence_lower:    list[float]
    confidence_upper:    list[float]
    model:               str
    periods:             int
    timestamp:           str


class HealthResponse(BaseModel):
    status:         str
    version:        str
    timestamp:      str
    uptime_seconds: float


class ErrorResponse(BaseModel):
    detail:     str
    error_type: str
    timestamp:  str


class ChatRequest(BaseModel):
    question: str
    context: dict = {}  # pipeline output context
    api_key: Optional[str] = None  # user's own Anthropic key (optional)


class ChatResponse(BaseModel):
    answer: str
    llm_powered: bool
    timestamp: str


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=_config["api"]["title"],
    version=_config["api"]["version"],
    description=_config["api"].get("description", "AI Decision Intelligence API"),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "System",   "description": "Health and diagnostics"},
        {"name": "Pipeline", "description": "AI decision intelligence endpoints"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
_VALID_API_KEY  = os.getenv("API_KEY")


def _require_api_key(api_key: Optional[str] = Security(_API_KEY_HEADER)) -> None:
    if not _config["api"].get("enable_auth") or not _VALID_API_KEY:
        return
    if api_key != _VALID_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key. Pass X-API-Key header.",
        )


@app.middleware("http")
async def _request_logger(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    logger.info(
        "http_request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
        },
    )
    return response


@app.exception_handler(Exception)
async def _global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", extra={"path": request.url.path, "error": str(exc)}, exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="An internal error occurred. Check server logs for details.",
            error_type=type(exc).__name__,
            timestamp=datetime.now(timezone.utc).isoformat(),
        ).model_dump(),
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"], summary="System health check")
def health() -> dict[str, Any]:
    """Returns API status, version, and uptime."""
    return {
        "status":         "healthy",
        "version":        _config["api"]["version"],
        "timestamp":      datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - _startup_time, 1),
    }


@app.get(
    "/analyze",
    tags=["Pipeline"],
    summary="Run full multi-metric AI decision pipeline",
    dependencies=[Depends(_require_api_key)],
)
def analyze() -> dict[str, Any]:
    """Execute all 7 pipeline stages and return the complete decision intelligence output.

    Stages: Ingest -> Transform -> Anomaly Detection (multi-metric) ->
    Root Cause -> Forecast -> Recommendations -> LLM Explanation
    """
    try:
        return run_pipeline()
    except Exception as exc:
        logger.exception("Pipeline execution failed")
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {exc}") from exc


@app.get(
    "/forecast",
    response_model=ForecastResponse,
    tags=["Pipeline"],
    summary="7-day revenue forecast with confidence intervals",
)
def forecast() -> dict[str, Any]:
    """Run only the forecasting stage. Returns a 7-day revenue projection."""
    try:
        cfg     = load_config()
        paths   = build_paths(cfg)
        raw_df  = load_or_create_raw(paths.raw)
        proc_df = transform_data(raw_df, paths.processed)
        result  = forecast_revenue(proc_df, periods=cfg["forecast"]["periods"])
        result["periods"]   = cfg["forecast"]["periods"]
        result["timestamp"] = datetime.now(timezone.utc).isoformat()
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get(
    "/decision",
    tags=["Pipeline"],
    summary="Executive decision brief (alias for /analyze)",
    dependencies=[Depends(_require_api_key)],
)
def decision() -> dict[str, Any]:
    """Alias for /analyze — named /decision to reflect executive-facing intent."""
    return analyze()


@app.get(
    "/metrics",
    tags=["Pipeline"],
    summary="Multi-metric scorecard only",
)
def metrics() -> dict[str, Any]:
    """Returns the per-metric anomaly scorecard without running the full pipeline."""
    try:
        from app.engine.anomaly.detect import detect_anomalies
        cfg     = load_config()
        paths   = build_paths(cfg)
        raw_df  = load_or_create_raw(paths.raw)
        proc_df = transform_data(raw_df, paths.processed)
        _, summary = detect_anomalies(
            proc_df,
            contamination=cfg["anomaly"]["contamination"],
            lookback=cfg["data"].get("lookback_days", 14),
        )
        return {
            "per_metric":      summary.get("per_metric", {}),
            "overall_severity": summary["severity"],
            "anomaly_detected": summary["anomaly_detected"],
            "timestamp":        datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


_ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@app.post(
    "/upload",
    tags=["Pipeline"],
    summary="Upload CSV or Excel file and run full AI decision pipeline",
)
async def upload_and_analyze(file: UploadFile = File(...)) -> dict[str, Any]:
    """Accept a CSV or Excel file upload, run all 7 pipeline stages, return decision intelligence output.

    Supported formats: .csv, .xlsx, .xls (max 50 MB).
    The web app POSTs the user's file here; the backend runs the full ML pipeline
    and returns the structured JSON result for dashboard rendering.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = Path(file.filename).suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f'Unsupported file format "{ext}". Please upload a CSV (.csv) or Excel (.xlsx / .xls) file.',
        )

    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File is too large ({len(content) // (1024*1024)} MB). Maximum allowed size is 50 MB.",
        )
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    tmp_path: str | None = None
    try:
        # Write to a temp file preserving the original extension so ingest.py
        # can detect whether to use read_csv or read_excel.
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        result = run_pipeline(source_csv=Path(tmp_path))
        return result

    except HTTPException:
        raise
    except Exception as exc:
        # NOTE: "filename" is a reserved key in Python LogRecord — use "upload_filename" instead
        logger.exception("Upload pipeline failed", extra={"upload_filename": file.filename})
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {exc}") from exc
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.post("/chat", response_model=ChatResponse, tags=["Pipeline"], summary="AI chat about uploaded dataset")
async def chat(req: ChatRequest) -> dict:
    """Answer questions about the analyzed dataset using Claude."""
    from app.engine.llm.chat import answer_question
    answer, llm_powered = answer_question(req.question, req.context, req.api_key)
    return {"answer": answer, "llm_powered": llm_powered, "timestamp": datetime.now(timezone.utc).isoformat()}


@app.delete("/session", tags=["System"], summary="Delete all session data")
async def delete_session() -> dict:
    """Hard-delete all uploaded raw data, processed outputs, and cached AI context."""
    deleted = []
    for p in ["data/raw/source.csv", "data/processed/processed.csv"]:
        fp = Path(p)
        if fp.exists():
            fp.unlink()
            deleted.append(str(p))
    outputs = Path("outputs")
    if outputs.exists():
        shutil.rmtree(outputs)
        outputs.mkdir(exist_ok=True)
        deleted.append("outputs/")
    return {"deleted": deleted, "status": "complete", "timestamp": datetime.now(timezone.utc).isoformat()}
