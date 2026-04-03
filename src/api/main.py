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
import time
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field

from run_pipeline import run_pipeline
from src.forecasting.forecast import forecast_revenue
from src.ingestion.ingest import load_or_create_raw
from src.processing.transform import transform_data
from src.utils.helpers import build_paths, load_config
from src.utils.logger import get_logger

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
    allow_origins=_config["api"].get("cors_origins", ["*"]),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
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
    response_model=DecisionResponse,
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
    response_model=DecisionResponse,
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
        from src.anomaly.detect import detect_anomalies
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
