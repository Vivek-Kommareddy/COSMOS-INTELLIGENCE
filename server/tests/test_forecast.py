"""Unit tests for src/forecasting/forecast.py."""
from __future__ import annotations

import pytest

from app.engine.forecasting.forecast import forecast_revenue


def test_forecast_returns_correct_number_of_values(base_df):
    result = forecast_revenue(base_df, periods=7)
    assert len(result["forecast_values"]) == 7


def test_forecast_keys_present(base_df):
    result = forecast_revenue(base_df, periods=7)
    for key in ("prediction", "forecast_values", "confidence_lower", "confidence_upper",
                "model", "forecast_pct_change"):
        assert key in result, f"Missing key: {key}"


def test_forecast_values_are_numeric(base_df):
    result = forecast_revenue(base_df, periods=7)
    for v in result["forecast_values"]:
        assert isinstance(v, (int, float))


def test_confidence_intervals_are_plausible(base_df):
    result = forecast_revenue(base_df, periods=7)
    for lo, hi in zip(result["confidence_lower"], result["confidence_upper"]):
        assert lo <= hi, f"Lower bound {lo} > upper bound {hi}"


def test_forecast_pct_change_is_float(base_df):
    result = forecast_revenue(base_df, periods=7)
    assert isinstance(result["forecast_pct_change"], float)


def test_prediction_phrase_mentions_direction(base_df):
    result = forecast_revenue(base_df, periods=7)
    prediction = result["prediction"]
    assert "drop" in prediction or "increase" in prediction


def test_custom_periods(base_df):
    result = forecast_revenue(base_df, periods=14)
    assert len(result["forecast_values"]) == 14
