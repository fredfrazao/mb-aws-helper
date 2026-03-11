"""SSM session helpers."""
from __future__ import annotations

import json
import os
import subprocess
from typing import Dict

from aws_helper.aws.auth import resolve_profile
from aws_helper.utils.common import die
from aws_helper.utils.logging_utils import LOG


def build_aws_env(env: str, service: str, region: str) -> Dict[str, str]:
    profile = resolve_profile(env, service)
    env_vars = os.environ.copy()
    env_vars["AWS_PROFILE"] = profile
    env_vars["AWS_REGION"] = region
    env_vars["AWS_DEFAULT_REGION"] = region
    return env_vars


def build_start_interactive_command_payload(command: str) -> str:
    return json.dumps({"command": [command]})


def run_ssm_start_session(
    instance_id: str,
    env: str,
    service: str,
    region: str,
    remote_command: str,
) -> None:
    env_vars = build_aws_env(env, service, region)
    params = build_start_interactive_command_payload(remote_command)

    LOG.info(
        "Opening SSM interactive session to instance=%s service=%s env=%s region=%s",
        instance_id,
        service,
        env,
        region,
    )
    LOG.debug("Remote command: %s", remote_command)

    try:
        result = subprocess.run(
            [
                "aws",
                "ssm",
                "start-session",
                "--target",
                instance_id,
                "--region",
                region,
                "--document-name",
                "AWS-StartInteractiveCommand",
                "--parameters",
                params,
            ],
            env=env_vars,
            check=False,
        )
    except KeyboardInterrupt:
        print("\n# SSM session interrupted by user.\n")
        return
    except FileNotFoundError:
        die("aws CLI not found in PATH")

    if result.returncode not in (0, 130):
        die(f"aws ssm start-session failed for instance {instance_id}", result.returncode)


def start_interactive_shell_session(instance_id: str, env: str, service: str, region: str) -> None:
    run_ssm_start_session(
        instance_id=instance_id,
        env=env,
        service=service,
        region=region,
        remote_command="exec bash -l",
    )


def build_screen_remote_command(mode: str) -> str:
    if mode == "recover":
        screen_script = (
            'screen -ls; '
            'echo "Above are the existing screen sessions (if any)."; '
            'read -p "Screen session name to attach (default: deploy): " SNAME; '
            '[ -z "$SNAME" ] && SNAME=deploy; '
            'echo "Attaching to screen session: $SNAME"; '
            'screen -dr "$SNAME" || screen -S "$SNAME"'
        )
    else:
        screen_script = "screen -S deploy"

    escaped_script = screen_script.replace("'", "'\"'\"'")
    return f"bash -lc '{escaped_script}'"
