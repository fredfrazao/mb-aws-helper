"""Artifactory-specific commands."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from aws_helper.aws.auth import get_client
from aws_helper.aws.discovery import discover_asg_instances
from aws_helper.constants import RUNNING_STATES
from aws_helper.utils.common import print_json


def extract_last_output_line(invocation: Dict[str, Any]) -> str:
    plugins = invocation.get("CommandPlugins", []) or []
    for plugin in plugins:
        output = plugin.get("Output", "") or ""
        lines = [line for line in output.splitlines() if line.strip()]
        if lines:
            return lines[-1]
    return ""


def get_command_invocations(env: str, region: str, command_id: str) -> List[Dict[str, Any]]:
    ssm_client = get_client(env, "artifactory", "ssm", region)
    paginator = ssm_client.get_paginator("list_command_invocations")

    summarized: List[Dict[str, Any]] = []
    for page in paginator.paginate(CommandId=command_id, Details=True):
        for invocation in page.get("CommandInvocations", []) or []:
            summarized.append(
                {
                    "instance_id": invocation.get("InstanceId"),
                    "status": invocation.get("Status"),
                    "status_details": invocation.get("StatusDetails"),
                    "document_name": invocation.get("DocumentName"),
                    "comment": invocation.get("Comment"),
                    "last_output_line": extract_last_output_line(invocation),
                }
            )
    return summarized


def cmd_support_instances(
    env: str,
    region: str,
    ticket_id: str,
    since: str,
    dry_run: bool = True,
    asg_match: Optional[str] = None,
) -> Optional[str]:
    target_instances = discover_asg_instances(
        env=env,
        service="artifactory",
        region=region,
        asg_filter=lambda asg: (
            asg.get("AutoScalingGroupName", "").startswith("artifactory-frontend-")
            or asg.get("AutoScalingGroupName", "").startswith("artifactory-worker-")
        ),
        instance_state="running",
        asg_match=asg_match,
        sort_order="asc",
    )

    target_instance_ids = [item["id"] for item in target_instances]
    if not target_instance_ids:
        print("# No running instances found in matching artifactory frontend/worker ASGs.")
        return None

    print("# Target instances:")
    for instance_id in target_instance_ids:
        print(f"  - {instance_id}")

    command = f"cd /artifactory && ./jfrog_support_collect.sh {ticket_id} {since}"
    if dry_run:
        command += " --dry-run"

    print(f"\n# Sending SSM command to run:\n#   {command}\n")

    ssm_client = get_client(env, "artifactory", "ssm", region)
    response = ssm_client.send_command(
        InstanceIds=target_instance_ids,
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [command]},
        Comment=f"JFrog support bundle for ticket {ticket_id}, since={since}, dry_run={dry_run}",
    )

    command_id_value = response.get("Command", {}).get("CommandId")
    print(f"# SSM CommandId: {command_id_value}")
    print(f"# Tip: python aws_tool.py --region {region} support status <env> <command-id>")
    print(f"# Tip: python aws_tool.py --region {region} support status <env> <command-id> --watch")
    return command_id_value


def cmd_support_status(
    env: str,
    region: str,
    command_id: str,
    json_output: bool = False,
    watch: bool = False,
    interval: int = 2,
) -> None:
    if watch:
        print("\n# Checking command status (live watch)...\n")
        try:
            while True:
                invocations = get_command_invocations(env, region, command_id)
                if not invocations:
                    print("# No command invocations found yet for this CommandId.")
                    time.sleep(interval)
                    continue

                if json_output:
                    print_json(invocations)
                else:
                    for invocation in invocations:
                        print(f"Instance: {invocation['instance_id']}")
                        print(f"Status:   {invocation['status']} ({invocation['status_details']})")
                        if invocation["last_output_line"]:
                            print(f"Last line: {invocation['last_output_line']}")
                        print("------")

                statuses = {invocation["status"] for invocation in invocations}
                if statuses.isdisjoint(RUNNING_STATES):
                    print("\n# Finished.\n")
                    break

                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n# Live watch interrupted by user (Ctrl+C).\n")
        return

    invocations = get_command_invocations(env, region, command_id)
    if json_output:
        print_json(invocations)
        return

    if not invocations:
        print("# No command invocations found for this CommandId.")
        print("# Make sure AWS_PROFILE and region match the ones used to send the command.")
        return

    print("# Command invocations:")
    for invocation in invocations:
        print(f"- Instance: {invocation['instance_id']}")
        print(f"  Status:   {invocation['status']} ({invocation['status_details']})")
        if invocation["last_output_line"]:
            print(f"  Last line of output: {invocation['last_output_line']}")
        print("")
