"""Shared data models for the AAS transform pipeline.

Extracted from transform.py to avoid circular dependencies between
transform, matching, and value_normalise.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InputRow:
    sheet: str
    row: int
    id_short: str
    field_type: str
    semantic_id: str
    actual_value: str
    section_path: tuple[str, ...]


@dataclass
class Candidate:
    element: dict[str, Any]
    path: str
    id_short: str
    semantic_id: str
    model_type: str
    value_type: str


@dataclass(frozen=True)
class TemplateEntry:
    path: str
    id_short: str
    semantic_id: str
    model_type: str
    value_type: str
    cardinality: str
    is_arbitrary_placeholder: bool


@dataclass(frozen=True)
class RowClassification:
    row: InputRow
    classification: str
    reason: str
    template_path: str
    final_path: str
