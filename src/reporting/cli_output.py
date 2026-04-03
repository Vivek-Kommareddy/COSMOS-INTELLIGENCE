"""Rich CLI output for the AI Decision Intelligence pipeline.

Renders a full-color, structured terminal report using the 'rich' library.
Designed to look impressive during live demos to executive audiences.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

try:
    from rich import box
    from rich.columns import Columns
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import print as rprint
    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False

from src.utils.logger import get_logger

logger = get_logger(__name__)

console = Console() if _RICH_AVAILABLE else None

# ── Severity colours ─────────────────────────────────────────────────────────
_SEV_STYLE = {
    "CRITICAL": "bold red",
    "WARNING":  "bold yellow",
    "NORMAL":   "bold green",
}
_SEV_ICON = {
    "CRITICAL": "🔴",
    "WARNING":  "🟡",
    "NORMAL":   "🟢",
}


def _change_style(pct: float) -> str:
    if pct < -10:
        return "bold red"
    if pct < 0:
        return "red"
    if pct > 10:
        return "bold green"
    if pct > 0:
        return "green"
    return "white"


def _fallback_print(result: dict[str, Any]) -> None:
    """Plain-text fallback when rich is not installed."""
    print("\n" + "=" * 70)
    print("  AI DECISION INTELLIGENCE — EXECUTIVE BRIEF")
    print("=" * 70)
    print(f"  Severity:  {result['severity']}")
    print(f"  Change:    {result['change']}")
    print(f"  Anomalies: {result['anomaly_count']}")
    print(f"\n  {result['explanation']}")
    print("\n  TOP RECOMMENDATIONS:")
    for i, rec in enumerate(result.get("recommendation", [])[:3], 1):
        print(f"  {i}. [{rec['priority']}] {rec['action'][:80]}")
    print("=" * 70 + "\n")


def render_cli_report(result: dict[str, Any]) -> None:
    """Render the full decision intelligence report to the terminal."""
    if not _RICH_AVAILABLE or console is None:
        _fallback_print(result)
        return

    severity   = result.get("severity", "NORMAL")
    sev_style  = _SEV_STYLE.get(severity, "white")
    sev_icon   = _SEV_ICON.get(severity, "⚪")
    timestamp  = result.get("timestamp", datetime.utcnow().isoformat())
    version    = result.get("pipeline_version", "1.0.0")
    proc_ms    = result.get("processing_time_ms", 0)

    console.print()
    console.rule("[bold blue]AI Decision Intelligence System[/bold blue] — Executive Brief", style="blue")
    console.print(
        f"[dim]Pipeline v{version}  |  Analysed: {timestamp[:19]}Z  |  "
        f"Processed in {proc_ms:.0f} ms[/dim]"
    )
    console.print()

    # ── Severity banner ──────────────────────────────────────────────────────
    banner = Panel(
        Text(
            f"{sev_icon}  {severity}  |  Revenue {result.get('change', 'N/A')} vs prior 14 days  "
            f"|  {result.get('anomaly_count', 0)} anomalies detected",
            style=sev_style,
            justify="center",
        ),
        box=box.DOUBLE_EDGE,
        style=sev_style,
    )
    console.print(banner)
    console.print()

    # ── Multi-metric scorecard ───────────────────────────────────────────────
    per_metric = result.get("per_metric", {})
    if per_metric:
        metric_table = Table(
            title="[bold]Multi-Metric Intelligence Scorecard[/bold]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )
        metric_table.add_column("Metric",          style="bold white",  min_width=18)
        metric_table.add_column("Change (14d)",     justify="right", min_width=12)
        metric_table.add_column("Severity",         min_width=10)
        metric_table.add_column("Anomaly?",         justify="center", min_width=9)
        metric_table.add_column("Recent Value",     justify="right", min_width=14)
        metric_table.add_column("Prior Value",      justify="right", min_width=14)

        for _col, mdata in per_metric.items():
            chg_pct = mdata.get("change_pct", 0.0)
            is_anom = mdata.get("anomaly_detected", False)
            msev    = mdata.get("severity", "NORMAL")
            metric_table.add_row(
                mdata.get("label", _col),
                Text(mdata.get("change", "0%"), style=_change_style(chg_pct)),
                Text(f"{_SEV_ICON.get(msev, '')} {msev}", style=_SEV_STYLE.get(msev, "white")),
                Text("YES" if is_anom else "no", style="bold red" if is_anom else "dim"),
                f"{mdata.get('recent_value', 0):>12,.1f}",
                f"{mdata.get('prior_value',  0):>12,.1f}",
            )

        console.print(metric_table)
        console.print()

    # ── Root causes ──────────────────────────────────────────────────────────
    root_causes = result.get("root_cause", [])
    if root_causes:
        rc_table = Table(
            title="[bold]Root Cause Attribution[/bold]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
        )
        rc_table.add_column("#",             justify="center", min_width=3)
        rc_table.add_column("Dimension",     min_width=12)
        rc_table.add_column("Group",         min_width=14)
        rc_table.add_column("Revenue Delta", justify="right", min_width=14)
        rc_table.add_column("Contribution",  justify="right", min_width=12)
        rc_table.add_column("Driver Summary", min_width=35)

        for idx, rc in enumerate(root_causes[:8], 1):
            delta = float(rc.get("delta", 0))
            cont  = float(rc.get("contribution_pct", 0))
            rc_table.add_row(
                str(idx),
                rc.get("dimension", "").replace("_", " ").title(),
                rc.get("group_value", ""),
                Text(f"${delta:>+,.0f}", style="red" if delta < 0 else "green"),
                Text(f"{cont:>+.1f}%",  style="red" if cont < 0  else "green"),
                Text(rc.get("driver", "")[:55], style="dim white"),
            )

        console.print(rc_table)
        console.print()

    # ── Forecast ─────────────────────────────────────────────────────────────
    forecast_pct  = result.get("forecast_pct_change", 0.0)
    forecast_vals = result.get("forecast_values", [])
    prediction    = result.get("prediction", "No forecast available")

    forecast_panel = Panel(
        f"[bold]7-Day Revenue Forecast[/bold]\n\n"
        f"  Outlook: [{'bold red' if forecast_pct < 0 else 'bold green'}]{prediction}[/]\n"
        f"  Values:  {' → '.join(f'${v:,.0f}' for v in forecast_vals[:7])}\n"
        f"  Model:   {result.get('model', 'linear_trend')}",
        box=box.ROUNDED,
        style="blue",
    )
    console.print(forecast_panel)
    console.print()

    # ── Recommendations ──────────────────────────────────────────────────────
    recs = result.get("recommendation", [])
    if recs:
        rec_table = Table(
            title="[bold]Prioritized Action Plan[/bold]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold yellow",
        )
        rec_table.add_column("Priority",    justify="center", min_width=8)
        rec_table.add_column("Action",      min_width=45)
        rec_table.add_column("Impact",      min_width=22)
        rec_table.add_column("Timeline",    min_width=16)
        rec_table.add_column("Owner",       min_width=18)
        rec_table.add_column("Confidence",  justify="center", min_width=10)

        _pri_style = {"HIGH": "bold red", "MEDIUM": "bold yellow", "LOW": "dim white"}
        for rec in recs:
            pri = rec.get("priority", "LOW")
            conf = rec.get("confidence", 0.0)
            rec_table.add_row(
                Text(pri, style=_pri_style.get(pri, "white")),
                Text(rec.get("action", "")[:70], style="white"),
                Text(rec.get("expected_impact", "")[:30], style="dim"),
                Text(rec.get("timeline", "")[:20], style="cyan"),
                Text(rec.get("owner", "")[:22], style="dim"),
                Text(f"{conf:.0%}", style="green"),
            )

        console.print(rec_table)
        console.print()

    # ── Executive briefing ───────────────────────────────────────────────────
    explanation  = result.get("explanation", "")
    confidence   = result.get("confidence", 0.0)
    llm_powered  = result.get("llm_powered", False)
    llm_badge    = "[bold green]LLM-POWERED[/bold green]" if llm_powered else "[dim]DETERMINISTIC[/dim]"

    exec_panel = Panel(
        f"[italic]{explanation}[/italic]\n\n"
        f"[dim]Confidence Score: [bold]{confidence:.0%}[/bold]  |  {llm_badge}[/dim]",
        title="[bold]Executive Briefing[/bold]",
        box=box.ROUNDED,
        style="cyan",
    )
    console.print(exec_panel)
    console.rule(style="blue")
    console.print()
