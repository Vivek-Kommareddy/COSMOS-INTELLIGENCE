"""Pipeline orchestrator — runs all 7 stages and produces structured output + reports.

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
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.anomaly.detect import detect_anomalies
from src.forecasting.forecast import forecast_revenue
from src.ingestion.ingest import load_or_create_raw
from src.llm.explain import build_explanation
from src.processing.transform import transform_data
from src.recommendation.recommend import generate_recommendations
from src.root_cause.analyze import analyze_root_cause
from src.utils.helpers import build_paths, load_config
from src.utils.logger import get_logger, log_stage

logger = get_logger(__name__)

_ROOT = Path(__file__).resolve().parent


def run_pipeline(config_path: Optional[str] = None) -> dict[str, Any]:
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
        raw_df = load_or_create_raw(paths.raw)

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

    result: dict[str, Any] = {
        # Core decision output
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
    return result


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
            from src.reporting.cli_output import render_cli_report
            render_cli_report(output)
        except Exception as e:
            logger.warning("CLI report failed", extra={"error": str(e)})

    # HTML report
    if args.html:
        try:
            from src.reporting.html_report import generate_html_report
            ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = _ROOT / "outputs" / f"decision_brief_{ts}.html"
            generate_html_report(output, out)
            print(f"\n  HTML report saved -> {out}\n")
        except Exception as e:
            logger.warning("HTML report failed", extra={"error": str(e)})

    # JSON output
    if args.pretty or args.json_only:
        print(json.dumps(output, indent=2))
