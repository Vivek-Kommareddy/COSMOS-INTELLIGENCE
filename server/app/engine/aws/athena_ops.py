"""AWS Athena operations: execute SQL queries and retrieve results as DataFrames."""
from __future__ import annotations

import io
import time
from typing import Any, Optional

import boto3
import pandas as pd
from botocore.exceptions import ClientError

from app.engine.utils.logger import get_logger

logger = get_logger(__name__)

_TERMINAL_STATES = {"SUCCEEDED", "FAILED", "CANCELLED"}


def run_athena_query(
    query: str,
    database: str,
    output_location: str,
    region: str = "us-east-1",
    poll_seconds: float = 2.0,
    timeout_seconds: float = 60.0,
    workgroup: str = "primary",
) -> dict[str, str]:
    """Execute an Athena SQL query and wait for completion.

    Args:
        query:           SQL string to execute.
        database:        Athena database name.
        output_location: S3 URI where Athena writes results (e.g. s3://bucket/athena-output/).
        region:          AWS region.
        poll_seconds:    Seconds between status polls.
        timeout_seconds: Maximum wait time in seconds.
        workgroup:       Athena workgroup (default "primary").

    Returns:
        {"query_execution_id": str, "state": "SUCCEEDED"}

    Raises:
        TimeoutError:  Query did not finish within *timeout_seconds*.
        RuntimeError:  Query ended in FAILED or CANCELLED state.
    """
    athena = boto3.client("athena", region_name=region)

    try:
        response = athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={"Database": database},
            ResultConfiguration={"OutputLocation": output_location},
            WorkGroup=workgroup,
        )
    except ClientError as exc:
        logger.error("Failed to start Athena query", extra={"error": str(exc)})
        raise

    qid = response["QueryExecutionId"]
    logger.info("Athena query started", extra={"query_execution_id": qid})

    deadline = time.time() + timeout_seconds
    while True:
        if time.time() > deadline:
            athena.stop_query_execution(QueryExecutionId=qid)
            raise TimeoutError(f"Athena query {qid} did not complete within {timeout_seconds}s")

        execution = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]
        state = execution["Status"]["State"]

        if state in _TERMINAL_STATES:
            break

        time.sleep(poll_seconds)

    if state == "FAILED":
        reason = execution["Status"].get("StateChangeReason", "Unknown reason")
        raise RuntimeError(f"Athena query {qid} FAILED: {reason}")
    if state == "CANCELLED":
        raise RuntimeError(f"Athena query {qid} was CANCELLED")

    logger.info("Athena query succeeded", extra={"query_execution_id": qid})
    return {"query_execution_id": qid, "state": state}


def get_query_results_as_dataframe(
    query_execution_id: str,
    region: str = "us-east-1",
    max_rows: int = 10_000,
) -> pd.DataFrame:
    """Fetch Athena query results and return as a pandas DataFrame.

    Args:
        query_execution_id: ID returned by run_athena_query.
        region:             AWS region.
        max_rows:           Safety limit on returned rows.

    Returns:
        pandas DataFrame with query results.
    """
    athena = boto3.client("athena", region_name=region)

    rows: list[list[str]] = []
    header: Optional[list[str]] = None
    next_token: Optional[str] = None

    while True:
        kwargs: dict[str, Any] = {
            "QueryExecutionId": query_execution_id,
            "MaxResults": min(1000, max_rows - len(rows)),
        }
        if next_token:
            kwargs["NextToken"] = next_token

        response = athena.get_query_results(**kwargs)
        result_set = response["ResultSet"]

        for i, row in enumerate(result_set["Rows"]):
            values = [col.get("VarCharValue", "") for col in row["Data"]]
            if i == 0 and header is None:
                header = values
            else:
                rows.append(values)

        if len(rows) >= max_rows:
            logger.warning("Athena results truncated at max_rows", extra={"max_rows": max_rows})
            break

        next_token = response.get("NextToken")
        if not next_token:
            break

    df = pd.DataFrame(rows, columns=header or [])
    logger.info("Athena results fetched", extra={"rows": len(df), "columns": list(df.columns)})
    return df


def query_and_fetch(
    query: str,
    database: str,
    output_location: str,
    region: str = "us-east-1",
    timeout_seconds: float = 60.0,
) -> pd.DataFrame:
    """Convenience wrapper: execute a query and immediately return the results as a DataFrame."""
    result = run_athena_query(
        query=query,
        database=database,
        output_location=output_location,
        region=region,
        timeout_seconds=timeout_seconds,
    )
    return get_query_results_as_dataframe(result["query_execution_id"], region=region)
