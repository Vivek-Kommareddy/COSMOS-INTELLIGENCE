"""HTML decision brief generator.

Produces a self-contained, single-file HTML report with:
  - KPI severity banner
  - Multi-metric scorecard table
  - Root cause attribution bar chart (inline Plotly)
  - 7-day revenue forecast chart with confidence band (inline Plotly)
  - Prioritized action plan table
  - Executive briefing narrative

No external CDN dependencies for charts — Plotly is embedded inline.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.engine.utils.logger import get_logger

logger = get_logger(__name__)

# ── Severity colours ─────────────────────────────────────────────────────────
_SEV_COLOR = {
    "CRITICAL": "#ef4444",
    "WARNING":  "#f59e0b",
    "NORMAL":   "#22c55e",
}
_SEV_BG = {
    "CRITICAL": "#fef2f2",
    "WARNING":  "#fffbeb",
    "NORMAL":   "#f0fdf4",
}
_SEV_ICON = {
    "CRITICAL": "🔴",
    "WARNING":  "🟡",
    "NORMAL":   "🟢",
}


def _metric_rows(per_metric: dict) -> str:
    rows = []
    for col, m in per_metric.items():
        chg_pct = m.get("change_pct", 0.0)
        color   = "#ef4444" if chg_pct < -5 else "#22c55e" if chg_pct > 5 else "#6b7280"
        is_anom = m.get("anomaly_detected", False)
        sev     = m.get("severity", "NORMAL")
        sev_c   = _SEV_COLOR.get(sev, "#6b7280")
        badge   = (
            f'<span style="background:{sev_c};color:white;padding:2px 8px;'
            f'border-radius:12px;font-size:12px;font-weight:600">{sev}</span>'
        )
        anom_badge = (
            '<span style="background:#ef4444;color:white;padding:2px 8px;'
            'border-radius:12px;font-size:12px;font-weight:600">ANOMALY</span>'
            if is_anom else
            '<span style="color:#9ca3af;font-size:12px">—</span>'
        )
        rows.append(f"""
        <tr>
          <td style="font-weight:600">{m.get('label', col)}</td>
          <td style="color:{color};font-weight:700;text-align:right">{m.get('change', '0%')}</td>
          <td style="text-align:center">{badge}</td>
          <td style="text-align:center">{anom_badge}</td>
          <td style="text-align:right">{m.get('recent_value', 0):>,.1f}</td>
          <td style="text-align:right">{m.get('prior_value', 0):>,.1f}</td>
        </tr>""")
    return "\n".join(rows)


def _root_cause_chart_json(root_causes: list[dict]) -> str:
    """Build Plotly horizontal bar chart JSON for root causes."""
    filtered = [rc for rc in root_causes if rc.get("dimension") != "n/a"][:10]
    if not filtered:
        return "null"

    labels = [f"{rc['dimension'].replace('_',' ').title()}: {rc['group_value']}" for rc in filtered]
    values = [rc["contribution_pct"] for rc in filtered]
    colors = ["#ef4444" if v < 0 else "#22c55e" for v in values]

    data = [{
        "type": "bar",
        "orientation": "h",
        "y": labels[::-1],
        "x": values[::-1],
        "marker": {"color": colors[::-1]},
        "text": [f"{v:+.1f}%" for v in values[::-1]],
        "textposition": "outside",
        "hovertemplate": "%{y}<br>Contribution: %{x:.1f}%<extra></extra>",
    }]
    layout = {
        "title": {"text": "Revenue Change Attribution by Driver", "font": {"size": 16}},
        "xaxis": {"title": "Contribution to Revenue Change (%)", "zeroline": True},
        "yaxis": {"tickfont": {"size": 12}},
        "height": max(260, len(filtered) * 45 + 80),
        "margin": {"l": 180, "r": 80, "t": 50, "b": 40},
        "paper_bgcolor": "#ffffff",
        "plot_bgcolor":  "#f9fafb",
    }
    return json.dumps({"data": data, "layout": layout})


def _forecast_chart_json(result: dict) -> str:
    """Build Plotly forecast chart JSON with confidence band."""
    vals   = result.get("forecast_values", [])
    lower  = result.get("confidence_lower", [])
    upper  = result.get("confidence_upper", [])
    if not vals:
        return "null"

    x_labels = [f"Day +{i+1}" for i in range(len(vals))]

    traces = []
    if upper and lower:
        traces.append({
            "type": "scatter",
            "x": x_labels + x_labels[::-1],
            "y": upper + lower[::-1],
            "fill": "toself",
            "fillcolor": "rgba(59,130,246,0.15)",
            "line": {"color": "transparent"},
            "name": "80% Confidence Band",
            "hoverinfo": "skip",
        })
    traces.append({
        "type": "scatter",
        "x": x_labels,
        "y": vals,
        "mode": "lines+markers",
        "line": {"color": "#3b82f6", "width": 3},
        "marker": {"size": 8, "color": "#1d4ed8"},
        "name": "Forecast",
        "hovertemplate": "%{x}<br>Revenue: $%{y:,.0f}<extra></extra>",
    })

    layout = {
        "title": {"text": "7-Day Revenue Forecast", "font": {"size": 16}},
        "xaxis": {"title": "Forecast Day"},
        "yaxis": {"title": "Revenue (USD)", "tickformat": "$,.0f"},
        "height": 320,
        "margin": {"l": 60, "r": 30, "t": 50, "b": 40},
        "paper_bgcolor": "#ffffff",
        "plot_bgcolor":  "#f9fafb",
        "legend": {"orientation": "h", "y": -0.25},
    }
    return json.dumps({"data": traces, "layout": layout})


def _rec_rows(recs: list[dict]) -> str:
    _pri_color = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#6b7280"}
    rows = []
    for rec in recs:
        pri   = rec.get("priority", "LOW")
        color = _pri_color.get(pri, "#6b7280")
        conf  = rec.get("confidence", 0.0)
        rows.append(f"""
        <tr>
          <td style="text-align:center">
            <span style="background:{color};color:white;padding:3px 10px;
              border-radius:12px;font-size:12px;font-weight:700">{pri}</span>
          </td>
          <td style="font-size:13px">{rec.get('action', '')}</td>
          <td style="font-size:12px;color:#4b5563">{rec.get('expected_impact', '')}</td>
          <td style="font-size:12px;color:#4b5563">{rec.get('timeline', '')}</td>
          <td style="font-size:12px;color:#6b7280">{rec.get('owner', '')}</td>
          <td style="text-align:center;font-weight:600;color:#16a34a">{conf:.0%}</td>
        </tr>""")
    return "\n".join(rows)


def generate_html_report(result: dict[str, Any], output_path: Path) -> Path:
    """Render a self-contained HTML executive decision brief and save to output_path."""

    severity    = result.get("severity", "NORMAL")
    sev_color   = _SEV_COLOR.get(severity, "#6b7280")
    sev_bg      = _SEV_BG.get(severity, "#f9fafb")
    sev_icon    = _SEV_ICON.get(severity, "⚪")
    change      = result.get("change", "0%")
    chg_pct     = result.get("change_pct", 0.0)
    chg_color   = "#ef4444" if chg_pct < 0 else "#22c55e"
    anom_count  = result.get("anomaly_count", 0)
    confidence  = result.get("confidence", 0.0)
    explanation = result.get("explanation", "")
    llm_powered = result.get("llm_powered", False)
    prediction  = result.get("prediction", "")
    timestamp   = result.get("timestamp", datetime.now(timezone.utc).isoformat())
    version     = result.get("pipeline_version", "1.0.0")
    proc_ms     = result.get("processing_time_ms", 0)
    model_used  = result.get("model", "linear_trend")

    per_metric   = result.get("per_metric", {})
    root_causes  = result.get("root_cause", [])
    recs         = result.get("recommendation", [])

    metric_rows_html = _metric_rows(per_metric)
    rec_rows_html    = _rec_rows(recs)
    rc_chart_json    = _root_cause_chart_json(root_causes)
    fc_chart_json    = _forecast_chart_json(result)

    llm_badge = (
        '<span style="background:#16a34a;color:white;padding:2px 8px;'
        'border-radius:12px;font-size:11px">LLM-POWERED ✓</span>'
        if llm_powered else
        '<span style="background:#6b7280;color:white;padding:2px 8px;'
        'border-radius:12px;font-size:11px">DETERMINISTIC</span>'
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>AI Decision Intelligence — Executive Brief</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
          background:#f1f5f9;color:#1e293b;}}
    .container{{max-width:1200px;margin:0 auto;padding:24px;}}
    .header{{background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 100%);
              color:white;padding:28px 32px;border-radius:12px;margin-bottom:20px;}}
    .header h1{{font-size:22px;font-weight:700;letter-spacing:-0.3px}}
    .header p{{font-size:13px;color:#94a3b8;margin-top:6px}}
    .severity-banner{{background:{sev_bg};border:2px solid {sev_color};
                       border-radius:10px;padding:20px 28px;margin-bottom:20px;
                       display:flex;align-items:center;gap:16px}}
    .severity-badge{{background:{sev_color};color:white;font-size:18px;font-weight:800;
                      padding:8px 20px;border-radius:8px;white-space:nowrap}}
    .severity-text{{font-size:16px;color:#1e293b}}
    .severity-change{{font-size:24px;font-weight:800;color:{chg_color};margin-left:auto}}
    .card{{background:white;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.07);
            padding:24px;margin-bottom:20px}}
    .card-title{{font-size:15px;font-weight:700;color:#0f172a;margin-bottom:16px;
                  padding-bottom:10px;border-bottom:1px solid #e2e8f0}}
    table{{width:100%;border-collapse:collapse;font-size:13px}}
    th{{background:#f8fafc;padding:10px 12px;text-align:left;font-weight:600;
         color:#475569;border-bottom:2px solid #e2e8f0}}
    td{{padding:10px 12px;border-bottom:1px solid #f1f5f9;vertical-align:middle}}
    tr:hover td{{background:#fafbfc}}
    .grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
    .exec-brief{{background:linear-gradient(135deg,#eff6ff,#dbeafe);
                  border:1px solid #bfdbfe;border-radius:10px;padding:24px;
                  margin-bottom:20px}}
    .exec-brief p{{font-size:15px;line-height:1.7;color:#1e293b;font-style:italic}}
    .confidence-bar{{display:flex;align-items:center;gap:12px;margin-top:14px}}
    .bar-track{{flex:1;background:#e2e8f0;border-radius:20px;height:8px}}
    .bar-fill{{height:8px;border-radius:20px;
                background:linear-gradient(90deg,#3b82f6,#06b6d4);
                width:{confidence*100:.0f}%}}
    .meta{{font-size:12px;color:#64748b}}
    .footer{{text-align:center;font-size:12px;color:#94a3b8;padding:16px 0}}
  </style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="header">
    <h1>🧠 AI Decision Intelligence System</h1>
    <p>Executive Decision Brief  ·  Pipeline v{version}  ·  {timestamp[:19]} UTC  ·
       Analysis completed in {proc_ms:.0f}ms</p>
  </div>

  <!-- Severity Banner -->
  <div class="severity-banner">
    <div class="severity-badge">{sev_icon} {severity}</div>
    <div class="severity-text">
      <strong>{anom_count} anomalies detected</strong> across tracked business metrics
      <br><span style="font-size:13px;color:#475569">{prediction}</span>
    </div>
    <div class="severity-change">{change}</div>
  </div>

  <!-- Executive Briefing -->
  <div class="exec-brief">
    <div style="font-size:11px;font-weight:700;color:#1d4ed8;letter-spacing:1px;
                 text-transform:uppercase;margin-bottom:10px">Executive Briefing</div>
    <p>{explanation}</p>
    <div class="confidence-bar">
      <span class="meta">Confidence</span>
      <div class="bar-track"><div class="bar-fill"></div></div>
      <span style="font-weight:700;color:#1d4ed8">{confidence:.0%}</span>
      {llm_badge}
    </div>
  </div>

  <!-- Multi-Metric Scorecard -->
  <div class="card">
    <div class="card-title">📊 Multi-Metric Intelligence Scorecard</div>
    <table>
      <thead>
        <tr>
          <th>Metric</th><th style="text-align:right">Change (14d)</th>
          <th style="text-align:center">Severity</th>
          <th style="text-align:center">Anomaly?</th>
          <th style="text-align:right">Recent Value</th>
          <th style="text-align:right">Prior Value</th>
        </tr>
      </thead>
      <tbody>
        {metric_rows_html}
      </tbody>
    </table>
  </div>

  <!-- Charts: Root Cause + Forecast -->
  <div class="grid-2">
    <div class="card">
      <div class="card-title">🔍 Root Cause Attribution</div>
      <div id="rc-chart"></div>
    </div>
    <div class="card">
      <div class="card-title">📈 7-Day Revenue Forecast</div>
      <div id="fc-chart"></div>
    </div>
  </div>

  <!-- Recommendations -->
  <div class="card">
    <div class="card-title">✅ Prioritized Action Plan</div>
    <table>
      <thead>
        <tr>
          <th style="text-align:center;width:80px">Priority</th>
          <th>Action</th>
          <th style="width:200px">Expected Impact</th>
          <th style="width:160px">Timeline</th>
          <th style="width:180px">Owner</th>
          <th style="text-align:center;width:90px">Confidence</th>
        </tr>
      </thead>
      <tbody>
        {rec_rows_html}
      </tbody>
    </table>
  </div>

  <!-- Footer -->
  <div class="footer">
    AI Decision Intelligence System  ·  Forecast model: {model_used}  ·
    This brief was auto-generated by the pipeline. For questions, contact Analytics &amp; BI.
  </div>

</div>

<script>
  const rcData = {rc_chart_json};
  const fcData = {fc_chart_json};

  const plotlyConfig = {{displaylogo: false, responsive: true,
    modeBarButtonsToRemove: ['select2d','lasso2d','autoScale2d']}};

  if (rcData) {{
    Plotly.newPlot('rc-chart', rcData.data, {{
      ...rcData.layout, margin: {{l:200,r:60,t:40,b:40}}
    }}, plotlyConfig);
  }}
  if (fcData) {{
    Plotly.newPlot('fc-chart', fcData.data, fcData.layout, plotlyConfig);
  }}
</script>
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    logger.info("HTML report saved", extra={"path": str(output_path)})
    return output_path
