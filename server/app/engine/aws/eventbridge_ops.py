"""AWS EventBridge operations: schedule and manage pipeline trigger rules."""
from __future__ import annotations

from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

from app.engine.utils.logger import get_logger

logger = get_logger(__name__)


def schedule_lambda(
    rule_name: str,
    lambda_arn: str,
    schedule_expression: str = "cron(0 3 * * ? *)",
    description: str = "AI Decision Intelligence pipeline — daily trigger",
    region: str = "us-east-1",
    enabled: bool = True,
) -> dict[str, Any]:
    """Create or update an EventBridge rule that triggers a Lambda function.

    Args:
        rule_name:           EventBridge rule name (must be unique in the account).
        lambda_arn:          Full ARN of the Lambda function to invoke.
        schedule_expression: Cron or rate expression.
                             Default: "cron(0 3 * * ? *)" = every day at 03:00 UTC.
                             Example: "rate(1 hour)" = every hour.
        description:         Human-readable rule description.
        region:              AWS region.
        enabled:             ENABLED or DISABLED state.

    Returns:
        Dict with RuleArn and target info.

    Note:
        The Lambda function must already have a resource-based policy granting
        events.amazonaws.com permission to invoke it. Call grant_invoke_permission()
        to set this up automatically.
    """
    events = boto3.client("events", region_name=region)

    try:
        rule_response = events.put_rule(
            Name=rule_name,
            ScheduleExpression=schedule_expression,
            State="ENABLED" if enabled else "DISABLED",
            Description=description,
        )
        rule_arn = rule_response["RuleArn"]

        events.put_targets(
            Rule=rule_name,
            Targets=[
                {
                    "Id": "AIDILambdaTarget",
                    "Arn": lambda_arn,
                    "Input": '{"trigger": "eventbridge-scheduled"}',
                }
            ],
        )

        logger.info(
            "EventBridge rule created/updated",
            extra={
                "rule_name": rule_name,
                "rule_arn": rule_arn,
                "schedule": schedule_expression,
                "enabled": enabled,
            },
        )
        return {"rule_arn": rule_arn, "rule_name": rule_name, "schedule": schedule_expression}

    except ClientError as exc:
        logger.error("Failed to create EventBridge rule", extra={"rule_name": rule_name, "error": str(exc)})
        raise


def grant_invoke_permission(
    lambda_arn: str,
    rule_arn: str,
    statement_id: str = "AIDIEventBridgeInvoke",
    region: str = "us-east-1",
) -> None:
    """Add a resource-based policy to the Lambda allowing EventBridge to invoke it.

    This is required before EventBridge can trigger the function.
    Safe to call multiple times — ignores ResourceConflictException.
    """
    lam = boto3.client("lambda", region_name=region)
    try:
        lam.add_permission(
            FunctionName=lambda_arn,
            StatementId=statement_id,
            Action="lambda:InvokeFunction",
            Principal="events.amazonaws.com",
            SourceArn=rule_arn,
        )
        logger.info("Lambda invoke permission granted for EventBridge", extra={"lambda_arn": lambda_arn})
    except lam.exceptions.ResourceConflictException:
        logger.info("Lambda invoke permission already exists — skipping", extra={"statement_id": statement_id})
    except ClientError as exc:
        logger.error("Failed to grant Lambda permission", extra={"error": str(exc)})
        raise


def disable_rule(rule_name: str, region: str = "us-east-1") -> None:
    """Disable an EventBridge rule (pause scheduling without deleting it)."""
    events = boto3.client("events", region_name=region)
    events.disable_rule(Name=rule_name)
    logger.info("EventBridge rule disabled", extra={"rule_name": rule_name})


def delete_rule(rule_name: str, region: str = "us-east-1") -> None:
    """Remove all targets from a rule, then delete it."""
    events = boto3.client("events", region_name=region)
    try:
        targets = events.list_targets_by_rule(Rule=rule_name).get("Targets", [])
        if targets:
            events.remove_targets(Rule=rule_name, Ids=[t["Id"] for t in targets])
        events.delete_rule(Name=rule_name)
        logger.info("EventBridge rule deleted", extra={"rule_name": rule_name})
    except ClientError as exc:
        logger.error("Failed to delete EventBridge rule", extra={"rule_name": rule_name, "error": str(exc)})
        raise
