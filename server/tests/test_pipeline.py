"""Integration tests for the full run_pipeline() orchestration."""
from __future__ import annotations

import pytest

from run_pipeline import run_pipeline


@pytest.fixture(scope="module")
def pipeline_output() -> dict:
    """Run the pipeline once and reuse the output across all tests in this module."""
    return run_pipeline()


# ── Output shape ─────────────────────────────────────────────────────────────

def test_output_has_all_required_keys(pipeline_output):
    expected = {
        "metric", "anomaly_detected", "severity", "change", "anomaly_count",
        "anomaly_dates", "root_cause", "prediction", "forecast_values",
        "forecast_confidence_lower", "forecast_confidence_upper",
        "recommendation", "confidence", "explanation", "llm_powered",
        "processing_time_ms", "timestamp", "pipeline_version",
    }
    assert expected.issubset(pipeline_output.keys())


# ── Types ────────────────────────────────────────────────────────────────────

def test_anomaly_detected_is_bool(pipeline_output):
    assert isinstance(pipeline_output["anomaly_detected"], bool)


def test_severity_is_valid(pipeline_output):
    assert pipeline_output["severity"] in ("CRITICAL", "WARNING", "NORMAL")


def test_confidence_in_valid_range(pipeline_output):
    confidence = pipeline_output["confidence"]
    assert 0.0 <= confidence <= 1.0


def test_forecast_values_is_list_of_floats(pipeline_output):
    values = pipeline_output["forecast_values"]
    assert isinstance(values, list)
    assert all(isinstance(v, (int, float)) for v in values)


def test_root_cause_is_list(pipeline_output):
    assert isinstance(pipeline_output["root_cause"], list)
    assert len(pipeline_output["root_cause"]) >= 1


def test_root_cause_items_have_driver_key(pipeline_output):
    for item in pipeline_output["root_cause"]:
        assert "driver" in item


def test_recommendation_is_list(pipeline_output):
    assert isinstance(pipeline_output["recommendation"], list)
    assert len(pipeline_output["recommendation"]) >= 1


def test_recommendation_items_have_priority(pipeline_output):
    for item in pipeline_output["recommendation"]:
        assert item["priority"] in ("HIGH", "MEDIUM", "LOW")


def test_explanation_is_nonempty_string(pipeline_output):
    explanation = pipeline_output["explanation"]
    assert isinstance(explanation, str)
    assert len(explanation) > 10


def test_processing_time_is_positive(pipeline_output):
    assert pipeline_output["processing_time_ms"] > 0


def test_timestamp_is_iso_format(pipeline_output):
    from datetime import datetime
    ts = pipeline_output["timestamp"]
    # Should not raise
    datetime.fromisoformat(ts.replace("Z", "+00:00"))


def test_pipeline_version_present(pipeline_output):
    assert isinstance(pipeline_output["pipeline_version"], str)
    assert len(pipeline_output["pipeline_version"]) > 0
