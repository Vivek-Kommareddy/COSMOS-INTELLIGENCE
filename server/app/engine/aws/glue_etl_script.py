"""AWS Glue ETL script — runs inside the Glue Python Shell environment.

This script is uploaded to S3 and referenced when creating the Glue job.
It applies the same transformation logic as src/processing/transform.py
but reads from and writes to S3 directly.

Glue Job Parameters (set in AWS Console or via CLI):
  --INPUT_PATH   s3://your-bucket/raw/source.csv
  --OUTPUT_PATH  s3://your-bucket/processed/processed.csv

Upload this file to S3 before creating the Glue job:
  aws s3 cp src/aws/glue_etl_script.py s3://your-bucket/scripts/glue_etl_script.py
"""
from __future__ import annotations

import io
import sys

import boto3
import pandas as pd

# ── Parse Glue job arguments ─────────────────────────────────────────────────

def _get_args() -> dict[str, str]:
    """Parse --KEY VALUE pairs from sys.argv (Glue Python Shell convention)."""
    args: dict[str, str] = {}
    argv = sys.argv[1:]
    for i in range(0, len(argv) - 1, 2):
        if argv[i].startswith("--"):
            args[argv[i].lstrip("-")] = argv[i + 1]
    return args


# ── S3 helpers ───────────────────────────────────────────────────────────────

def _read_csv_from_s3(s3_uri: str) -> pd.DataFrame:
    """Download a CSV from S3 and return as a DataFrame."""
    bucket, key = s3_uri.replace("s3://", "").split("/", 1)
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=bucket, Key=key)
    return pd.read_csv(io.BytesIO(obj["Body"].read()))


def _write_csv_to_s3(df: pd.DataFrame, s3_uri: str) -> None:
    """Serialise DataFrame to CSV and upload to S3."""
    bucket, key = s3_uri.replace("s3://", "").split("/", 1)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=buffer.getvalue().encode("utf-8"),
        ServerSideEncryption="AES256",
        ContentType="text/csv",
    )
    print(f"[Glue ETL] Written {len(df)} rows to {s3_uri}")


# ── Transformation logic (mirrors src/processing/transform.py) ───────────────

_REQUIRED_COLUMNS = ["date", "region", "product", "category", "revenue", "orders", "campaign"]
_CATEGORICAL = ["region", "product", "category", "campaign"]
_NUMERIC = ["revenue", "orders"]


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Apply canonical schema cleaning and aggregation."""
    clean = df.copy()

    for col in _REQUIRED_COLUMNS:
        if col not in clean.columns:
            clean[col] = None

    clean["date"] = pd.to_datetime(clean["date"], errors="coerce")
    clean = clean.dropna(subset=["date"])

    for col in _NUMERIC:
        clean[col] = pd.to_numeric(clean[col], errors="coerce").fillna(0.0)

    for col in _CATEGORICAL:
        clean[col] = clean[col].fillna("Unknown")

    grouped = (
        clean.groupby(["date", "region", "product", "category", "campaign"], as_index=False)
        .agg(revenue=("revenue", "sum"), orders=("orders", "sum"))
        .sort_values("date")
        .reset_index(drop=True)
    )
    return grouped


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    args = _get_args()
    input_path = args.get("INPUT_PATH") or args.get("input_path")
    output_path = args.get("OUTPUT_PATH") or args.get("output_path")

    if not input_path or not output_path:
        print("Usage: glue_etl_script.py --INPUT_PATH s3://... --OUTPUT_PATH s3://...")
        sys.exit(1)

    print(f"[Glue ETL] Reading from {input_path}")
    raw = _read_csv_from_s3(input_path)
    print(f"[Glue ETL] Loaded {len(raw)} rows")

    processed = transform(raw)
    print(f"[Glue ETL] Transformed to {len(processed)} aggregated rows")

    _write_csv_to_s3(processed, output_path)
    print("[Glue ETL] Job complete")


if __name__ == "__main__":
    main()
