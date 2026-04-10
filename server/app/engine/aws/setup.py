"""AWS infrastructure bootstrap script.

Run this once to provision all Phase 2 AWS resources:
  S3 bucket (with versioning + encryption)
  Athena database + table
  EventBridge rule
  Lambda resource policy (invoke permission)

Usage:
  python -m app.engine.aws.setup --bucket my-bucket --region us-east-1 --lambda-arn arn:aws:lambda:...
"""
from __future__ import annotations

import argparse
import sys

import boto3
from botocore.exceptions import ClientError

from app.engine.utils.logger import get_logger

logger = get_logger(__name__)


# ── S3 ───────────────────────────────────────────────────────────────────────

def create_s3_bucket(bucket: str, region: str) -> str:
    """Create an S3 bucket with SSE-S3 encryption, versioning, and blocked public access."""
    s3 = boto3.client("s3", region_name=region)

    # Create bucket (us-east-1 has no LocationConstraint requirement).
    try:
        if region == "us-east-1":
            s3.create_bucket(Bucket=bucket)
        else:
            s3.create_bucket(
                Bucket=bucket,
                CreateBucketConfiguration={"LocationConstraint": region},
            )
        logger.info("S3 bucket created", extra={"bucket": bucket, "region": region})
    except s3.exceptions.BucketAlreadyOwnedByYou:
        logger.info("S3 bucket already exists and is owned by you — skipping creation", extra={"bucket": bucket})
    except ClientError as exc:
        logger.error("S3 bucket creation failed", extra={"error": str(exc)})
        raise

    # Block all public access.
    s3.put_public_access_block(
        Bucket=bucket,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )

    # Enable SSE-S3 default encryption.
    s3.put_bucket_encryption(
        Bucket=bucket,
        ServerSideEncryptionConfiguration={
            "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
        },
    )

    # Enable versioning.
    s3.put_bucket_versioning(
        Bucket=bucket,
        VersioningConfiguration={"Status": "Enabled"},
    )

    logger.info("S3 bucket configured (public access blocked, SSE-S3, versioning enabled)", extra={"bucket": bucket})
    return f"arn:aws:s3:::{bucket}"


def create_folder_structure(bucket: str, region: str) -> None:
    """Create logical folder prefixes in the bucket."""
    s3 = boto3.client("s3", region_name=region)
    for prefix in ["raw/", "processed/", "athena-output/", "lambda-package/"]:
        s3.put_object(Bucket=bucket, Key=prefix, Body=b"")
    logger.info("S3 folder structure created", extra={"bucket": bucket})


# ── Athena ───────────────────────────────────────────────────────────────────

def create_athena_database(database: str, output_location: str, region: str) -> None:
    """Create Athena database if it does not exist."""
    athena = boto3.client("athena", region_name=region)
    athena.start_query_execution(
        QueryString=f"CREATE DATABASE IF NOT EXISTS `{database}`",
        ResultConfiguration={"OutputLocation": output_location},
    )
    logger.info("Athena database creation query submitted", extra={"database": database})


def create_athena_table(
    database: str,
    bucket: str,
    output_location: str,
    region: str,
) -> None:
    """Create the processed_sales Athena table pointing at the S3 processed/ prefix."""
    ddl = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS `{database}`.`processed_sales` (
        `date`     STRING,
        `region`   STRING,
        `product`  STRING,
        `category` STRING,
        `campaign` STRING,
        `revenue`  DOUBLE,
        `orders`   BIGINT
    )
    ROW FORMAT DELIMITED
    FIELDS TERMINATED BY ','
    STORED AS TEXTFILE
    LOCATION 's3://{bucket}/processed/'
    TBLPROPERTIES ('skip.header.line.count'='1')
    """
    athena = boto3.client("athena", region_name=region)
    athena.start_query_execution(
        QueryString=ddl,
        QueryExecutionContext={"Database": database},
        ResultConfiguration={"OutputLocation": output_location},
    )
    logger.info("Athena table creation query submitted", extra={"database": database, "table": "processed_sales"})


# ── EventBridge ──────────────────────────────────────────────────────────────

def setup_eventbridge(rule_name: str, lambda_arn: str, region: str) -> None:
    from app.engine.aws.eventbridge_ops import grant_invoke_permission, schedule_lambda  # noqa: PLC0415

    result = schedule_lambda(rule_name=rule_name, lambda_arn=lambda_arn, region=region)
    grant_invoke_permission(lambda_arn=lambda_arn, rule_arn=result["rule_arn"], region=region)
    logger.info("EventBridge rule configured and Lambda permission granted")


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bootstrap AWS infrastructure for AI Decision Intelligence"
    )
    parser.add_argument("--bucket", required=True, help="S3 bucket name (globally unique)")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--athena-database", default="ai_decision_intelligence")
    parser.add_argument("--lambda-arn", default=None, help="Lambda ARN for EventBridge setup")
    parser.add_argument("--eventbridge-rule", default="ai-decision-intelligence-daily")
    args = parser.parse_args()

    output_location = f"s3://{args.bucket}/athena-output/"

    print(f"\n[1/4] Creating S3 bucket: {args.bucket} in {args.region}")
    create_s3_bucket(args.bucket, args.region)
    create_folder_structure(args.bucket, args.region)

    print(f"[2/4] Creating Athena database: {args.athena_database}")
    create_athena_database(args.athena_database, output_location, args.region)

    print(f"[3/4] Creating Athena table: processed_sales")
    create_athena_table(args.athena_database, args.bucket, output_location, args.region)

    if args.lambda_arn:
        print(f"[4/4] Configuring EventBridge rule: {args.eventbridge_rule}")
        setup_eventbridge(args.eventbridge_rule, args.lambda_arn, args.region)
    else:
        print("[4/4] Skipping EventBridge setup (--lambda-arn not provided)")

    print("\nBootstrap complete.")
    print(f"  S3 bucket:        s3://{args.bucket}/")
    print(f"  Athena database:  {args.athena_database}")
    print(f"  Athena output:    {output_location}")
    if args.lambda_arn:
        print(f"  EventBridge rule: {args.eventbridge_rule} → {args.lambda_arn}")


if __name__ == "__main__":
    main()
