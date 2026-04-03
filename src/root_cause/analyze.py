"""Root cause analysis: rank dimensional contributors to revenue change.

Dimensions analysed:
  Standard:   campaign, region, category, channel
  Enterprise: inventory_status, discount_band, incident_flag

Each dimension returns the top contributing groups, with:
  - absolute revenue delta
  - % contribution to total change
  - direction (declined / grew)
  - human-readable driver description

The final output is a unified ranked list sorted by |contribution_pct| descending.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Dimensions to analyse. incident_flag and holiday_flag are binary;
# they surface as causal signals when present.
_STANDARD_DIMS   = ["campaign", "region", "category", "channel"]
_ENTERPRISE_DIMS = ["inventory_status", "discount_band"]
_BINARY_DIMS     = ["incident_flag", "holiday_flag"]

_MIN_CONTRIBUTION_PCT = 5.0   # only report drivers with ≥5% contribution


def _dimension_contributions(
    current: pd.DataFrame,
    previous: pd.DataFrame,
    dimension: str,
    total_delta: float,
) -> list[dict[str, Any]]:
    """Compute per-group revenue delta and contribution % for one dimension."""
    cur = (
        current.groupby(dimension, as_index=False)["revenue"]
        .sum()
        .rename(columns={"revenue": "cur_rev"})
    )
    prv = (
        previous.groupby(dimension, as_index=False)["revenue"]
        .sum()
        .rename(columns={"revenue": "prv_rev"})
    )
    merged = cur.merge(prv, on=dimension, how="outer").fillna(0.0)
    merged["delta"] = merged["cur_rev"] - merged["prv_rev"]

    results = []
    for _, row in merged.iterrows():
        delta = float(row["delta"])
        contribution_pct = (delta / total_delta * 100) if total_delta != 0 else 0.0
        if abs(contribution_pct) < _MIN_CONTRIBUTION_PCT:
            continue

        group_value = str(row[dimension])
        direction   = "declined" if delta < 0 else "grew"
        results.append({
            "driver":           f"{dimension.replace('_', ' ').title()} '{group_value}' {direction} by {abs(delta):,.0f}",
            "dimension":        dimension,
            "group_value":      group_value,
            "delta":            round(delta, 2),
            "contribution_pct": round(contribution_pct, 1),
        })

    return sorted(results, key=lambda x: abs(x["contribution_pct"]), reverse=True)


def _binary_signal(
    current: pd.DataFrame,
    previous: pd.DataFrame,
    col: str,
    total_delta: float,
) -> list[dict[str, Any]]:
    """Surface incident / holiday flags as causal signals.

    For incident_flag: estimates the revenue LOSS by comparing impacted rows'
    avg_order_value to the baseline (non-incident rows) in the recent period.
    For holiday_flag: surfaces as a positive driver when holiday revenue is higher.
    """
    if col not in current.columns or col not in previous.columns:
        return []

    if col == "incident_flag":
        # Estimate loss: compare incident rows vs baseline (non-incident) AOV
        incident_rows  = current.loc[current[col] == 1]
        baseline_rows  = current.loc[current[col] == 0]
        if incident_rows.empty or baseline_rows.empty:
            return []
        baseline_aov   = float(baseline_rows["revenue"].sum() / max(len(baseline_rows), 1))
        incident_aov   = float(incident_rows["revenue"].sum() / max(len(incident_rows), 1))
        estimated_loss = (baseline_aov - incident_aov) * len(incident_rows)
        if estimated_loss < 0 or abs(estimated_loss) < 100:
            return []
        contribution_pct = -(estimated_loss / (float(current["revenue"].sum()) + abs(estimated_loss))) * 100
        if abs(contribution_pct) < _MIN_CONTRIBUTION_PCT:
            return []
        return [{
            "driver":           f"Operational Incident impacted revenue — estimated loss {estimated_loss:,.0f} vs non-incident baseline",
            "dimension":        col,
            "group_value":      "event_active",
            "delta":            round(-estimated_loss, 2),
            "contribution_pct": round(contribution_pct, 1),
        }]

    # For holiday_flag: standard delta comparison
    cur_affected = float(current.loc[current[col] == 1, "revenue"].sum())
    prv_affected = float(previous.loc[previous[col] == 1, "revenue"].sum())
    delta = cur_affected - prv_affected

    if abs(delta) < 1.0 or total_delta == 0:
        return []
    contribution_pct = delta / total_delta * 100
    if abs(contribution_pct) < _MIN_CONTRIBUTION_PCT:
        return []

    label = col.replace("_flag", "").replace("_", " ").title()
    direction = "declined" if delta < 0 else "grew"
    return [{
        "driver":           f"{label} event revenue {direction} by {abs(delta):,.0f}",
        "dimension":        col,
        "group_value":      "event_active",
        "delta":            round(delta, 2),
        "contribution_pct": round(contribution_pct, 1),
    }]


def analyze_root_cause(df: pd.DataFrame, lookback_days: int = 14) -> list[dict[str, Any]]:
    """Identify the top contributors to revenue change in the latest lookback_days window.

    Compares the most recent N days against the prior N days across
    standard and enterprise dimensions.

    Returns a ranked list of root-cause dicts.
    """
    ordered  = df.sort_values("date")
    max_date = ordered["date"].max()

    current_start  = max_date - pd.Timedelta(days=lookback_days - 1)
    previous_start = max_date - pd.Timedelta(days=lookback_days * 2 - 1)
    previous_end   = max_date - pd.Timedelta(days=lookback_days)

    current  = ordered[ordered["date"] >= current_start]
    previous = ordered[ordered["date"].between(previous_start, previous_end)]

    if previous.empty:
        logger.warning("Insufficient history for root-cause analysis (need >= 28 days)")
        return [{
            "driver":           "Insufficient history for comparison",
            "dimension":        "n/a",
            "group_value":      "n/a",
            "delta":            0.0,
            "contribution_pct": 0.0,
        }]

    total_recent = float(current["revenue"].sum())
    total_prior  = float(previous["revenue"].sum())
    total_delta  = total_recent - total_prior

    if total_delta == 0:
        return [{
            "driver":           "No significant revenue change detected",
            "dimension":        "n/a",
            "group_value":      "n/a",
            "delta":            0.0,
            "contribution_pct": 0.0,
        }]

    all_findings: list[dict[str, Any]] = []

    for dim in _STANDARD_DIMS + _ENTERPRISE_DIMS:
        if dim in df.columns:
            all_findings.extend(
                _dimension_contributions(current, previous, dim, total_delta)
            )

    for col in _BINARY_DIMS:
        all_findings.extend(_binary_signal(current, previous, col, total_delta))

    # Deduplicate and sort
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in sorted(all_findings, key=lambda x: abs(x["contribution_pct"]), reverse=True):
        key = f"{item['dimension']}:{item['group_value']}"
        if key not in seen:
            seen.add(key)
            unique.append(item)

    if not unique:
        unique = [{
            "driver":           "No single driver above threshold; monitor cross-metric trends",
            "dimension":        "n/a",
            "group_value":      "n/a",
            "delta":            round(total_delta, 2),
            "contribution_pct": 100.0,
        }]

    logger.info(
        "Root cause analysis complete",
        extra={
            "total_delta":    round(total_delta, 2),
            "drivers_found":  len(unique),
            "top_driver":     unique[0]["driver"] if unique else None,
        },
    )
    return unique
