"""Argument validators."""
from __future__ import annotations

import argparse
import re

from aws_helper.constants import ENV_MAP, VALID_SERVICES, VALID_SORT_ORDERS


def validate_env(env: str) -> str:
    key = env.lower().strip()
    if key not in ENV_MAP:
        raise argparse.ArgumentTypeError(
            "invalid env: use prod | sandbox | int (dev/integration accepted as aliases)"
        )
    return key


def validate_service(service: str) -> str:
    normalized = service.lower().strip()
    if normalized not in VALID_SERVICES:
        raise argparse.ArgumentTypeError(
            "invalid service: use {}".format(" | ".join(VALID_SERVICES))
        )
    return normalized


def validate_region(region: str) -> str:
    if not re.match(r"^[a-z]{2}(-gov)?-[a-z]+-\d+$", region):
        raise argparse.ArgumentTypeError(
            "invalid AWS region format (example: eu-central-1)"
        )
    return region


def validate_sort_order(value: str) -> str:
    normalized = value.lower().strip()
    if normalized not in VALID_SORT_ORDERS:
        raise argparse.ArgumentTypeError("invalid sort order: use asc | desc")
    return normalized


def validate_instance_id(value: str) -> str:
    normalized = value.strip()
    if not re.match(r"^i-[0-9a-f]{8,17}$", normalized):
        raise argparse.ArgumentTypeError(
            "invalid EC2 instance id (expected format like i-0123456789abcdef0)"
        )
    return normalized


def validate_command_id(value: str) -> str:
    normalized = value.strip()
    if not re.match(r"^[0-9a-fA-F-]{20,}$", normalized):
        raise argparse.ArgumentTypeError("invalid SSM command id format")
    return normalized


def validate_ticket_id(value: str) -> str:
    normalized = value.strip()
    if not normalized.isdigit():
        raise argparse.ArgumentTypeError("ticket_id must be numeric")
    return normalized


def validate_since(value: str) -> str:
    normalized = value.strip()
    if not re.match(r"^\d+[hHdDmM]$", normalized):
        raise argparse.ArgumentTypeError(
            "invalid since format, expected examples: 6h, 24h, 7d, 30m"
        )
    return normalized.lower()
