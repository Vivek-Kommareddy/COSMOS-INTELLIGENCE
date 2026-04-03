"""Data ingestion: load from CSV or generate a rich enterprise synthetic dataset.

The synthetic generator produces 365 days of realistic retail/ecommerce data with:
  - 7 product categories, 18 SKUs, 4 regions, 3 sales channels, 3 campaigns
  - Derived signals: inventory_status, holiday_flag, discount_band, incident_flag, impressions
  - 4 injected causal scenarios in the final 90 days (the 'recent' analysis window):
      1. Campaign_A paused  -> revenue + orders decline (days -60 to -30)
      2. Electronics stockout -> category + region revenue drop (days -45 to -20)
      3. Shipping delay incident -> revenue compression on Web channel (days -25 to -10)
      4. Summer promo lift -> positive anomaly in Grocery/South (days -90 to -75)
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.utils.helpers import ensure_parent
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── Master reference data ────────────────────────────────────────────────────

_REGIONS = ["East", "West", "North", "South"]

_CATEGORY_PRODUCTS: dict[str, list[str]] = {
    "Electronics":  ["Laptop", "Smartphone", "Headphones", "Tablet"],
    "Furniture":    ["Office Chair", "Standing Desk"],
    "Fashion":      ["Running Shoes", "Winter Jacket", "T-Shirt"],
    "Grocery":      ["Organic Bundle", "Coffee Pack", "Snack Box"],
    "Sports":       ["Yoga Mat", "Dumbbell Set"],
    "Beauty":       ["Skincare Kit"],
    "Home":         ["Smart Lamp"],
}

_BASE_PRICES: dict[str, float] = {
    "Laptop": 950.0, "Smartphone": 650.0, "Headphones": 180.0, "Tablet": 420.0,
    "Office Chair": 320.0, "Standing Desk": 550.0,
    "Running Shoes": 110.0, "Winter Jacket": 190.0, "T-Shirt": 35.0,
    "Organic Bundle": 55.0, "Coffee Pack": 28.0, "Snack Box": 18.0,
    "Yoga Mat": 45.0, "Dumbbell Set": 130.0,
    "Skincare Kit": 85.0,
    "Smart Lamp": 70.0,
}

_CAMPAIGNS = ["Campaign_A", "Campaign_B", "Campaign_C", "None"]
_CHANNELS  = ["Web", "Mobile", "Retail"]

_HOLIDAYS: set[tuple[int, int]] = {
    (1, 1), (1, 15), (2, 19), (5, 27), (7, 4),
    (9, 2), (11, 28), (11, 29), (12, 24), (12, 25),
}

REQUIRED_COLUMNS = {
    "date", "region", "product", "category", "channel",
    "revenue", "orders", "impressions",
    "campaign", "inventory_status", "discount_band",
    "holiday_flag", "incident_flag",
}


def _holiday_flag(dates: pd.DatetimeIndex) -> np.ndarray:
    return np.array(
        [1 if (d.month, d.day) in _HOLIDAYS else 0 for d in dates],
        dtype=np.int8,
    )


def _generate_synthetic_dataset(rows: int = 365, seed: int = 42) -> pd.DataFrame:
    """Generate one year of realistic enterprise retail data with injected anomalies."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2025-01-01", periods=rows, freq="D")

    records: list[dict] = []
    for date in dates:
        for region in _REGIONS:
            n_products = int(rng.integers(2, 5))
            categories = list(_CATEGORY_PRODUCTS.keys())
            chosen_cats = rng.choice(categories, size=min(n_products, len(categories)), replace=False)
            for cat in chosen_cats:
                product = str(rng.choice(_CATEGORY_PRODUCTS[str(cat)]))
                campaign = str(rng.choice(_CAMPAIGNS, p=[0.40, 0.30, 0.20, 0.10]))
                channel  = str(rng.choice(_CHANNELS,  p=[0.50, 0.35, 0.15]))
                records.append({
                    "date": date,
                    "region": region,
                    "product": product,
                    "category": cat,
                    "channel": channel,
                    "campaign": campaign,
                })

    df = pd.DataFrame(records)
    n = len(df)
    base_prices = np.array([_BASE_PRICES[p] for p in df["product"]])

    dow_boost = np.where(df["date"].dt.dayofweek.isin([5, 6]), 1.25, 1.0)
    df["orders"] = np.maximum(
        1,
        (rng.normal(loc=40, scale=15, size=n) * dow_boost).astype(int),
    )
    df["impressions"] = (df["orders"] * rng.uniform(8, 25, size=n)).astype(int)

    uplift = np.select(
        [df["campaign"].eq("Campaign_A"), df["campaign"].eq("Campaign_B"),
         df["campaign"].eq("Campaign_C")],
        [1.30, 1.15, 1.05],
        default=1.0,
    )

    disc_choice = rng.choice(["none", "low", "medium", "high"], size=n, p=[0.50, 0.25, 0.15, 0.10])
    disc_factor = np.select(
        [disc_choice == "none", disc_choice == "low", disc_choice == "medium"],
        [1.0, 0.92, 0.82],
        default=0.70,
    )
    df["discount_band"] = disc_choice

    df["revenue"] = (df["orders"] * base_prices * uplift * disc_factor
                     * rng.uniform(0.88, 1.12, size=n)).round(2)
    df["holiday_flag"] = _holiday_flag(pd.DatetimeIndex(df["date"]))

    inv_choice = rng.choice(
        ["in_stock", "low_stock", "out_of_stock"], size=n, p=[0.87, 0.10, 0.03]
    )
    df["inventory_status"] = inv_choice
    oos_mask = df["inventory_status"].eq("out_of_stock")
    df.loc[oos_mask, "revenue"] = (df.loc[oos_mask, "revenue"] * 0.30).round(2)
    df.loc[oos_mask, "orders"]  = np.maximum(1, (df.loc[oos_mask, "orders"] * 0.30).astype(int))
    df["incident_flag"] = 0

    end_date = df["date"].max()

    # ─── Scenarios are timed so the RECENT 14-day window shows declining metrics,
    #     while the PRIOR 14-day window (days -27 to -14) was healthy.
    # Recent window: days -13 to 0
    # Prior  window: days -27 to -14

    # Scenario 1 (RECENT): Campaign_A stopped 12 days ago — drops revenue in East + West
    s1_mask = (
        df["date"].between(end_date - pd.Timedelta(days=12), end_date)
        & df["campaign"].eq("Campaign_A")
        & df["region"].isin(["East", "West"])
    )
    df.loc[s1_mask, "campaign"]    = "None"
    df.loc[s1_mask, "revenue"]     = (df.loc[s1_mask, "revenue"] * 0.32).round(2)
    df.loc[s1_mask, "orders"]      = np.maximum(1, (df.loc[s1_mask, "orders"] * 0.35).astype(int))
    df.loc[s1_mask, "impressions"] = np.maximum(10, (df.loc[s1_mask, "impressions"] * 0.40).astype(int))

    # Scenario 2 (RECENT): Electronics stockout in West + North (last 10 days)
    s2_mask = (
        df["date"].between(end_date - pd.Timedelta(days=10), end_date)
        & df["category"].eq("Electronics")
        & df["region"].isin(["West", "North"])
    )
    df.loc[s2_mask, "inventory_status"] = "out_of_stock"
    df.loc[s2_mask, "revenue"]          = (df.loc[s2_mask, "revenue"] * 0.10).round(2)
    df.loc[s2_mask, "orders"]           = np.maximum(1, (df.loc[s2_mask, "orders"] * 0.10).astype(int))
    df.loc[s2_mask, "incident_flag"]    = 1

    # Scenario 3 (RECENT): Shipping delay on Web channel (last 7 days)
    s3_mask = (
        df["date"].between(end_date - pd.Timedelta(days=7), end_date)
        & df["channel"].eq("Web")
    )
    df.loc[s3_mask, "revenue"]       = (df.loc[s3_mask, "revenue"] * 0.55).round(2)
    df.loc[s3_mask, "incident_flag"] = 1

    # Scenario 4 (PRIOR): Summer promo lift in Grocery/South (days -25 to -18)
    # Makes the prior window look strong, amplifying the recent decline contrast
    s4_mask = (
        df["date"].between(end_date - pd.Timedelta(days=25), end_date - pd.Timedelta(days=18))
        & df["category"].eq("Grocery")
        & df["region"].eq("South")
    )
    df.loc[s4_mask, "revenue"]  = (df.loc[s4_mask, "revenue"] * 2.20).round(2)
    df.loc[s4_mask, "orders"]   = (df.loc[s4_mask, "orders"] * 1.80).astype(int)
    df.loc[s4_mask, "campaign"] = "Campaign_A"

    df = df.sort_values("date").reset_index(drop=True)
    df["revenue"] = df["revenue"].clip(lower=0.01)
    df["orders"]  = df["orders"].clip(lower=1)

    logger.info(
        "Synthetic enterprise dataset generated",
        extra={
            "rows": len(df),
            "date_range": f"{df['date'].min().date()} to {df['date'].max().date()}",
            "scenarios_injected": 4,
            "total_revenue": round(float(df["revenue"].sum()), 2),
        },
    )
    return df


def load_or_create_raw(
    raw_path: Path,
    source_csv: Optional[Path] = None,
) -> pd.DataFrame:
    """Load source CSV or generate synthetic data if none exists."""
    ensure_parent(raw_path)

    if source_csv and Path(source_csv).exists():
        df = pd.read_csv(source_csv)
        logger.info("Loaded source CSV", extra={"path": str(source_csv), "rows": len(df)})
    elif raw_path.exists() and raw_path.stat().st_size > 0:
        df = pd.read_csv(raw_path)
        if not {"inventory_status", "impressions"}.issubset(df.columns):
            logger.info("Raw CSV missing enterprise columns — regenerating synthetic dataset")
            df = _generate_synthetic_dataset()
        else:
            logger.info("Loaded existing raw CSV", extra={"path": str(raw_path), "rows": len(df)})
    else:
        logger.info("No source CSV found — generating synthetic enterprise dataset")
        df = _generate_synthetic_dataset()

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        logger.warning(
            "Source CSV missing columns; filled during transform",
            extra={"missing": sorted(missing)},
        )

    df.to_csv(raw_path, index=False)
    return df
