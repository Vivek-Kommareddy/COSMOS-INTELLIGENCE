"""Multi-metric anomaly detection using Isolation Forest with severity scoring.

Analyzes three business metrics simultaneously:
  - revenue         : total sales value
  - orders          : transaction volume
  - avg_order_value : average ticket size (revenue / orders)

Each metric receives its own Isolation Forest model, anomaly flags,
severity label, and period-over-period change signal.

The overall anomaly summary reflects the worst (highest severity) metric.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.engine.utils.helpers import safe_pct_change
from app.engine.utils.logger import get_logger

logger = get_logger(__name__)

# ── Severity thresholds ──────────────────────────────────────────────────────
_THRESHOLD_CRITICAL = -0.15
_THRESHOLD_WARNING  = -0.05

TRACKED_METRICS: list[tuple[str, str]] = [
    ("revenue",         "Revenue"),
    ("orders",          "Order Volume"),
    ("avg_order_value", "Avg Order Value"),
]

_SEVERITY_ORDER = {"CRITICAL": 3, "WARNING": 2, "NORMAL": 1}


def _classify_severity(if_score: float, pct_change: float) -> str:
    if if_score < _THRESHOLD_CRITICAL or pct_change < -20.0:
        return "CRITICAL"
    if if_score < _THRESHOLD_WARNING or pct_change < -10.0:
        return "WARNING"
    return "NORMAL"


def _analyse_metric(
    df: pd.DataFrame,
    metric: str,
    label: str,
    contamination: float,
    lookback: int,
) -> dict[str, Any]:
    """Run Isolation Forest on a single daily metric and return its summary."""
    daily = (
        df.groupby("date", as_index=False)[metric]
        .sum()
        .sort_values("date")
        .reset_index(drop=True)
    )

    values = daily[[metric]].values.astype(float)

    # Guard: zero-variance data (all identical values) causes StandardScaler to produce
    # all-zeros and breaks IsolationForest tree construction.
    if np.std(values) == 0 or len(values) < 2:
        logger.warning(
            "Skipping IsolationForest — zero variance or insufficient rows",
            extra={"metric": metric, "rows": len(values)},
        )
        recent = daily.tail(lookback)
        prior  = daily.iloc[-lookback * 2:-lookback] if len(daily) >= lookback * 2 else pd.DataFrame()
        recent_val = float(recent[metric].sum()) if not recent.empty else 0.0
        prior_val  = float(prior[metric].sum())  if not prior.empty  else recent_val
        pct_change = safe_pct_change(recent_val, prior_val)
        return {
            "metric":           metric,
            "label":            label,
            "anomaly_detected": False,
            "severity":         "NORMAL",
            "change":           f"{pct_change:+.1f}%",
            "change_pct":       round(pct_change, 2),
            "anomaly_count":    0,
            "anomaly_dates":    [],
            "recent_value":     round(recent_val, 2),
            "prior_value":      round(prior_val, 2),
            "if_score_worst":   0.0,
        }

    scaler = StandardScaler()
    scaled = scaler.fit_transform(values)

    model = IsolationForest(contamination=contamination, random_state=42, n_jobs=-1)
    model.fit(scaled)

    flags  = model.predict(scaled)
    scores = model.decision_function(scaled)

    anomaly_mask = flags == -1
    # Filter NaT before calling strftime to avoid AttributeError on NaTType
    anomaly_dates_all = daily.loc[anomaly_mask, "date"].dropna()

    # Use full lookback if enough data, else fall back gracefully
    recent = daily.tail(lookback)
    prior  = daily.iloc[-lookback * 2:-lookback] if len(daily) >= lookback * 2 else pd.DataFrame()

    recent_val = float(recent[metric].sum()) if not recent.empty else 0.0
    prior_val  = float(prior[metric].sum())  if not prior.empty  else recent_val
    pct_change = safe_pct_change(recent_val, prior_val)

    worst_score = float(scores[anomaly_mask].min()) if anomaly_mask.any() else 0.0
    severity    = _classify_severity(worst_score, pct_change)

    recent_date_strs = set(recent["date"].dt.strftime("%Y-%m-%d"))
    anomaly_dates_recent = sorted(
        {d.strftime("%Y-%m-%d") for d in anomaly_dates_all
         if pd.notna(d) and d.strftime("%Y-%m-%d") in recent_date_strs}
    )

    return {
        "metric":           metric,
        "label":            label,
        "anomaly_detected": bool(anomaly_mask.any()),
        "severity":         severity,
        "change":           f"{pct_change:+.1f}%",
        "change_pct":       round(pct_change, 2),
        "anomaly_count":    int(anomaly_mask.sum()),
        "anomaly_dates":    anomaly_dates_recent[:10],
        "recent_value":     round(recent_val, 2),
        "prior_value":      round(prior_val, 2),
        "if_score_worst":   round(worst_score, 4),
    }


_MIN_ROWS_FOR_ANALYSIS = 10  # IsolationForest needs meaningful variance


def detect_anomalies(
    df: pd.DataFrame,
    contamination: float = 0.08,
    lookback: int = 14,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Detect anomalies across revenue, orders, and avg_order_value.

    Returns:
        (enriched_df, summary)
    """
    if df.empty:
        raise ValueError(
            "Your dataset is empty after validation. "
            "Please check that your file contains valid dates and numeric revenue/orders columns."
        )

    unique_dates = df["date"].nunique() if "date" in df.columns else len(df)
    if unique_dates < _MIN_ROWS_FOR_ANALYSIS:
        raise ValueError(
            f"Your dataset has only {unique_dates} unique date(s). "
            f"At least {_MIN_ROWS_FOR_ANALYSIS} daily rows are required for meaningful analysis. "
            "Please upload a dataset covering at least 10 days."
        )

    out = df.copy()

    if "avg_order_value" not in out.columns:
        out["avg_order_value"] = np.where(
            out["orders"] > 0, out["revenue"] / out["orders"], 0.0
        )

    per_metric: dict[str, dict[str, Any]] = {}
    for col, label in TRACKED_METRICS:
        if col not in out.columns:
            logger.warning("Metric column missing — skipping", extra={"metric": col})
            continue
        per_metric[col] = _analyse_metric(out, col, label, contamination, lookback)

    overall_severity = max(
        (m["severity"] for m in per_metric.values()),
        key=lambda s: _SEVERITY_ORDER.get(s, 0),
        default="NORMAL",
    )
    any_anomaly = any(m["anomaly_detected"] for m in per_metric.values())

    rev = per_metric.get("revenue", {})

    summary: dict[str, Any] = {
        "per_metric":       per_metric,
        "metric":           "revenue",
        "anomaly_detected": any_anomaly,
        "severity":         overall_severity,
        "change":           rev.get("change", "+0.0%"),
        "change_pct":       rev.get("change_pct", 0.0),
        "anomaly_count":    rev.get("anomaly_count", 0),
        "anomaly_dates":    rev.get("anomaly_dates", []),
        "recent_revenue":   rev.get("recent_value", 0.0),
        "prior_revenue":    rev.get("prior_value", 0.0),
    }

    logger.info(
        "Multi-metric anomaly detection complete",
        extra={
            "metrics_analysed": list(per_metric.keys()),
            "overall_severity": overall_severity,
            "any_anomaly":      any_anomaly,
            "revenue_change":   rev.get("change", "n/a"),
        },
    )
    return out, summary
