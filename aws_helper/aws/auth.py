"""AWS authentication and session creation."""
from __future__ import annotations

import subprocess
from typing import Any

from aws_helper.constants import (
    ENV_MAP,
    GRANTED_SSO_REGION,
    GRANTED_SSO_START_URL,
    PROFILE_PATTERNS,
)
from aws_helper.utils.common import die
from aws_helper.utils.logging_utils import LOG

try:
    import boto3
    from botocore.exceptions import (
        BotoCoreError,
        ClientError,
        CredentialRetrievalError,
        NoCredentialsError,
        ProfileNotFound,
    )
except ImportError:
    boto3 = None
    CredentialRetrievalError = BotoCoreError = ClientError = NoCredentialsError = ProfileNotFound = Exception


def resolve_profile(env: str, service: str) -> str:
    suffix = ENV_MAP[env]
    pattern = PROFILE_PATTERNS[service]
    return pattern.format(suffix=suffix)


def is_credential_process_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "credential_process" in message
        or "custom-process" in message
        or "custom process" in message
        or "please login using 'granted sso login" in message
        or "error when retrieving credentials" in message
        or "sso session" in message
        or "expired" in message
        or "failed to refresh cached credentials" in message
        or "process provider" in message
    )


def run_granted_login() -> None:
    command = [
        "granted",
        "sso",
        "login",
        "--sso-start-url",
        GRANTED_SSO_START_URL,
        "--sso-region",
        GRANTED_SSO_REGION,
    ]

    LOG.warning("AWS SSO session appears expired or missing. Running granted login.")
    LOG.info("Command: %s", " ".join(command))

    try:
        result = subprocess.run(command, check=False)
    except FileNotFoundError:
        die("'granted' command not found in PATH. Install/configure granted first.")

    if result.returncode != 0:
        die("granted login failed. Please authenticate manually and retry.", result.returncode)


def new_session(env: str, service: str, region: str) -> Any:
    if boto3 is None:
        die("boto3/botocore are not installed. Run: python -m pip install boto3")

    profile = resolve_profile(env, service)
    LOG.info("Using AWS profile: %s", profile)
    LOG.debug("Creating boto3 session for service=%s env=%s region=%s", service, env, region)

    def _build_session() -> Any:
        session = boto3.Session(profile_name=profile, region_name=region)
        session.client("sts").get_caller_identity()
        return session

    try:
        return _build_session()
    except ProfileNotFound as exc:
        die(f"AWS profile not found: {exc}")
    except NoCredentialsError as exc:
        if is_credential_process_error(exc):
            run_granted_login()
            return _build_session()
        die(f"No AWS credentials available: {exc}")
    except CredentialRetrievalError as exc:
        if not is_credential_process_error(exc):
            raise
        run_granted_login()
        return _build_session()
    except (BotoCoreError, ClientError) as exc:
        if not is_credential_process_error(exc):
            raise
        run_granted_login()
        return _build_session()


def get_client(env: str, service: str, client_name: str, region: str) -> Any:
    return new_session(env, service=service, region=region).client(client_name)
