"""Terminal output helpers for pipeline stages.

Named cli_output (not logging) to avoid shadowing the stdlib logging module.
"""

from __future__ import annotations

import os
import sys
from typing import Any

RED = "\033[31m"
GREEN = "\033[32m"
CYAN = "\033[36m"
RESET = "\033[0m"


def color(text: str, ansi: str) -> str:
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return text
    return f"{ansi}{text}{RESET}"


def info(message: str, *values: Any) -> None:
    print(message.format(*values), flush=True)


def generated(path: Any) -> None:
    print(color(f"generated {path}", GREEN), flush=True)


def classified(message: str) -> None:
    print(color(message, CYAN), flush=True)


def warning(message: str) -> None:
    # Keep machine-readable pipeline output on stdout; diagnostics belong on
    # stderr so callers can safely pipe stdout into another tool.
    print(color(f"WARNING {message}", RED), file=sys.stderr, flush=True)


def error(message: str) -> None:
    print(color(message, RED), file=sys.stderr, flush=True)
