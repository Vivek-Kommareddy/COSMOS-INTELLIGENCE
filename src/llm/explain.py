"""LLM-powered executive decision briefing using Anthropic Claude.

Falls back to a deterministic narrative if no API key is present.
Confidence score is computed dynamically from multi-metric signal strength.
"""
from __future__ import annotations

import os
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


# ── Confidence scoring ───────────────────────────────────────────────────────

def _compute_confidence(
    anomaly_summary: dict[str, Any],
    root_causes: list[dict[str, Any]],
    forecast_summary: dict[str, Any],
) -> float:
    """Compute a data-driven confidence score in [0.40, 0.95].

    Components:
      Base:                                0.50
      Anomaly detected (any metric):      +0.08
      Revenue signal > 15% change:       +0.10  (> 5%: +0.05)
      Multiple metrics anomalous:         +0.08  (one: +0.04)
      Root causes >= 2 meaningful drivers:+0.10  (1 driver: +0.05)
      Forecast direction consistent:      +0.05
      Enterprise signals present:         +0.04
    """
    score = 0.50

    if anomaly_summary.get("anomaly_detected"):
        score += 0.08

    rev_pct = abs(float(anomaly_summary.get("change_pct", 0.0)))
    if rev_pct > 15:
        score += 0.10
    elif rev_pct > 5:
        score += 0.05

    per_metric = anomaly_summary.get("per_metric", {})
    anomalous_metrics = sum(1 for m in per_metric.values() if m.get("anomaly_detected"))
    if anomalous_metrics >= 2:
        score += 0.08
    elif anomalous_metrics == 1:
        score += 0.04

    meaningful = [
        rc for rc in root_causes
        if abs(rc.get("contribution_pct", 0.0)) >= 10 and rc.get("dimension") != "n/a"
    ]
    if len(meaningful) >= 2:
        score += 0.10
    elif len(meaningful) == 1:
        score += 0.05

    forecast_pct = float(forecast_summary.get("forecast_pct_change", 0.0))
    change_pct   = float(anomaly_summary.get("change_pct", 0.0))
    if (forecast_pct < 0 and change_pct < 0) or (forecast_pct > 0 and change_pct > 0):
        score += 0.05

    enterprise_dims = {"inventory_status", "discount_band", "incident_flag"}
    if any(rc.get("dimension") in enterprise_dims for rc in root_causes):
        score += 0.04

    return round(min(score, 0.95), 2)


# ── Deterministic fallback ───────────────────────────────────────────────────

def _deterministic_narrative(
    anomaly_summary: dict[str, Any],
    root_causes: list[dict[str, Any]],
    forecast_summary: dict[str, Any],
) -> str:
    severity   = anomaly_summary.get("severity", "NORMAL")
    change     = anomaly_summary.get("change", "0%")
    prediction = forecast_summary.get("prediction", "No forecast available")

    # Multi-metric context
    per_metric = anomaly_summary.get("per_metric", {})
    anomalous  = [
        m["label"] for m in per_metric.values()
        if m.get("anomaly_detected") and m.get("label")
    ]
    metrics_text = (
        f"Anomalies detected across: {', '.join(anomalous)}. "
        if anomalous else ""
    )

    top_causes = [
        rc["driver"] for rc in root_causes[:3]
        if rc.get("dimension") != "n/a"
    ]
    cause_text = (
        f"Primary drivers: {'; '.join(top_causes)}."
        if top_causes
        else "No specific causal driver was isolated above the significance threshold."
    )

    return (
        f"[{severity}] Revenue has changed {change} vs the prior 14-day period. "
        f"{metrics_text}"
        f"{cause_text} "
        f"Forecast: {prediction}."
    )


# ── Anthropic Claude call ────────────────────────────────────────────────────

def _call_anthropic(
    anomaly_summary: dict[str, Any],
    root_causes: list[dict[str, Any]],
    forecast_summary: dict[str, Any],
    recommendations: list[dict[str, Any]],
    model: str,
    max_tokens: int,
) -> str:
    import anthropic  # noqa: PLC0415

    per_metric = anomaly_summary.get("per_metric", {})
    metric_lines = []
    for col, data in per_metric.items():
        flag = "ANOMALY" if data.get("anomaly_detected") else "normal"
        metric_lines.append(
            f"  {data.get('label', col):20s} {data.get('change', ''):>8s}  [{flag}]"
        )
    metrics_block = "\n".join(metric_lines) or "  No metric data"

    cause_lines = "\n".join(
        f"  • {rc['driver']} ({rc['contribution_pct']:+.1f}%)"
        for rc in root_causes[:4]
        if rc.get("dimension") != "n/a"
    ) or "  • No specific driver isolated"

    top_actions = "\n".join(
        f"  [{r['priority']}] {r['action'][:90]}"
        for r in recommendations[:3]
    )

    prompt = (
        "You are a senior enterprise decision intelligence system briefing a Fortune 500 C-suite executive.\n\n"
        f"SITUATION SUMMARY\n"
        f"  Severity:  {anomaly_summary.get('severity', 'NORMAL')}\n"
        f"  Timestamp: Latest 14-day analysis window\n\n"
        f"METRIC SIGNALS\n{metrics_block}\n\n"
        f"ROOT CAUSE ATTRIBUTION\n{cause_lines}\n\n"
        f"FORECAST\n  {forecast_summary.get('prediction', 'Unavailable')}\n\n"
        f"RECOMMENDED ACTIONS\n{top_actions}\n\n"
        "Write a concise 3-sentence executive briefing. "
        "Sentence 1: State what changed and the severity. "
        "Sentence 2: Attribute the key causal driver(s) with quantified impact. "
        "Sentence 3: State the highest-priority action and expected timeline. "
        "Be direct, quantitative, and urgency-appropriate. No bullet points. No labels."
    )

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


# ── Public interface ─────────────────────────────────────────────────────────

def build_explanation(
    anomaly_summary: dict[str, Any],
    root_causes: list[dict[str, Any]],
    forecast_summary: dict[str, Any],
    recommendations: list[dict[str, Any]],
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 300,
) -> dict[str, Any]:
    """Generate the final decision explanation with confidence score.

    Returns:
        {
            "narrative":   str,   # executive briefing
            "confidence":  float, # 0.40 – 0.95
            "llm_powered": bool,
        }
    """
    confidence = _compute_confidence(anomaly_summary, root_causes, forecast_summary)
    api_key    = os.getenv("ANTHROPIC_API_KEY")
    llm_powered = False
    narrative   = ""

    if api_key:
        try:
            narrative   = _call_anthropic(
                anomaly_summary, root_causes, forecast_summary,
                recommendations, model, max_tokens,
            )
            llm_powered = True
            logger.info("LLM executive briefing generated", extra={"model": model})
        except Exception as exc:
            logger.warning("LLM call failed; using deterministic fallback",
                           extra={"error": str(exc)})
            narrative = _deterministic_narrative(
                anomaly_summary, root_causes, forecast_summary
            )
    else:
        logger.info("ANTHROPIC_API_KEY not set; using deterministic narrative")
        narrative = _deterministic_narrative(
            anomaly_summary, root_causes, forecast_summary
        )

    return {
        "narrative":   narrative,
        "confidence":  confidence,
        "llm_powered": llm_powered,
    }
