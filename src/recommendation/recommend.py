"""Enterprise recommendation engine with priority, impact, owner, and confidence.

Generates prioritized, actionable recommendations from:
  - Root cause dimensional drivers (campaign, region, category, channel)
  - Enterprise signals (inventory_status, discount_band, incident_flag)
  - Multi-metric anomaly context (revenue, orders, avg_order_value)

Priority assignment:
  >= 40% contribution or CRITICAL severity  -> HIGH
  >= 20% contribution or WARNING severity   -> MEDIUM
  <  20% contribution and NORMAL severity   -> LOW
"""
from __future__ import annotations

from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)

_PRIORITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def _make_rec(
    action: str,
    priority: str,
    expected_impact: str,
    timeline: str,
    owner: str,
    confidence: float = 0.75,
) -> dict[str, Any]:
    return {
        "action":          action,
        "priority":        priority,
        "expected_impact": expected_impact,
        "timeline":        timeline,
        "owner":           owner,
        "confidence":      round(confidence, 2),
    }


def _priority(contribution: float, severity: str) -> str:
    if contribution >= 40 or severity == "CRITICAL":
        return "HIGH"
    if contribution >= 20 or severity == "WARNING":
        return "MEDIUM"
    return "LOW"


def _impact_range(contribution: float) -> str:
    lo = int(contribution * 0.55)
    hi = int(contribution * 0.85)
    return f"{lo}–{hi}% revenue recovery"


def _campaign_rec(cause: dict, severity: str) -> dict[str, Any]:
    gv   = cause["group_value"]
    cont = abs(float(cause["contribution_pct"]))
    pri  = _priority(cont, severity)
    return _make_rec(
        action=f"Reactivate '{gv}' immediately — increase budget by 20-30% to offset lost reach; "
               f"A/B test creative refresh within 48 hours",
        priority=pri,
        expected_impact=f"Expected {_impact_range(cont)} within 7 days",
        timeline="Immediate (24–48 hours)",
        owner="Growth & Performance Marketing",
        confidence=0.88 if pri == "HIGH" else 0.75,
    )


def _region_rec(cause: dict, severity: str) -> dict[str, Any]:
    gv   = cause["group_value"]
    cont = abs(float(cause["contribution_pct"]))
    pri  = _priority(cont, severity)
    return _make_rec(
        action=f"Deploy regional recovery playbook for {gv}: activate local promotions, "
               f"reallocate national ad spend (+15%), and accelerate field sales outreach",
        priority=pri,
        expected_impact=f"Expected {_impact_range(cont)} within 14 days",
        timeline="Short-term (3–5 business days)",
        owner="Regional Sales Director",
        confidence=0.78 if pri == "HIGH" else 0.65,
    )


def _category_rec(cause: dict, severity: str) -> dict[str, Any]:
    gv   = cause["group_value"]
    cont = abs(float(cause["contribution_pct"]))
    pri  = _priority(cont, severity)
    return _make_rec(
        action=f"Audit '{gv}' category: review competitive pricing, check fulfillment SLAs, "
               f"and run targeted win-back promotion for lapsed buyers",
        priority=pri,
        expected_impact=f"Expected {_impact_range(cont)} within 21 days",
        timeline="Short-term (1–2 weeks)",
        owner="Category Management & Merchandising",
        confidence=0.72,
    )


def _channel_rec(cause: dict, severity: str) -> dict[str, Any]:
    gv   = cause["group_value"]
    cont = abs(float(cause["contribution_pct"]))
    pri  = _priority(cont, severity)
    return _make_rec(
        action=f"Investigate {gv} channel performance: check funnel drop-off, load times, "
               f"and payment success rates; escalate any technical incidents to engineering",
        priority=pri,
        expected_impact=f"Expected {_impact_range(cont)} within 5 days once resolved",
        timeline="Immediate (24 hours for triage)",
        owner="Digital Product & Engineering",
        confidence=0.80,
    )


def _inventory_rec(cause: dict, severity: str) -> dict[str, Any]:
    gv   = cause["group_value"]
    cont = abs(float(cause["contribution_pct"]))
    pri  = _priority(cont, severity)
    action = (
        "Expedite emergency replenishment order; activate substitute SKU recommendations "
        "on product pages; notify demand planning team for safety-stock review"
        if gv == "out_of_stock"
        else f"Monitor {gv} inventory levels daily; trigger reorder for items within 10-day runout"
    )
    return _make_rec(
        action=action,
        priority=pri,
        expected_impact=f"Prevents estimated {int(cont * 0.7)}–{int(cont * 0.9)}% additional revenue loss",
        timeline="Immediate" if gv == "out_of_stock" else "Short-term (2–3 days)",
        owner="Supply Chain & Inventory Management",
        confidence=0.82,
    )


