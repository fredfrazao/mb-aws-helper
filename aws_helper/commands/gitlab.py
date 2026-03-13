"""GitLab-specific commands."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from aws_helper.aws.discovery import discover_asg_instances
from aws_helper.aws.logs import (
    GITLAB_DEPLOY_LOG_GROUP,
    build_deploy_hot_reload_query,
    run_logs_insights_query,
)
from aws_helper.output.renderers import render_table
from aws_helper.selection import select_instance
from aws_helper.ssm.session import (
    build_screen_remote_command,
    run_ssm_start_session,
    start_interactive_shell_session,
)
from aws_helper.utils.common import print_json


def get_gitlab_deploy_instances(
        env: str,
        region: str,
        match: Optional[str] = None,
        asg_match: Optional[str] = None,
        sort_order: str = "asc",
) -> List[Dict[str, Any]]:
    return discover_asg_instances(
        env=env,
        service="gitlab",
        region=region,
        asg_filter=lambda asg: (
                "deploy-node" in asg.get("AutoScalingGroupName", "")
                and "gitlab" in asg.get("AutoScalingGroupName", "")
        ),
        instance_state="running",
        name_match=match,
        asg_match=asg_match,
        sort_order=sort_order,
    )


def cmd_gitlab_deploy_list(
        env: str,
        region: str,
        match: Optional[str] = None,
        asg_match: Optional[str] = None,
        sort_order: str = "asc",
        json_output: bool = False,
) -> None:
    deploy_instances = get_gitlab_deploy_instances(env, region, match, asg_match, sort_order)

    if json_output:
        print_json(deploy_instances)
        return

    if not deploy_instances:
        print("# No running GitLab deploy-node instances found.")
        return

    print("# GitLab deploy-node instances\n")
    render_table(
        headers=[
            "ASG",
            "INSTANCE_ID",
            "STATE",
            "AZ",
            "PRIVATE_IP",
            "TYPE",
            "AMI",
            "LT_NAME",
            "LT_VER",
            "LAUNCH_TIME",
        ],
        rows=[
            [
                row["asg"],
                row["id"],
                row["state"],
                row["az"],
                row["private_ip"],
                row["instance_type"],
                row["image_id"],
                row["lt_name"],
                row["lt_version"],
                row["launch_time_str"],
            ]
            for row in deploy_instances
        ],
    )


def cmd_gitlab_deploy_session(
        env: str,
        region: str,
        mode: str = "new",
        instance_id: Optional[str] = None,
        match: Optional[str] = None,
        asg_match: Optional[str] = None,
        sort_order: str = "asc",
) -> None:
    deploy_instances = get_gitlab_deploy_instances(env, region, match, asg_match, sort_order)

    if not deploy_instances:
        print("# No running GitLab deploy-node instances found.")
        return

    chosen = select_instance(
        instances=deploy_instances,
        instance_id=instance_id,
        title="# GitLab deploy-node instances available:",
        prompt="Select deploy-node instance number: ",
    )

    print(f"\n# Opening GitLab deploy-node SSM session on {chosen['id']} with screen (mode={mode}):")
    run_ssm_start_session(
        instance_id=chosen["id"],
        env=env,
        service="gitlab",
        region=region,
        remote_command=build_screen_remote_command(mode),
    )


def cmd_gitlab_rails_worker_shell(
        env: str,
        region: str,
        asg_match: Optional[str] = None,
        sort_order: str = "asc",
) -> None:
    rails_worker_instances = discover_asg_instances(
        env=env,
        service="gitlab",
        region=region,
        asg_filter=lambda asg: (
                "gitlab" in asg.get("AutoScalingGroupName", "")
                and "rails-worker" in asg.get("AutoScalingGroupName", "")
        ),
        instance_state="running",
        asg_match=asg_match,
        sort_order=sort_order,
    )

    if not rails_worker_instances:
        print("# No running GitLab rails-worker instances found.")
        return

    chosen = rails_worker_instances[0]
    print(f"\n# Opening SSM shell on first rails-worker instance: {chosen['id']} ({chosen['asg']})\n")
    start_interactive_shell_session(
        instance_id=chosen["id"],
        env=env,
        service="gitlab",
        region=region,
    )


def cmd_gitlab_deploy_logs(
        env: str,
        region: str,
        since: str = "24h",
        limit: int = 100,
        json_output: bool = False,
) -> None:
    query = build_deploy_hot_reload_query(limit=limit)
    query_id, rows = run_logs_insights_query(
        env=env,
        region=region,
        service="gitlab",
        log_group_name=GITLAB_DEPLOY_LOG_GROUP,
        query_string=query,
        since=since,
    )

    if json_output:
        print_json(
            {
                "query_id": query_id,
                "log_group": GITLAB_DEPLOY_LOG_GROUP,
                "since": since,
                "rows": rows,
            }
        )
        return

    if not rows:
        print(f"# No deploy_hot_reload logs found in the last {since}.")
        print(f"# QueryId: {query_id}")
        return

    print("# GitLab deploy_hot_reload logs\n")
    print(f"Log group: {GITLAB_DEPLOY_LOG_GROUP}")
    print(f"Since:     {since}")
    print(f"QueryId:   {query_id}\n")

    render_table(
        headers=["TIMESTAMP", "MESSAGE"],
        rows=[
            [
                row.get("@timestamp", ""),
                row.get("@message", ""),
            ]
            for row in rows
        ],
    )