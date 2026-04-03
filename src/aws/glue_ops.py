"""AWS Glue operations: start ETL jobs and poll for completion."""
from __future__ import annotations

import time
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

from src.utils.logger import get_logger

logger = get_logger(__name__)

_TERMINAL_STATES = {"SUCCEEDED", "FAILED", "ERROR", "STOPPED", "TIMEOUT"}


def start_glue_job(
    job_name: str,
    region: str = "us-east-1",
    arguments: Optional[dict[str, str]] = None,
) -> str:
    """Start an existing AWS Glue job run.

    Args:
        job_name:  Name of the Glue job (must already exist in AWS Glue console).
        region:    AWS region.
        arguments: Optional key-value pairs passed to the Glue job as --arg-name.
                   Example: {"--INPUT_PATH": "s3://bucket/raw/", "--OUTPUT_PATH": "s3://bucket/processed/"}

    Returns:
        The JobRunId string.
    """
    glue = boto3.client("glue", region_name=region)
    kwargs: dict[str, Any] = {"JobName": job_name}
    if arguments:
        kwargs["Arguments"] = arguments

    try:
        response = glue.start_job_run(**kwargs)
        run_id = response["JobRunId"]
        logger.info("Glue job started", extra={"job_name": job_name, "run_id": run_id})
        return run_id
    except ClientError as exc:
        logger.error("Failed to start Glue job", extra={"job_name": job_name, "error": str(exc)})
        raise


def wait_for_glue_job(
    job_name: str,
    run_id: str,
    region: str = "us-east-1",
    poll_seconds: float = 10.0,
    timeout_seconds: float = 600.0,
) -> dict[str, Any]:
    """Poll a Glue job run until it reaches a terminal state.

    Args:
        job_name:        Glue job name.
        run_id:          JobRunId returned by start_glue_job.
        region:          AWS region.
        poll_seconds:    Seconds between status polls.
        timeout_seconds: Maximum wait time before raising TimeoutError.

    Returns:
        Final job run status dict from AWS: {"State": ..., "ErrorMessage": ..., ...}

    Raises:
        TimeoutError: If the job does not complete within *timeout_seconds*.
        RuntimeError: If the job ends in FAILED / ERROR / STOPPED / TIMEOUT state.
    """
    glue = boto3.client("glue", region_name=region)
    deadline = time.time() + timeout_seconds

    while True:
        if time.time() > deadline:
            raise TimeoutError(
                f"Glue job '{job_name}' run '{run_id}' did not complete within {timeout_seconds}s"
            )

        try:
            run_info = glue.get_job_run(JobName=job_name, RunId=run_id)["JobRun"]
        except ClientError as exc:
            logger.error("Failed to poll Glue job", extra={"run_id": run_id, "error": str(exc)})
            raise

        state = run_info["JobRunState"]
        logger.info("Glue job status", extra={"job_name": job_name, "run_id": run_id, "state": state})

        if state in _TERMINAL_STATES:
            if state != "SUCCEEDED":
                error_msg = run_info.get("ErrorMessage", "No error message returned")
                raise RuntimeError(
                    f"Glue job '{job_name}' ended with state '{state}': {error_msg}"
                )
            return run_info

        time.sleep(poll_seconds)


def run_glue_job_sync(
    job_name: str,
    region: str = "us-east-1",
    arguments: Optional[dict[str, str]] = None,
    timeout_seconds: float = 600.0,
) -> dict[str, Any]:
    """Convenience wrapper: start a Glue job and wait for it to complete.

    Returns the final run status dict.
    """
    run_id = start_glue_job(job_name, region=region, arguments=arguments)
    return wait_for_glue_job(job_name, run_id, region=region, timeout_seconds=timeout_seconds)
