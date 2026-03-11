"""Common utility helpers."""
from __future__ import annotations

import json
import sys
from typing import Any, Iterable, List, Optional

from aws_helper.utils.logging_utils import LOG


def die(message: str, exit_code: int = 1) -> None:
    LOG.error(message)
    sys.exit(exit_code)


def json_default(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, default=json_default))


def chunked(items: List[str], size: int) -> Iterable[List[str]]:
    for index in range(0, len(items), size):
        yield items[index:index + size]


def casefold_contains(haystack: str, needle: Optional[str]) -> bool:
    if not needle:
        return True
    return needle.lower() in haystack.lower()
