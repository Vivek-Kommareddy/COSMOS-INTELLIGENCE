"""Unit tests for src/processing/transform.py."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.engine.processing.transform import REQUIRED_COLUMNS, transform_data


@pytest.fixture
def tmp_csv(tmp_path) -> Path:
    return tmp_path / "processed.csv"


def test_output_has_all_required_columns(base_df, tmp_csv):
    result = transform_data(base_df, tmp_csv)
    for col in REQUIRED_COLUMNS:
        assert col in result.columns, f"Missing column: {col}"


def test_output_sorted_by_date(base_df, tmp_csv):
    result = transform_data(base_df, tmp_csv)
    assert result["date"].is_monotonic_increasing


def test_revenue_is_numeric(base_df, tmp_csv):
    result = transform_data(base_df, tmp_csv)
    assert pd.api.types.is_numeric_dtype(result["revenue"])


def test_orders_is_numeric(base_df, tmp_csv):
    result = transform_data(base_df, tmp_csv)
    assert pd.api.types.is_numeric_dtype(result["orders"])


def test_no_null_revenue_after_transform(tmp_csv):
    df = pd.DataFrame(
        {
            "date": ["2025-01-01", "2025-01-02"],
            "region": ["East", "West"],
            "product": ["Laptop", "Chair"],
            "category": ["Electronics", "Furniture"],
            "campaign": ["Campaign_A", None],
            "revenue": [1000.0, None],
            "orders": [10, 5],
        }
    )
    result = transform_data(df, tmp_csv)
    assert result["revenue"].isna().sum() == 0


def test_missing_column_is_filled(tmp_csv):
    """If a column is missing entirely, transform should add it with null/default."""
    df = pd.DataFrame(
        {
            "date": ["2025-01-01"],
            "revenue": [500.0],
            "orders": [10],
        }
    )
    result = transform_data(df, tmp_csv)
    assert "campaign" in result.columns


def test_unparseable_dates_are_dropped(tmp_csv):
    df = pd.DataFrame(
        {
            "date": ["2025-01-01", "not-a-date", "2025-01-03"],
            "region": ["East", "East", "East"],
            "product": ["Laptop", "Laptop", "Laptop"],
            "category": ["Electronics", "Electronics", "Electronics"],
            "campaign": ["Campaign_A", "Campaign_A", "Campaign_A"],
            "revenue": [1000.0, 2000.0, 3000.0],
            "orders": [10, 20, 30],
        }
    )
    result = transform_data(df, tmp_csv)
    assert len(result) == 2  # one bad row dropped


def test_csv_is_persisted(base_df, tmp_csv):
    transform_data(base_df, tmp_csv)
    assert tmp_csv.exists()
    on_disk = pd.read_csv(tmp_csv)
    assert len(on_disk) > 0
