"""CLI parser setup."""
from __future__ import annotations

import argparse

from aws_helper.constants import DEFAULT_REGION, VALID_SERVICES, VALID_SORT_ORDERS
from aws_helper.validators import (
    validate_command_id,
    validate_env,
    validate_instance_id,
    validate_region,
    validate_service,
    validate_since,
    validate_sort_order,
    validate_ticket_id,
)


def print_examples() -> None:
    print(
        """
mb-aws-helper usage examples

Environment
-----------
Print AWS exports for GitLab PROD:
  mb-aws-helper env prod --service gitlab

Print AWS exports for Artifactory PROD:
  mb-aws-helper env prod

Export values directly into your current shell:
  eval "$(mb-aws-helper env prod --service gitlab)"

Infrastructure
--------------
List Auto Scaling Groups for GitLab PROD:
  mb-aws-helper asgs prod --service gitlab

List EC2 instances for GitLab PROD:
  mb-aws-helper instances prod --service gitlab

List only running GitLab PROD instances:
  mb-aws-helper instances prod --service gitlab --state running

Filter instances by ASG substring:
  mb-aws-helper instances prod --service gitlab --asg rails

Filter instances by generic match:
  mb-aws-helper instances prod --service gitlab --match sidekiq

Show a quick summary:
  mb-aws-helper summary prod --service gitlab

Output JSON:
  mb-aws-helper summary prod --service gitlab --json

SSM
---
Open an interactive SSM session:
  mb-aws-helper ssm prod --service gitlab

Open SSM directly to a known instance:
  mb-aws-helper ssm prod --service gitlab --instance-id i-0123456789abcdef0

GitLab helpers
--------------
List deploy nodes:
  mb-aws-helper deploy-node list prod

Open deploy node with a new screen session:
  mb-aws-helper deploy-node open prod new

Recover an existing screen session on deploy node:
  mb-aws-helper deploy-node open prod recover

Open shell on the first rails-worker instance:
  mb-aws-helper rails-worker-shell prod

Artifactory helpers
-------------------
Run support bundle collection:
  mb-aws-helper support instances prod 123456 24h

Run support bundle collection for matching ASGs only:
  mb-aws-helper support instances prod 123456 24h --asg worker

Check SSM command status:
  mb-aws-helper support status prod 12345678-1234-1234-1234-1234567890ab

Watch support command status until completion:
  mb-aws-helper support status prod 12345678-1234-1234-1234-1234567890ab --watch

Notes
-----
- Default service is 'artifactory' for: env, asgs, instances, summary, ssm
- Valid environments include: prod, sandbox, int
- Aliases also accepted: dev -> sandbox, integration -> int
"""
    )


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mb-aws-helper",
        description="AWS helper for Artifactory and GitLab operations",
        epilog="""
Examples:
  mb-aws-helper env prod --service gitlab
  mb-aws-helper instances prod --service gitlab
  mb-aws-helper summary prod --service gitlab
  mb-aws-helper ssm prod --service gitlab
  mb-aws-helper deploy-node list prod

Run 'mb-aws-helper --examples' for a full list.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--region", type=validate_region, default=DEFAULT_REGION, help="AWS region")
    parser.add_argument("--verbose", action="store_true", help="Enable informational logging")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Show usage examples and exit",
    )

    subparsers = parser.add_subparsers(dest="command")

    env_parser = subparsers.add_parser("env", help="Print AWS_PROFILE/AWS_REGION exports")
    env_parser.add_argument("env", type=validate_env, help="prod | sandbox | int")
    env_parser.add_argument(
        "--service",
        type=validate_service,
        choices=VALID_SERVICES,
        default="artifactory",
        help="Service to generate AWS_PROFILE for (default: artifactory)",
    )

    asgs_parser = subparsers.add_parser("asgs", help="List Auto Scaling Groups")
    asgs_parser.add_argument("env", type=validate_env, help="prod | sandbox | int")
    asgs_parser.add_argument("--service", type=validate_service, choices=VALID_SERVICES, default="artifactory")
    asgs_parser.add_argument("--asg", dest="asg_match", help="Case-insensitive substring filter for ASG name")
    asgs_parser.add_argument("--json", action="store_true", help="Output JSON")

    instances_parser = subparsers.add_parser("instances", help="List EC2 instances in ASGs")
    instances_parser.add_argument("env", type=validate_env, help="prod | sandbox | int")
    instances_parser.add_argument("--service", type=validate_service, choices=VALID_SERVICES, default="artifactory")
    instances_parser.add_argument("--match", help="Case-insensitive substring filter for ASG name or instance ID")
    instances_parser.add_argument("--asg", dest="asg_match", help="Case-insensitive substring filter for ASG name")
    instances_parser.add_argument("--state", help="Filter by instance state, e.g. running")
    instances_parser.add_argument("--sort", type=validate_sort_order, choices=VALID_SORT_ORDERS, default="asc")
    instances_parser.add_argument("--json", action="store_true", help="Output JSON")

    summary_parser = subparsers.add_parser("summary", help="Show a quick environment summary")
    summary_parser.add_argument("env", type=validate_env, help="prod | sandbox | int")
    summary_parser.add_argument("--service", type=validate_service, choices=VALID_SERVICES, default="artifactory")
    summary_parser.add_argument("--asg", dest="asg_match", help="Case-insensitive substring filter for ASG name")
    summary_parser.add_argument("--json", action="store_true", help="Output JSON")

    support_parser = subparsers.add_parser("support", help="Artifactory support bundle helpers")
    support_sub = support_parser.add_subparsers(dest="support_command", required=True)

    support_instances_parser = support_sub.add_parser("instances", help="Run jfrog_support_collect.sh via SSM")
    support_instances_parser.add_argument("env", type=validate_env, help="prod | sandbox | int")
    support_instances_parser.add_argument("ticket_id", type=validate_ticket_id, help="Numeric ticket ID")
    support_instances_parser.add_argument("since", type=validate_since, help="Time window like 6h, 24h, 7d")
    support_instances_parser.add_argument("--asg", dest="asg_match", help="Filter target ASGs")
    support_instances_parser.add_argument("--no-dry-run", action="store_true", help="Run without --dry-run")

    support_status_parser = support_sub.add_parser("status", help="Show status of an SSM CommandId")
    support_status_parser.add_argument("env", type=validate_env, help="prod | sandbox | int")
    support_status_parser.add_argument("command_id", type=validate_command_id, help="SSM CommandId")
    support_status_parser.add_argument("--json", action="store_true", help="Output JSON")
    support_status_parser.add_argument("--watch", action="store_true", help="Watch until finished")
    support_status_parser.add_argument("--interval", type=int, default=2, help="Polling interval in seconds")

    ssm_parser = subparsers.add_parser("ssm", help="Open SSM session to an instance")
    ssm_parser.add_argument("env", type=validate_env, help="prod | sandbox | int")
    ssm_parser.add_argument("--service", type=validate_service, choices=VALID_SERVICES, default="artifactory")
    ssm_parser.add_argument("--instance-id", type=validate_instance_id, help="Open SSM directly to this instance ID")
    ssm_parser.add_argument("--match", help="Case-insensitive substring filter for ASG name or instance ID")
    ssm_parser.add_argument("--asg", dest="asg_match", help="Case-insensitive substring filter for ASG name")
    ssm_parser.add_argument("--sort", type=validate_sort_order, choices=VALID_SORT_ORDERS, default="asc")

    deploy_parser = subparsers.add_parser("deploy-node", help="GitLab deploy-node helpers")
    deploy_sub = deploy_parser.add_subparsers(dest="deploy_command", required=True)

    deploy_list_parser = deploy_sub.add_parser("list", help="List GitLab deploy nodes")
    deploy_list_parser.add_argument("env", type=validate_env, help="prod | sandbox | int")
    deploy_list_parser.add_argument("--match", help="Case-insensitive substring filter for ASG name or instance ID")
    deploy_list_parser.add_argument("--asg", dest="asg_match", help="Case-insensitive substring filter for ASG name")
    deploy_list_parser.add_argument("--sort", type=validate_sort_order, choices=VALID_SORT_ORDERS, default="asc")
    deploy_list_parser.add_argument("--json", action="store_true", help="Output JSON")

    deploy_open_parser = deploy_sub.add_parser("open", help="Open GitLab deploy node session with screen")
    deploy_open_parser.add_argument("env", type=validate_env, help="prod | sandbox | int")
    deploy_open_parser.add_argument("mode", choices=["new", "recover"], help="new or recover")
    deploy_open_parser.add_argument("--instance-id", type=validate_instance_id, help="Open directly to this instance ID")
    deploy_open_parser.add_argument("--match", help="Case-insensitive substring filter for ASG name or instance ID")
    deploy_open_parser.add_argument("--asg", dest="asg_match", help="Case-insensitive substring filter for ASG name")
    deploy_open_parser.add_argument("--sort", type=validate_sort_order, choices=VALID_SORT_ORDERS, default="asc")

    rails_worker_parser = subparsers.add_parser(
        "rails-worker-shell",
        help="Open SSM shell on the first GitLab rails-worker instance",
    )
    rails_worker_parser.add_argument("env", type=validate_env, help="prod | sandbox | int")
    rails_worker_parser.add_argument("--asg", dest="asg_match", help="Case-insensitive substring filter for ASG name")
    rails_worker_parser.add_argument("--sort", type=validate_sort_order, choices=VALID_SORT_ORDERS, default="asc")

    return parser