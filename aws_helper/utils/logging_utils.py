"""Logging helpers."""
from __future__ import annotations

import logging
import sys

LOG = logging.getLogger("aws_tool")


def configure_logging(verbose: bool = False, debug: bool = False) -> None:
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )
