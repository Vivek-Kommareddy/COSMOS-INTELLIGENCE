"""Cosmos Intelligence Pipeline Orchestrator — runs all 7 stages and produces structured output + reports.

Usage:
    python run_pipeline.py                    # run + rich CLI output
    python run_pipeline.py --pretty           # also pretty-print JSON to stdout
    python run_pipeline.py --html             # save HTML executive brief
    python run_pipeline.py --pretty --html    # both
    python run_pipeline.py --json-only        # suppress CLI report, output JSON only
"""
from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.engine.anomaly.detect import detect_anomalies
from app.engine.forecasting.forecast import forecast_revenue
from app.engine.ingestion.ingest import load_or_create_raw
from app.engine.llm.explain import build_explanation
from app.engine.processing.transform import transform_data
from app.engine.recommendation.recommend import generate_recommendations
from app.engine.root_cause.analyze import analyze_root_cause
from app.engine.utils.helpers import build_paths, load_config
from app.engine.utils.logger import get_logger, log_stage

logger = get_logger(__name__)

_ROOT = Path(__file__).resolve().parent


def _sanitize(obj: Any) -> Any:
    """Recursively convert the pipeline result to JSON-safe Python primitives.

    Handles:
    - numpy scalars (int64, float64, bool_) → int / float / bool
    - NaN and ±Inf → None  (JSON has no NaN/Inf)
    - pandas Timestamp → ISO string
    - dict / list → recursed
    """
    import numpy as np  # local import to avoid top-level cost
    import pandas as pd

    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        v = float(obj)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, np.ndarray):
        return _sanitize(obj.tolist())
    return obj


