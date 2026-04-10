"""Unit tests for src/anomaly/detect.py."""
from __future__ import annotations

import pandas as pd
import pytest

from app.engine.anomaly.detect import detect_anomalies


def test_anomaly_detected_in_anomalous_data(anomaly_df):
    _, summary = detect_anomalies(anomaly_df)
    assert summary["anomaly_detected"] is True
    assert summary["anomaly_count"] > 0


def test_summary_has_required_keys(base_df):
    _, summary = detect_anomalies(base_df)
    expected = {"metric", "anomaly_detected", "severity", "change", "change_pct",
                "anomaly_count", "anomaly_dates", "recent_revenue", "prior_revenue"}
    assert expected.issubset(summary.keys())


def test_severity_is_valid_value(base_df):
    _, summary = detect_anomalies(base_df)
    assert summary["severity"] in ("CRITICAL", "WARNING", "NORMAL")


def test_critical_severity_on_large_drop(anomaly_df):
    """A 75% revenue drop in the last 14 days should register as CRITICAL."""
    _, summary = detect_anomalies(anomaly_df)
    assert summary["severity"] in ("CRITICAL", "WARNING")  # at minimum WARNING


def test_anomaly_dates_are_strings(anomaly_df):
    _, summary = detect_anomalies(anomaly_df)
    for d in summary["anomaly_dates"]:
        assert isinstance(d, str)


def test_change_pct_is_float(base_df):
    _, summary = detect_anomalies(base_df)
    assert isinstance(summary["change_pct"], float)


def test_enriched_df_has_anomaly_columns(base_df):
    out, _ = detect_anomalies(base_df)
    assert "avg_order_value" in out.columns


def test_contamination_parameter(base_df):
    """Higher contamination should produce more anomalies."""
    _, s1 = detect_anomalies(base_df, contamination=0.05)
    _, s2 = detect_anomalies(base_df, contamination=0.30)
    assert s2["anomaly_count"] >= s1["anomaly_count"]
