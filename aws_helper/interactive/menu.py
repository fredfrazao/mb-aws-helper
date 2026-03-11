"""Interactive terminal menu."""
from __future__ import annotations

import argparse

from aws_helper.commands.artifactory import cmd_support_instances, cmd_support_status
from aws_helper.commands.common import cmd_asgs, cmd_env, cmd_instances, cmd_ssm, cmd_summary
from aws_helper.commands.gitlab import (
    cmd_gitlab_deploy_list,
    cmd_gitlab_deploy_session,
    cmd_gitlab_rails_worker_shell,
)
from aws_helper.validators import validate_command_id, validate_instance_id, validate_since, validate_ticket_id


def interactive_menu(region: str) -> None:
    print("=== AWS Tool Interactive Mode ===\n")

    service = None
    env = None

    while True:
        while service is None:
            print("Select service:")
            print("  1) Artifactory")
            print("  2) GitLab")
            print("  q) Exit")
            choice = input("Service [1-2/q]: ").strip().lower()

            if choice == "1":
                service = "artifactory"
            elif choice == "2":
                service = "gitlab"
            elif choice in ("q", "quit", "exit"):
                print("\nBye")
                return
            else:
                print("Invalid service choice.\n")

        while env is None:
            print("\nSelect environment:")
            print("  1) sandbox")
            print("  2) int")
            print("  3) prod")
            print("  b) Back to service")
            print("  q) Exit")
            choice = input("Env [1-3/b/q]: ").strip().lower()

            if choice == "1":
                env = "sandbox"
            elif choice == "2":
                env = "int"
            elif choice == "3":
                env = "prod"
            elif choice in ("b", "back"):
                service = None
                print("")
                break
            elif choice in ("q", "quit", "exit"):
                print("\nBye")
                return
            else:
                print("Invalid env choice.\n")

        if service is None or env is None:
            continue

        while True:
            print(f"\n# Selected: service={service}, env={env}, region={region}\n")
            print("Select action:")
            print("  1) Set AWS env (env)")
            print("  2) List ASGs")
            print("  3) List instances")
            print("  4) SSM session (select)")
            print("  5) SSM session by instance-id")
            print("  6) Environment summary")

            if service == "artifactory":
                print("  7) Run support bundle (jfrog_support_collect.sh)")
                print("  8) Watch support bundle status")
                max_action = 8
            else:
                print("  7) List GitLab deploy nodes")
                print("  8) GitLab deploy node (new screen session)")
                print("  9) GitLab deploy node (recover screen session)")
                print(" 10) GitLab rails-worker shell (first instance)")
                max_action = 10

            print("  b) Back to environment")
            print("  s) Change service")
            print("  e) Change environment")
            print("  q) Exit")

            choice = input(f"Action [1-{max_action}/b/s/e/q]: ").strip().lower()

            if choice in ("q", "quit", "exit"):
                print("\nBye")
                return
            if choice in ("b", "back"):
                env = None
                print("")
                break
            if choice == "s":
                service = None
                env = None
                print("")
                break
            if choice == "e":
                env = None
                print("")
                break

            try:
                if choice == "1":
                    cmd_env(env, service, region)
                elif choice == "2":
                    cmd_asgs(env, service, region)
                elif choice == "3":
                    cmd_instances(env, service, region)
                elif choice == "4":
                    cmd_ssm(env, service, region)
                elif choice == "5":
                    instance_id = validate_instance_id(input("Instance ID: ").strip())
                    cmd_ssm(env, service, region, instance_id=instance_id)
                elif choice == "6":
                    cmd_summary(env, service, region)
                elif choice == "7" and service == "artifactory":
                    ticket_id = validate_ticket_id(input("Ticket ID (numeric): ").strip())
                    since = validate_since(input("Since (e.g. 6h, 24h, 7d): ").strip())
                    dry_run = input("Dry run? [Y/n]: ").strip().lower() not in ("n", "no")
                    cmd_support_instances(env, region, ticket_id, since, dry_run=dry_run)
                elif choice == "8" and service == "artifactory":
                    command_id = validate_command_id(input("SSM CommandId: ").strip())
                    cmd_support_status(env, region, command_id, watch=True)
                elif choice == "7" and service == "gitlab":
                    cmd_gitlab_deploy_list(env, region)
                elif choice == "8" and service == "gitlab":
                    cmd_gitlab_deploy_session(env, region, mode="new")
                elif choice == "9" and service == "gitlab":
                    cmd_gitlab_deploy_session(env, region, mode="recover")
                elif choice == "10" and service == "gitlab":
                    cmd_gitlab_rails_worker_shell(env, region)
                else:
                    print("Invalid action choice.")
                    continue
            except KeyboardInterrupt:
                print("\n# Interrupted by user.\n")
                continue
            except argparse.ArgumentTypeError as exc:
                print(f"ERROR: {exc}")
                continue

            print("\n--- Action completed. ---\n")
