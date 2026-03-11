"""Output formatting helpers."""
from __future__ import annotations

from typing import Any, List


def render_table(headers: List[str], rows: List[List[Any]]) -> None:
    if not rows:
        return

    widths = [len(header) for header in headers]
    str_rows = [[str(value) for value in row] for row in rows]

    for row in str_rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    def fmt_row(values: List[str]) -> str:
        return " | ".join(value.ljust(widths[index]) for index, value in enumerate(values))

    print(fmt_row(headers))
    print("-+-".join("-" * width for width in widths))
    for row in str_rows:
        print(fmt_row(row))
