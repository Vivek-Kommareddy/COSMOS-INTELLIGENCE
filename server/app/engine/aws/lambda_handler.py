"""AWS Lambda handler — entry point when the pipeline runs in the cloud.

Deploy this file as part of the Lambda deployment package.
Handler string in AWS Lambda console: app.engine.aws.lambda_handler.handler
"""
from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone
from typing import Any


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda entry point.

    Args:
        event:   Lambda event dict (passed by EventBridge or manual invocation).
        context: Lambda context object (provides request_id, remaining time, etc.).

    Returns:
        Standard Lambda response with statusCode, body (JSON string), and metadata.

    The function is intentionally robust: pipeline failures are caught and returned
    as 500 responses with structured error details so EventBridge can trigger alarms.
    """
    request_id = getattr(context, "aws_request_id", "local")
    invoked_at = datetime.now(timezone.utc).isoformat()

    try:
        # Import here so Lambda layers / deployment packages are resolved at runtime.
        from run_pipeline import run_pipeline  # noqa: PLC0415

        result = run_pipeline()
        response_body = {
            "status": "success",
            "request_id": request_id,
            "invoked_at": invoked_at,
            "trigger": event.get("trigger", "eventbridge"),
            "result": result,
        }
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response_body),
        }

    except Exception as exc:
        error_body = {
            "status": "error",
            "request_id": request_id,
            "invoked_at": invoked_at,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        # Return 500 so Lambda marks the invocation as failed.
        # EventBridge + CloudWatch Alarms can then page on-call.
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(error_body),
        }
