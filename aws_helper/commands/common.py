"""Generic commands shared by services."""
from __future__ import annotations

from typing import Optional

from aws_helper.aws.auth import resolve_profile
from aws_helper.aws.discovery import discover_asg_instances, get_asgs, summarize_asg, summarize_environment
from aws_helper.output.renderers import render_table
from aws_helper.selection import select_instance
from aws_helper.ssm.session import start_interactive_shell_session
from aws_helper.utils.common import casefold_contains, print_json


def cmd_env(env: str, service: str, region: str) -> None:
    profile = resolve_profile(env, service)
    print(f'export AWS_PROFILE="{profile}"')
    print(f'export AWS_REGION="{region}"')
    print(f'export AWS_DEFAULT_REGION="{region}"')
    print(f'echo "AWS_PROFILE set to {profile}"')


def cmd_asgs(
    env: str,
    service: str,
    region: str,
    asg_match: Optional[str] = None,
    json_output: bool = False,
) -> None:
    asgs = get_asgs(
        env,
        service,
        region,
        asg_filter=lambda asg: casefold_contains(asg.get("AutoScalingGroupName", ""), asg_match),
    )
    data = [summarize_asg(asg) for asg in asgs]
    data.sort(key=lambda item: item["asg"])

    if json_output:
        print_json(data)
        return

    if not data:
        print("# No Auto Scaling Groups found.")
        return

    print(f"# Auto Scaling Groups for service={service}\n")
    render_table(
        headers=["ASG", "MIN", "MAX", "DESIRED", "INSTANCES", "LT_NAME", "LT_VER", "MIXED_POLICY"],
        rows=[
            [
                item["asg"],
                item["min"],
                item["max"],
                item["desired"],
                item["instances"],
                item["lt_name"],
                item["lt_version"],
                "yes" if item["mixed_policy"] else "no",
            ]
            for item in data
        ],
    )


def cmd_instances(
    env: str,
    service: str,
    region: str,
    match: Optional[str] = None,
    asg_match: Optional[str] = None,
    state: Optional[str] = None,
    sort_order: str = "asc",
    json_output: bool = False,
) -> None:
    rows = discover_asg_instances(
        env=env,
        service=service,
        region=region,
        instance_state=state,
        name_match=match,
        asg_match=asg_match,
        sort_order=sort_order,
    )

    if json_output:
        print_json(rows)
        return

    if not rows:
        print("# No instances found in ASGs for this env/service/filter.")
        return

    print(f"# Instances in ASGs for service={service}\n")
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
            for row in rows
        ],
    )


def cmd_ssm(
    env: str,
    service: str,
    region: str,
    instance_id: Optional[str] = None,
    match: Optional[str] = None,
    asg_match: Optional[str] = None,
    sort_order: str = "asc",
) -> None:
    instances = discover_asg_instances(
        env=env,
        service=service,
        region=region,
        instance_state="running",
        name_match=match,
        asg_match=asg_match,
        sort_order=sort_order,
    )

    if not instances:
        print(f"# No running {service} instances found.")
        return

    chosen = select_instance(
        instances=instances,
        instance_id=instance_id,
        title=f"# {service.capitalize()} running instances available:",
        prompt="Select instance number to open SSM session: ",
    )

    print(f"\n# Opening interactive SSM shell to {chosen['id']}...\n")
    start_interactive_shell_session(
        instance_id=chosen["id"],
        env=env,
        service=service,
        region=region,
    )


def cmd_summary(
    env: str,
    service: str,
    region: str,
    asg_match: Optional[str] = None,
    json_output: bool = False,
) -> None:
    summary = summarize_environment(env=env, service=service, region=region, asg_match=asg_match)
    if json_output:
        print_json(summary)
        return

    print(f"# Environment summary for service={service}, env={env}, region={region}\n")
    print(f"ASGs:          {summary['asgs']}")
    print(f"Instances:     {summary['instances']}")
    print(f"Deploy nodes:  {summary['deploy_nodes']}\n")

    def _render_mapping(title: str, mapping):
        print(title)
        if not mapping:
            print("  - none")
        else:
            for key, value in mapping.items():
                print(f"  - {key}: {value}")
        print("")

    _render_mapping("Roles", summary["roles"])
    _render_mapping("Availability Zones", summary["availability_zones"])
    _render_mapping("Instance Types", summary["instance_types"])
    _render_mapping("AMIs", summary["amis"])
