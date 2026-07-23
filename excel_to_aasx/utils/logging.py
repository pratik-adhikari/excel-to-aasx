"""Compatibility exports for the former logging helper.

New code should import output helpers from :mod:`excel_to_aasx.utils.cli_output`.
"""

from excel_to_aasx.utils.cli_output import (
    CYAN,
    GREEN,
    RED,
    RESET,
    classified,
    color,
    error,
    generated,
    info,
    warning,
)

__all__ = [
    "classified",
    "color",
    "error",
    "generated",
    "info",
    "warning",
    "RED",
    "GREEN",
    "CYAN",
    "RESET",
]
