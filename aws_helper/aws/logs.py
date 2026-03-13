"""CloudWatch Logs Insights helpers."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from aws_helper.aws.auth import get_client
from aws_helper.utils.common import die

GITLAB_DEPLOY_LOG_GROUP = "/gitlab/gitlab-deploy-node"
GITLAB_DEPLOY_LOG_STREAM = "deploy_hot_reload"


def parse_since_to_seconds(value: str) -> int:
    """Convert a time window like 30m, 6h, or 7d into seconds."""
    normalized = value.strip().lower()

    if len(normalized) < 2:
        raise ValueError(f"Invalid since value '{value}'")

    unit = normalized[-1]

    try:
        amount = int(normalized[:-1])
    except ValueError as exc:
        raise ValueError(f"Invalid since value '{value}'") from exc

    if amount <= 0:
        raise ValueError(f"Since value must be greater than 0: '{value}'")

    if unit == "m":
        return amount * 60
    if unit == "h":
        return amount * 3600
    if unit == "d":
        return amount * 86400

    raise ValueError(f"Unsupported since unit in '{value}'")


def build_deploy_hot_reload_query(limit: int | None = None) -> str:
    """Build the CloudWatch Logs Insights query for deploy hot reload logs."""
    query = f"""
fields @timestamp, @message
| filter @logStream = "{GITLAB_DEPLOY_LOG_STREAM}"
| sort @timestamp desc
""".strip()

    if limit is not None and limit > 0:
        query += f"\n| limit {limit}"

    return query


def _query_results_to_rows(results: List[List[Dict[str, str]]]) -> List[Dict[str, str]]:
    """Convert CloudWatch Logs Insights result structure into flat row dicts."""
    rows: List[Dict[str, str]] = []

    for result in results:
        row: Dict[str, str] = {}
        for field in result:
            key = field.get("field", "")
            value = field.get("value", "")
            row[key] = value
        rows.append(row)

    return rows


def run_logs_insights_query(
        env: str,
        region: str,
        service: str,
        log_group_name: str,
        query_string: str,
        since: str,
        poll_interval: int = 2,
        timeout_seconds: int = 60,
) -> Tuple[str, List[Dict[str, str]]]:
    """Run a CloudWatch Logs Insights query and wait until completion."""
    client = get_client(env=env, service=service, client_name="logs", region=region)

    end_time = int(datetime.now(timezone.utc).timestamp())
    start_time = end_time - parse_since_to_seconds(since)

    response = client.start_query(
        logGroupName=log_group_name,
        startTime=start_time,
        endTime=end_time,
        queryString=query_string,
    )
    query_id = response["queryId"]

    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        result = client.get_query_results(queryId=query_id)
        status = result["status"]

        if status == "Complete":
            return query_id, _query_results_to_rows(result.get("results", []))

        if status in {"Failed", "Cancelled", "Timeout", "Unknown"}:
            die(f"CloudWatch Logs Insights query ended with status: {status}")
            raise RuntimeError("Unreachable")

        time.sleep(poll_interval)

    die("Timed out waiting for CloudWatch Logs Insights query to finish")
    raise RuntimeError("Unreachable")