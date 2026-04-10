"""S3 operations: upload, download, and list with retry and error handling."""
from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.engine.utils.logger import get_logger

logger = get_logger(__name__)


def _s3_client(region: str = "us-east-1"):
    return boto3.client("s3", region_name=region)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def upload_file(
    local_path: Path,
    bucket: str,
    key: str,
    region: str = "us-east-1",
    extra_args: Optional[dict] = None,
) -> str:
    """Upload a local file to S3.

    Retries up to 3 times with exponential backoff on transient errors.

    Args:
        local_path: Absolute path to the local file.
        bucket:     S3 bucket name.
        key:        Destination object key (path inside the bucket).
        region:     AWS region.
        extra_args: Optional boto3 ExtraArgs (e.g. {"ServerSideEncryption": "AES256"}).

    Returns:
        Full S3 URI: s3://<bucket>/<key>
    """
    s3 = _s3_client(region)
    try:
        s3.upload_file(
            Filename=str(local_path),
            Bucket=bucket,
            Key=key,
            ExtraArgs=extra_args or {"ServerSideEncryption": "AES256"},
        )
        uri = f"s3://{bucket}/{key}"
        logger.info("S3 upload complete", extra={"uri": uri, "size_bytes": local_path.stat().st_size})
        return uri
    except ClientError as exc:
        logger.error("S3 upload failed", extra={"bucket": bucket, "key": key, "error": str(exc)})
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def download_file(
    bucket: str,
    key: str,
    local_path: Path,
    region: str = "us-east-1",
) -> Path:
    """Download an S3 object to a local file.

    Returns:
        *local_path* on success.
    """
    local_path.parent.mkdir(parents=True, exist_ok=True)
    s3 = _s3_client(region)
    try:
        s3.download_file(bucket, key, str(local_path))
        logger.info("S3 download complete", extra={"bucket": bucket, "key": key, "local_path": str(local_path)})
        return local_path
    except ClientError as exc:
        logger.error("S3 download failed", extra={"bucket": bucket, "key": key, "error": str(exc)})
        raise


def upload_dataframe_as_csv(
    df,  # pd.DataFrame — typed loosely to avoid mandatory import at module level
    bucket: str,
    key: str,
    region: str = "us-east-1",
) -> str:
    """Serialise a pandas DataFrame to CSV and upload directly to S3 (no tmp file)."""
    import pandas as pd  # noqa: PLC0415
    assert isinstance(df, pd.DataFrame)

    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    body = buffer.getvalue().encode("utf-8")

    s3 = _s3_client(region)
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ServerSideEncryption="AES256",
        ContentType="text/csv",
    )
    uri = f"s3://{bucket}/{key}"
    logger.info("DataFrame uploaded to S3 as CSV", extra={"uri": uri, "rows": len(df)})
    return uri


def list_objects(bucket: str, prefix: str = "", region: str = "us-east-1") -> list[str]:
    """Return a list of object keys under *prefix* in *bucket*."""
    s3 = _s3_client(region)
    paginator = s3.get_paginator("list_objects_v2")
    keys: list[str] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    logger.info("S3 list complete", extra={"bucket": bucket, "prefix": prefix, "count": len(keys)})
    return keys
