"""GitLab-specific commands."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from aws_helper.aws.discovery import discover_asg_instances
from aws_helper.output.renderers import render_table
from aws_helper.selection import select_instance
from aws_helper.ssm.session import build_screen_remote_command, run_ssm_start_session, start_interactive_shell_session
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
        headers=["ASG", "INSTANCE_ID", "STATE", "AZ", "PRIVATE_IP", "TYPE", "AMI", "LT_NAME", "LT_VER", "LAUNCH_TIME"],
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
