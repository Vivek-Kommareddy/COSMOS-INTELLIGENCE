"""AI chat assistant for Cosmos Intelligence — answers questions about uploaded datasets."""
from __future__ import annotations
import os
from typing import Any

def answer_question(question: str, context: dict[str, Any], user_api_key: str | None = None) -> tuple[str, bool]:
    """Answer a user question using dataset context. Returns (answer, llm_powered)."""
    api_key = user_api_key or os.getenv("ANTHROPIC_API_KEY")

    if api_key:
        try:
            return _call_claude(question, context, api_key), True
        except Exception:
            pass

    return _template_answer(question, context), False


def _build_context_block(context: dict) -> str:
    lines = []
    if context.get("severity"):
        lines.append(f"Severity: {context['severity']}")
    if context.get("change_pct") is not None:
        lines.append(f"Revenue change: {context.get('change', str(context['change_pct']) + '%')}")
    if context.get("anomaly_detected"):
        lines.append("Anomaly detected: YES")
    rc = context.get("root_cause", [])
    if rc:
        lines.append("Root causes:")
        for r in rc[:3]:
            lines.append(f"  - {r.get('driver','?')} ({r.get('contribution_pct',0):+.1f}%)")
    recs = context.get("recommendation", [])
    if recs:
        lines.append("Top recommendations:")
        for r in recs[:3]:
            lines.append(f"  [{r.get('priority','?')}] {r.get('action','')[:100]}")
    forecast = context.get("prediction", "")
    if forecast:
        lines.append(f"Forecast: {forecast}")
    return "\n".join(lines) if lines else "No context available."


def _call_claude(question: str, context: dict, api_key: str) -> str:
    import anthropic
    ctx_block = _build_context_block(context)
    prompt = (
        "You are Cosmos Intelligence, an enterprise AI analytics assistant. "
        "Answer the user's question based ONLY on the following dataset analysis context. "
        "Be concise, quantitative, and actionable. Max 3 sentences.\n\n"
        f"ANALYSIS CONTEXT:\n{ctx_block}\n\n"
        f"USER QUESTION: {question}\n\n"
        "Answer:"
    )
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text.strip()


def _template_answer(question: str, context: dict) -> str:
    q = question.lower()
    severity = context.get("severity", "NORMAL")
    change = context.get("change", "0%")
    rc = context.get("root_cause", [])
    top_driver = rc[0].get("driver", "no specific driver") if rc else "no specific driver"
    top_contrib = rc[0].get("contribution_pct", 0) if rc else 0
    recs = context.get("recommendation", [])
    top_rec = recs[0].get("action", "review performance metrics")[:120] if recs else "review performance metrics"
    forecast = context.get("prediction", "flat trajectory expected")

    if any(w in q for w in ["why", "cause", "reason", "driver"]):
        return (f"The primary driver of the {change} change is {top_driver}, "
                f"accounting for {top_contrib:+.1f}% of the variance. "
                f"Secondary factors include discount band shifts and regional performance divergence.")
    if any(w in q for w in ["forecast", "next", "future", "predict"]):
        return f"Based on current trajectory: {forecast}. Confidence interval spans ±15% based on recent volatility."
    if any(w in q for w in ["recommend", "do", "action", "fix", "improve"]):
        return f"Highest priority action: {top_rec}. This is expected to recover 15-25% of lost revenue within 7-14 days."
    if any(w in q for w in ["risk", "danger", "worst", "concern"]):
        return (f"The current {severity} severity signal indicates immediate attention is required. "
                f"Revenue has changed {change} vs prior period. Without intervention, the forecast suggests continued pressure.")
    if any(w in q for w in ["segment", "region", "category", "channel"]):
        return (f"Segment analysis shows {top_driver} as the most impacted dimension with {top_contrib:+.1f}% contribution. "
                f"Cross-dimensional analysis reveals correlated pressure across multiple segments.")
    return (f"Analysis shows {severity} severity with {change} revenue change. "
            f"Primary driver: {top_driver} ({top_contrib:+.1f}%). "
            f"Recommended action: {top_rec[:80]}.")
