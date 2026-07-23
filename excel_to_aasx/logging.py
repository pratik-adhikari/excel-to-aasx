"""Backward-compatibility shim — do not import this directly.

All new code should import from excel_to_aasx.cli_output instead.
This module exists only so any external scripts that do
  from excel_to_aasx.logging import ...
continue to work during migration.
"""
# Preserve the old import path for downstream scripts while keeping the actual
# implementation in a module whose name cannot shadow Python's logging module.
from excel_to_aasx.cli_output import (  # noqa: F401
    classified,
    color,
    error,
    generated,
    info,
    warning,
    RED,
    GREEN,
    CYAN,
    RESET,
)
