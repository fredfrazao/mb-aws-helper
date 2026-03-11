"""Main application entrypoint."""
from __future__ import annotations

import sys

from aws_helper.cli.parser import make_parser
from aws_helper.commands.artifactory import cmd_support_instances, cmd_support_status
from aws_helper.commands.common import cmd_asgs, cmd_env, cmd_instances, cmd_ssm, cmd_summary
from aws_helper.commands.gitlab import (
    cmd_gitlab_deploy_list,
    cmd_gitlab_deploy_session,
    cmd_gitlab_rails_worker_shell,
)
from aws_helper.constants import DEFAULT_REGION
from aws_helper.interactive.menu import interactive_menu
from aws_helper.utils.logging_utils import configure_logging


def main() -> None:
    parser = make_parser()

    if len(sys.argv) == 1:
        configure_logging()
        interactive_menu(DEFAULT_REGION)
        return

    args = parser.parse_args()
    configure_logging(verbose=args.verbose, debug=args.debug)

    if not getattr(args, "command", None):
        parser.print_help()
        raise SystemExit(1)

    if args.command == "env":
        cmd_env(args.env, args.service, args.region)
    elif args.command == "asgs":
        cmd_asgs(args.env, args.service, args.region, asg_match=args.asg_match, json_output=args.json)
    elif args.command == "instances":
        cmd_instances(
            args.env,
            args.service,
            args.region,
            match=args.match,
            asg_match=args.asg_match,
            state=args.state,
            sort_order=args.sort,
            json_output=args.json,
        )
    elif args.command == "summary":
        cmd_summary(args.env, args.service, args.region, asg_match=args.asg_match, json_output=args.json)
    elif args.command == "support":
        if args.support_command == "instances":
            cmd_support_instances(
                args.env,
                args.region,
                args.ticket_id,
                args.since,
                dry_run=not getattr(args, "no_dry_run", False),
                asg_match=args.asg_match,
            )
        elif args.support_command == "status":
            cmd_support_status(
                args.env,
                args.region,
                args.command_id,
                json_output=args.json,
                watch=args.watch,
                interval=args.interval,
            )
        else:
            parser.print_help()
            raise SystemExit(1)
    elif args.command == "ssm":
        cmd_ssm(
            args.env,
            args.service,
            args.region,
            instance_id=args.instance_id,
            match=args.match,
            asg_match=args.asg_match,
            sort_order=args.sort,
        )
    elif args.command == "deploy-node":
        if args.deploy_command == "list":
            cmd_gitlab_deploy_list(
                args.env,
                args.region,
                match=args.match,
                asg_match=args.asg_match,
                sort_order=args.sort,
                json_output=args.json,
            )
        elif args.deploy_command == "open":
            cmd_gitlab_deploy_session(
                args.env,
                args.region,
                mode=args.mode,
                instance_id=args.instance_id,
                match=args.match,
                asg_match=args.asg_match,
                sort_order=args.sort,
            )
        else:
            parser.print_help()
            raise SystemExit(1)
    elif args.command == "rails-worker-shell":
        cmd_gitlab_rails_worker_shell(args.env, args.region, asg_match=args.asg_match, sort_order=args.sort)
    else:
        parser.print_help()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