def run_pipeline(config_path: Optional[str] = None, source_csv: Optional[Path] = None) -> dict[str, Any]:
    """Execute the full AI Decision Intelligence pipeline.

    Stages:
      1. Ingest      — load or generate enterprise dataset
      2. Transform   — clean, validate, derive metrics
      3. Detect      — multi-metric anomaly detection
      4. Analyze     — dimensional root-cause attribution
      5. Forecast    — multi-metric revenue projection
      6. Recommend   — prioritized actionable recommendations
      7. Explain     — LLM or deterministic executive narrative

    Returns the fully structured decision output dict.
    """
    pipeline_start = time.perf_counter()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    logger.info("Pipeline starting", extra={"run_id": run_id})

    config  = load_config(config_path)
    paths   = build_paths(config)
    llm_cfg = config.get("llm", {})

    # Stage 1: Ingest
    with log_stage(logger, "ingest"):
        raw_df = load_or_create_raw(paths.raw, source_csv=source_csv)

    # Stage 2: Transform
    with log_stage(logger, "transform"):
        processed_df = transform_data(raw_df, paths.processed)

    # Stage 3: Multi-metric Anomaly Detection
    with log_stage(logger, "anomaly_detection"):
        anomaly_df, anomaly_summary = detect_anomalies(
            processed_df,
            contamination=config["anomaly"]["contamination"],
            lookback=config["data"].get("lookback_days", 14),
        )

    # Stage 4: Root Cause Analysis
    with log_stage(logger, "root_cause"):
        root_cause = analyze_root_cause(
            anomaly_df,
            lookback_days=config["data"].get("lookback_days", 14),
        )

    # Stage 5: Multi-metric Forecasting
    with log_stage(logger, "forecasting"):
        forecast_summary = forecast_revenue(
            anomaly_df,
            periods=config["forecast"]["periods"],
        )

    # Stage 6: Recommendations
    with log_stage(logger, "recommendations"):
        recommendations = generate_recommendations(root_cause, anomaly_summary)

    # Stage 7: LLM Explanation
    with log_stage(logger, "explanation"):
        explanation = build_explanation(
            anomaly_summary=anomaly_summary,
            root_causes=root_cause,
            forecast_summary=forecast_summary,
            recommendations=recommendations,
            model=llm_cfg.get("model", "claude-haiku-4-5-20251001"),
            max_tokens=llm_cfg.get("max_tokens", 300),
        )

    total_ms = round((time.perf_counter() - pipeline_start) * 1000, 1)

    # ── Serialize raw time-series for frontend charting ───────────────────────
    # Aggregate daily so the frontend gets one row per date (not per dimension)
    daily_df = (
        anomaly_df.groupby("date", as_index=False)
        .agg(revenue=("revenue", "sum"), orders=("orders", "sum"))
        .sort_values("date")
        .reset_index(drop=True)
    )
    if daily_df.empty:
        raise ValueError("No data remained after aggregation. Please check your uploaded file.")

    daily_df["aov"] = (daily_df["revenue"] / daily_df["orders"].fillna(1).clip(lower=1)).round(2)

    dates_list   = daily_df["date"].dt.strftime("%Y-%m-%d").tolist()
    revenue_list = daily_df["revenue"].round(2).tolist()
    orders_list  = daily_df["orders"].round(2).tolist()
    aov_list     = daily_df["aov"].tolist()

    # KPI cards — compare last 14 days vs prior 14 days
    lookback = config["data"].get("lookback_days", 14)
    has_prior = len(daily_df) >= lookback * 2
    recent_rev  = float(daily_df["revenue"].tail(lookback).sum())
    prior_rev   = float(daily_df["revenue"].iloc[-lookback*2:-lookback].sum()) if has_prior else recent_rev
    recent_ord  = float(daily_df["orders"].tail(lookback).sum())
    prior_ord   = float(daily_df["orders"].iloc[-lookback*2:-lookback].sum()) if has_prior else recent_ord
    recent_aov_s = daily_df["aov"].tail(lookback)
    prior_aov_s  = daily_df["aov"].iloc[-lookback*2:-lookback] if has_prior else recent_aov_s
    recent_aov  = float(recent_aov_s.mean()) if not recent_aov_s.empty else 0.0
    prior_aov   = float(prior_aov_s.mean())  if not prior_aov_s.empty  else recent_aov

    def _pct(a: float, b: float) -> float:
        return round((a - b) / b * 100, 1) if b else 0.0

    rev_chg = _pct(recent_rev, prior_rev)
    ord_chg = _pct(recent_ord, prior_ord)
    aov_chg = _pct(recent_aov, prior_aov)

    kpis = {
        "revenue": {
            "label": "Total Revenue",
            "val": f"${recent_rev:,.0f}",
            "raw": recent_rev,
            "prior": prior_rev,
            "chg": rev_chg,
        },
        "orders": {
            "label": "Total Orders",
            "val": f"{int(recent_ord):,}",
            "raw": recent_ord,
            "prior": prior_ord,
            "chg": ord_chg,
        },
        "aov": {
            "label": "Avg Order Value",
            "val": f"${recent_aov:.2f}",
            "raw": recent_aov,
            "prior": prior_aov,
            "chg": aov_chg,
        },
        "health": {
            "label": "Health Score",
            "val": f"{max(0, min(100, round(50 + rev_chg)))} / 100",
            "raw": max(0, min(100, round(50 + rev_chg))),
            "prior": 50,
            "chg": rev_chg,
        },
    }

    # Forecast dates (continuation of dates_list)
    import pandas as _pd
    last_date = _pd.Timestamp(dates_list[-1]) if dates_list else _pd.Timestamp.now()
    periods   = config["forecast"]["periods"]
    forecast_dates = [
        (last_date + _pd.Timedelta(days=i+1)).strftime("%Y-%m-%d")
        for i in range(periods)
    ]

    total_ms = round((time.perf_counter() - pipeline_start) * 1000, 1)

    result: dict[str, Any] = {
        # ── Raw time-series (for frontend charts) ──────────────────────────────
        "dates":    dates_list,
        "revenue":  revenue_list,
        "orders":   orders_list,
        "aov":      aov_list,
        "kpis":     kpis,
        "forecast_dates": forecast_dates,
        # ── Core decision output ───────────────────────────────────────────────
        "metric":           anomaly_summary["metric"],
        "anomaly_detected": anomaly_summary["anomaly_detected"],
        "severity":         anomaly_summary["severity"],
        "change":           anomaly_summary["change"],
        "change_pct":       anomaly_summary["change_pct"],
        "anomaly_count":    anomaly_summary["anomaly_count"],
        "anomaly_dates":    anomaly_summary["anomaly_dates"],
        # Multi-metric breakdown
        "per_metric":       anomaly_summary.get("per_metric", {}),
        # Root cause
        "root_cause":       root_cause,
        # Forecast
        "prediction":              forecast_summary["prediction"],
        "forecast_pct_change":     forecast_summary.get("forecast_pct_change", 0.0),
        "forecast_values":         forecast_summary["forecast_values"],
        "forecast_confidence_lower": forecast_summary.get("confidence_lower", []),
        "forecast_confidence_upper": forecast_summary.get("confidence_upper", []),
        "model":                   forecast_summary.get("model", "linear_trend"),
        "per_metric_forecast":     forecast_summary.get("per_metric", {}),
        # Recommendations
        "recommendation":   recommendations,
        # Intelligence layer
        "confidence":       explanation["confidence"],
        "explanation":      explanation["narrative"],
        "llm_powered":      explanation["llm_powered"],
        # Metadata
        "processing_time_ms": total_ms,
        "timestamp":          datetime.now(timezone.utc).isoformat(),
        "pipeline_version":   config.get("project", {}).get("version", "2.0.0"),
    }

    logger.info(
        "Pipeline complete",
        extra={
            "run_id":             run_id,
            "processing_time_ms": total_ms,
            "anomaly_detected":   result["anomaly_detected"],
            "severity":           result["severity"],
            "confidence":         result["confidence"],
        },
    )
    # Sanitize before returning: removes NaN/Inf and numpy types that break JSON
    return _sanitize(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AI Decision Intelligence Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python run_pipeline.py\n"
            "  python run_pipeline.py --pretty\n"
            "  python run_pipeline.py --html\n"
            "  python run_pipeline.py --pretty --html\n"
            "  python run_pipeline.py --json-only\n"
        ),
    )
    parser.add_argument("--config",    help="Path to custom config.yaml", default=None)
    parser.add_argument("--pretty",    action="store_true", help="Pretty-print JSON to stdout")
    parser.add_argument("--html",      action="store_true", help="Save HTML executive brief to outputs/")
    parser.add_argument("--json-only", action="store_true", help="Suppress CLI report; output JSON only")
    args = parser.parse_args()

    output = run_pipeline(args.config)

    # CLI report
    if not args.json_only:
        try:
            from app.engine.reporting.cli_output import render_cli_report
            render_cli_report(output)
        except Exception as e:
            logger.warning("CLI report failed", extra={"error": str(e)})

    # HTML report
    if args.html:
        try:
            from app.engine.reporting.html_report import generate_html_report
            ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = _ROOT / "outputs" / f"decision_brief_{ts}.html"
            generate_html_report(output, out)
            print(f"\n  HTML report saved -> {out}\n")
        except Exception as e:
            logger.warning("HTML report failed", extra={"error": str(e)})

    # JSON output
    if args.pretty or args.json_only:
        print(json.dumps(output, indent=2))
