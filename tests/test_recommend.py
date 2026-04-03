"""Unit tests for src/recommendation/recommend.py."""
from __future__ import annotations

import pytest

from src.recommendation.recommend import generate_recommendations


def test_returns_nonempty_list(root_causes_campaign, anomaly_summary_critical):
    recs = generate_recommendations(root_causes_campaign, anomaly_summary_critical)
    assert len(recs) >= 1


def test_each_rec_has_required_keys(root_causes_campaign, anomaly_summary_critical):
    recs = generate_recommendations(root_causes_campaign, anomaly_summary_critical)
    for rec in recs:
        for key in ("action", "priority", "expected_impact", "timeline", "owner"):
            assert key in rec, f"Missing key '{key}' in recommendation"


def test_priority_values_are_valid(root_causes_campaign, anomaly_summary_critical):
    recs = generate_recommendations(root_causes_campaign, anomaly_summary_critical)
    for rec in recs:
        assert rec["priority"] in ("HIGH", "MEDIUM", "LOW")


def test_campaign_driver_produces_campaign_action(root_causes_campaign, anomaly_summary_critical):
    recs = generate_recommendations(root_causes_campaign, anomaly_summary_critical)
    actions = [r["action"].lower() for r in recs]
    assert any("campaign" in a or "Campaign_A" in a.title() for a in actions)


def test_critical_severity_produces_high_priority(root_causes_campaign, anomaly_summary_critical):
    recs = generate_recommendations(root_causes_campaign, anomaly_summary_critical)
    assert any(r["priority"] == "HIGH" for r in recs)


def test_sorted_high_first(root_causes_campaign, anomaly_summary_critical):
    recs = generate_recommendations(root_causes_campaign, anomaly_summary_critical)
    priorities = [r["priority"] for r in recs]
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    scores = [order[p] for p in priorities]
    assert scores == sorted(scores), "Recommendations are not sorted HIGH → MEDIUM → LOW"


def test_fallback_on_empty_causes(anomaly_summary_normal):
    recs = generate_recommendations([], anomaly_summary_normal)
    assert len(recs) >= 1
    assert recs[0]["priority"] == "LOW"


def test_region_driver_produces_region_action(anomaly_summary_critical):
    causes = [
        {
            "driver": "Region 'South' declined by 9000.00",
            "dimension": "region",
            "group_value": "South",
            "delta": -9000.0,
            "contribution_pct": -55.0,
        }
    ]
    recs = generate_recommendations(causes, anomaly_summary_critical)
    assert any("region" in r["action"].lower() or "South" in r["action"] for r in recs)
