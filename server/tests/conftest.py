"""Shared pytest fixtures for all test modules."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="session")
def base_df() -> pd.DataFrame:
    """A clean 60-day synthetic dataset — no anomalies — for baseline tests."""
    rng = np.random.default_rng(0)
    dates = pd.date_range("2025-01-01", periods=60, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "region": rng.choice(["East", "West", "North", "South"], size=60),
            "product": rng.choice(["Laptop", "Chair", "T-Shirt"], size=60),
            "category": rng.choice(["Electronics", "Furniture", "Fashion"], size=60),
            "campaign": rng.choice(["Campaign_A", "Campaign_B", "None"], size=60),
            "revenue": rng.uniform(1_000, 5_000, size=60).round(2),
            "orders": rng.integers(20, 200, size=60),
        }
    )


@pytest.fixture(scope="session")
def anomaly_df(base_df) -> pd.DataFrame:
    """Dataset with a pronounced revenue drop in the last 14 days (clear anomaly signal)."""
    df = base_df.copy()
    df.loc[df.index[-14:], "revenue"] = (df.loc[df.index[-14:], "revenue"] * 0.25).round(2)
    return df


@pytest.fixture(scope="session")
def campaign_drop_df(base_df) -> pd.DataFrame:
    """Dataset where Campaign_A stopping drives the revenue drop."""
    df = base_df.copy()
    last_14 = df.index[-14:]
    # Campaign_A used to contribute revenue; simulate it stopping.
    df.loc[last_14 & df.index[df["campaign"] == "Campaign_A"], "revenue"] *= 0.1
    return df


@pytest.fixture
def anomaly_summary_critical() -> dict:
    return {
        "metric": "revenue",
        "anomaly_detected": True,
        "severity": "CRITICAL",
        "change": "-22.0%",
        "change_pct": -22.0,
        "anomaly_count": 5,
        "anomaly_dates": ["2025-02-15", "2025-02-20"],
        "recent_revenue": 78_000.0,
        "prior_revenue": 100_000.0,
    }


@pytest.fixture
def anomaly_summary_normal() -> dict:
    return {
        "metric": "revenue",
        "anomaly_detected": False,
        "severity": "NORMAL",
        "change": "+1.2%",
        "change_pct": 1.2,
        "anomaly_count": 0,
        "anomaly_dates": [],
        "recent_revenue": 101_200.0,
        "prior_revenue": 100_000.0,
    }


@pytest.fixture
def root_causes_campaign() -> list[dict]:
    return [
        {
            "driver": "Campaign 'Campaign_A' declined by 18500.00",
            "dimension": "campaign",
            "group_value": "Campaign_A",
            "delta": -18_500.0,
            "contribution_pct": -62.1,
        },
        {
            "driver": "Region 'West' declined by 7200.00",
            "dimension": "region",
            "group_value": "West",
            "delta": -7_200.0,
            "contribution_pct": -24.2,
        },
    ]
