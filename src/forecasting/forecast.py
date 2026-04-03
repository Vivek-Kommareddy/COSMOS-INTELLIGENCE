"""Multi-metric forecasting using linear regression (Prophet-ready upgrade path).

Forecasts three metrics for the next N days:
  - revenue         (primary KPI)
  - orders          (volume signal)
  - avg_order_value (ticket size signal)

Each metric uses a linear trend model with noise-derived confidence intervals.
When Prophet is available it is used automatically for the primary metric.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.utils.helpers import safe_pct_change
from src.utils.logger import get_logger

logger = get_logger(__name__)

_FORECAST_METRICS = ["revenue", "orders", "avg_order_value"]


def _linear_forecast(series: pd.Series, periods: int) -> dict[str, Any]:
    """Fit a linear trend and project forward with ±15% confidence interval."""
    y = series.values.astype(float)
    x = np.arange(len(y))

    # Weighted least-squares: recent data matters more
    weights = np.linspace(0.5, 1.0, len(y))
    slope, intercept = np.polyfit(x, y, 1, w=weights)

    future_x = np.arange(len(y), len(y) + periods)
    yhat = intercept + slope * future_x

    # Confidence interval: residual std ± extra margin for longer horizons
    residuals = y - (intercept + slope * x)
    resid_std = float(np.std(residuals))
    margin = resid_std * 1.5 + np.abs(yhat) * 0.05  # grows with forecast horizon

    lower = np.maximum(0.0, yhat - margin).round(2).tolist()
    upper = (yhat + margin).round(2).tolist()

    return {
        "forecast_values":    yhat.round(2).tolist(),
        "confidence_lower":   lower,
        "confidence_upper":   upper,
        "model":              "linear_trend",
    }


def _prophet_forecast(daily: pd.DataFrame, metric: str, periods: int) -> dict[str, Any]:
    """Use Facebook Prophet when available."""
    from prophet import Prophet  # noqa: PLC0415

    prophet_df = daily.rename(columns={"date": "ds", metric: "y"})
    model = Prophet(
        interval_width=0.80,
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=False,
        changepoint_prior_scale=0.15,
    )
    model.fit(prophet_df)
    future = model.make_future_dataframe(periods=periods)
    pred   = model.predict(future).tail(periods)

    return {
        "forecast_values":  pred["yhat"].round(2).tolist(),
        "confidence_lower": pred["yhat_lower"].round(2).tolist(),
        "confidence_upper": pred["yhat_upper"].round(2).tolist(),
        "model":            "prophet",
    }


def _forecast_one_metric(
    df: pd.DataFrame,
    metric: str,
    periods: int,
    use_prophet: bool = True,
) -> dict[str, Any]:
    """Forecast a single metric using the last 60 days of data for trend estimation."""
    daily_all = (
        df.groupby("date", as_index=False)[metric]
        .sum()
        .sort_values("date")
        .reset_index(drop=True)
    )
    # Use recent 60 days for trend — avoids distortion from historical patterns
    daily = daily_all.tail(60).reset_index(drop=True)

    forecast_data: dict[str, Any] = {}

    if use_prophet:
        try:
            forecast_data = _prophet_forecast(daily, metric, periods)
            logger.info("Prophet forecast", extra={"metric": metric, "periods": periods})
        except Exception as exc:
            logger.warning("Prophet unavailable; using linear trend",
                           extra={"metric": metric, "reason": str(exc)})
            forecast_data = _linear_forecast(daily[metric], periods)
    else:
        forecast_data = _linear_forecast(daily[metric], periods)

    # Summary phrase — compare forecast avg vs recent 14-day average (not last single day)
    forecast_values = forecast_data["forecast_values"]
    recent_avg = float(daily[metric].tail(14).mean()) if len(daily) >= 14 else float(daily[metric].iloc[-1])
    avg_future = float(np.mean(forecast_values)) if forecast_values else recent_avg
    pct = safe_pct_change(avg_future, recent_avg)

    direction = "decline" if pct < 0 else "increase"
    prediction = (
        f"Further {abs(pct):.1f}% {direction} expected over the next {periods} days"
        if abs(pct) > 0.5
        else f"Stable — less than 0.5% change expected over the next {periods} days"
    )

    return {
        "prediction":         prediction,
        "forecast_pct_change": round(pct, 2),
        **forecast_data,
    }


def forecast_revenue(df: pd.DataFrame, periods: int = 7) -> dict[str, Any]:
    """Forecast all tracked metrics for the next *periods* days.

    Returns a unified dict with:
      - Primary keys (revenue, backward-compatible):
          prediction, forecast_values, confidence_lower, confidence_upper,
          forecast_pct_change, model
      - Per-metric breakdowns under key 'per_metric'
    """
    if "avg_order_value" not in df.columns:
        df = df.copy()
        df["avg_order_value"] = np.where(
            df["orders"] > 0, df["revenue"] / df["orders"], 0.0
        )

    per_metric: dict[str, Any] = {}
    for metric in _FORECAST_METRICS:
        if metric not in df.columns:
            continue
        per_metric[metric] = _forecast_one_metric(df, metric, periods)

    # Primary metric = revenue
    primary = per_metric.get("revenue", {})

    result: dict[str, Any] = {
        "prediction":          primary.get("prediction", "Forecast unavailable"),
        "forecast_pct_change": primary.get("forecast_pct_change", 0.0),
        "forecast_values":     primary.get("forecast_values", []),
        "confidence_lower":    primary.get("confidence_lower", []),
        "confidence_upper":    primary.get("confidence_upper", []),
        "model":               primary.get("model", "linear_trend"),
        "per_metric":          per_metric,
    }

    logger.info(
        "Multi-metric forecast complete",
        extra={
            "metrics":        list(per_metric.keys()),
            "periods":        periods,
            "revenue_change": primary.get("forecast_pct_change", 0.0),
        },
    )
    return result