def _incident_rec(cause: dict, severity: str) -> dict[str, Any]:
    cont = abs(float(cause["contribution_pct"]))
    pri  = _priority(cont, severity)
    return _make_rec(
        action="Declare operational incident: notify engineering on-call, initiate customer "
               "communication, activate SLA recovery protocols, and document in incident tracker",
        priority=pri,
        expected_impact=f"Mitigates reputational damage; protects {int(cont * 0.6)}–{int(cont * 0.85)}% at-risk revenue",
        timeline="Immediate (within 1 hour)",
        owner="Engineering On-Call & Customer Operations",
        confidence=0.90,
    )


def _orders_rec(anomaly_summary: dict) -> dict[str, Any]:
    orders_data = anomaly_summary.get("per_metric", {}).get("orders", {})
    change = orders_data.get("change", "")
    return _make_rec(
        action=f"Order volume decline ({change}) indicates demand softening — "
               f"launch time-limited flash sale or free-shipping promotion to stimulate demand",
        priority="MEDIUM",
        expected_impact="Expected 10–20% order volume recovery within 5 days",
        timeline="Short-term (2–3 days)",
        owner="E-Commerce & Growth Team",
        confidence=0.70,
    )


def _aov_rec(anomaly_summary: dict) -> dict[str, Any]:
    aov_data = anomaly_summary.get("per_metric", {}).get("avg_order_value", {})
    change = aov_data.get("change", "")
    return _make_rec(
        action=f"Average order value declining ({change}) — activate cross-sell/upsell "
               f"recommendations, review discount band mix, and test bundle pricing",
        priority="MEDIUM",
        expected_impact="Expected 5–15% AOV recovery within 7 days",
        timeline="Short-term (1 week)",
        owner="Product & Pricing Strategy",
        confidence=0.68,
    )


def generate_recommendations(
    root_causes: list[dict[str, Any]],
    anomaly_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate prioritized, actionable recommendations from root causes and anomaly context.

    Returns a list of recommendation dicts sorted HIGH -> MEDIUM -> LOW.
    """
    recs: list[dict[str, Any]] = []
    severity = anomaly_summary.get("severity", "NORMAL")
    seen_dims: set[str] = set()

    dispatch = {
        "campaign":         _campaign_rec,
        "region":           _region_rec,
        "category":         _category_rec,
        "channel":          _channel_rec,
        "inventory_status": _inventory_rec,
        "incident_flag":    _incident_rec,
    }

    for cause in root_causes:
        dimension = cause.get("dimension", "")
        delta     = float(cause.get("delta", 0.0))
        is_decline = delta < 0

        if dimension == "n/a" or not is_decline:
            continue

        handler = dispatch.get(dimension)
        if handler and dimension not in seen_dims:
            recs.append(handler(cause, severity))
            seen_dims.add(dimension)

    # Multi-metric secondary recommendations
    per_metric = anomaly_summary.get("per_metric", {})
    orders_data = per_metric.get("orders", {})
    aov_data    = per_metric.get("avg_order_value", {})

    if orders_data.get("anomaly_detected") and "orders_volume" not in seen_dims:
        recs.append(_orders_rec(anomaly_summary))
        seen_dims.add("orders_volume")

    if aov_data.get("anomaly_detected") and aov_data.get("change_pct", 0) < -5 \
            and "aov_decline" not in seen_dims:
        recs.append(_aov_rec(anomaly_summary))
        seen_dims.add("aov_decline")

    # Always include a monitoring baseline
    if not recs or severity == "NORMAL":
        recs.append(_make_rec(
            action="Maintain elevated monitoring cadence: daily metric review, "
                   "automated alerting on 5%+ day-over-day changes, and weekly root-cause review",
            priority="LOW",
            expected_impact="Early detection prevents escalation beyond 10% revenue impact",
            timeline="Ongoing",
            owner="Analytics & Business Intelligence",
            confidence=0.95,
        ))

    recs.sort(key=lambda r: _PRIORITY_ORDER.get(r["priority"], 99))

    logger.info(
        "Recommendations generated",
        extra={
            "count":         len(recs),
            "high_priority": sum(1 for r in recs if r["priority"] == "HIGH"),
        },
    )
    return recs
