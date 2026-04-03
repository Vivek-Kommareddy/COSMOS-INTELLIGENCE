"""Data processing: clean, validate, aggregate, and derive enterprise metrics.

Derived metrics added during transform:
  avg_order_value   = revenue / orders          (ticket size signal)
  conversion_rate   = orders / impressions * 100 (conversion % signal)

These three metrics — revenue, orders, avg_order_value — form the multi-metric
intelligence layer for anomaly detection and forecasting.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.utils.helpers import ensure_parent
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── Schema contracts ─────────────────────────────────────────────────────────
REQUIRED_COLUMNS = [
    "date", "region", "product", "category", "channel",
    "revenue", "orders", "impressions",
    "campaign", "inventory_status", "discount_band",
    "holiday_flag", "incident_flag",
]

CATEGORICAL_COLUMNS = [
    "region", "product", "category", "channel",
    "campaign", "inventory_status", "discount_band",
]

NUMERIC_COLUMNS    = ["revenue", "orders", "impressions", "holiday_flag", "incident_flag"]
AGG_DIMENSIONS     = ["date", "region", "product", "category", "channel",
                      "campaign", "inventory_status", "discount_band",
                      "holiday_flag", "incident_flag"]


def transform_data(df: pd.DataFrame, processed_path: Path) -> pd.DataFrame:
    """Clean, validate, aggregate, and derive key business metrics.

    Steps:
    1.  Ensure all expected columns exist (fill with defaults if missing).
    2.  Parse and validate dates; drop rows with unparseable dates.
    3.  Coerce numeric columns; replace nulls with 0.
    4.  Fill missing categoricals with 'Unknown'.
    5.  Aggregate multiple records per dimension group by summing revenue/orders/impressions.
    6.  Derive avg_order_value and conversion_rate.
    7.  Persist to processed_path and return the result.
    """
    clean = df.copy()

    # 1. Ensure required columns ─────────────────────────────────────────────
    for col in REQUIRED_COLUMNS:
        if col not in clean.columns:
            clean[col] = None
            logger.warning("Added missing column", extra={"column": col})

    # 2. Parse dates ──────────────────────────────────────────────────────────
    before = len(clean)
    clean["date"] = pd.to_datetime(clean["date"], errors="coerce")
    clean = clean.dropna(subset=["date"])
    dropped = before - len(clean)
    if dropped:
        logger.warning("Dropped rows with unparseable dates", extra={"dropped": dropped})

    # 3. Coerce numerics ──────────────────────────────────────────────────────
    for col in NUMERIC_COLUMNS:
        clean[col] = pd.to_numeric(clean[col], errors="coerce").fillna(0.0)

    # 4. Fill categorical nulls ───────────────────────────────────────────────
    for col in CATEGORICAL_COLUMNS:
        null_count = int(clean[col].isna().sum())
        if null_count:
            logger.warning(
                "Filling null categoricals",
                extra={"column": col, "count": null_count},
            )
        clean[col] = clean[col].fillna("Unknown")

    # 5. Aggregate ────────────────────────────────────────────────────────────
    grouped = (
        clean.groupby(AGG_DIMENSIONS, as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            orders=("orders", "sum"),
            impressions=("impressions", "sum"),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    # 6. Derive business metrics ──────────────────────────────────────────────
    grouped["avg_order_value"] = np.where(
        grouped["orders"] > 0,
        (grouped["revenue"] / grouped["orders"]).round(2),
        0.0,
    )
    grouped["conversion_rate"] = np.where(
        grouped["impressions"] > 0,
        ((grouped["orders"] / grouped["impressions"]) * 100).round(4),
        0.0,
    )

    # 7. Persist ──────────────────────────────────────────────────────────────
    ensure_parent(processed_path)
    grouped.to_csv(processed_path, index=False)

    logger.info(
        "Transform complete",
        extra={
            "input_rows": len(df),
            "output_rows": len(grouped),
            "date_range": f"{grouped['date'].min().date()} to {grouped['date'].max().date()}",
            "total_revenue": round(float(grouped["revenue"].sum()), 2),
            "avg_order_value_mean": round(float(grouped["avg_order_value"].mean()), 2),
            "conversion_rate_mean": round(float(grouped["conversion_rate"].mean()), 4),
        },
    )
    return grouped
