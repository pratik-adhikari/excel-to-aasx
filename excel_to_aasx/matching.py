"""Row-to-template element matching logic for the AAS transform pipeline.

Template matching is kept separate from orchestration so its scoring rules can
be tested independently and reused by the transform stage.
Contains the scoring function, candidate enumeration, tie-breaking,
and ambiguity detection that map Excel input rows to AAS template elements.

Public API (re-exported from transform for backward compat):
    score, best_candidate, candidate_elements
"""

from __future__ import annotations

from typing import Any

from excel_to_aasx.cli_output import classified, warning
from excel_to_aasx.models import Candidate, InputRow, RowClassification, TemplateEntry


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

# A match must contain at least one strong signal. This conservative threshold
# avoids silently placing a source value in the wrong template element.
MIN_ACCEPTANCE_SCORE = 40

# Near ties are reported because the selected match remains a judgement call
# that reviewers may need to audit.
AMBIGUITY_WINDOW = 8


# ──────────────────────────────────────────────────────────────────────────────
# Helpers (duplicated from transform to avoid circular import)
# ──────────────────────────────────────────────────────────────────────────────

def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _semantic_id(element: dict[str, Any]) -> str:
    keys = (element.get("semanticId") or {}).get("keys", [])
    return keys[-1].get("value", "") if keys else ""


def _normalized_semantic(value: str) -> str:
    return value.replace("https://api.eclass-cdp.com/", "").rstrip("/").lower() if value else ""


def _children(element: dict[str, Any]) -> list[dict[str, Any]]:
    value = element.get("value")
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict) and "modelType" in item]
    sub = element.get("submodelElements")
    if isinstance(sub, list):
        return sub
    return []


def _expected_model_type(field_type: str) -> str:
    lowered = field_type.lower()
    if "file" in lowered:
        return "File"
    if "multilanguage" in lowered or "lang" in lowered:
        return "MultiLanguageProperty"
    if "reference" in lowered:
        return "ReferenceElement"
    if "blob" in lowered:
        return "Blob"
    if "relation" in lowered:
        return "RelationshipElement"
    if "collection" in lowered:
        return "SubmodelElementCollection"
    if "list" in lowered:
        return "SubmodelElementList"
    return "Property"


# ──────────────────────────────────────────────────────────────────────────────
# Candidate enumeration
# ──────────────────────────────────────────────────────────────────────────────

def candidate_elements(
    element: dict[str, Any],
    parent_path: str = "",
    _depth: int = 0,
) -> list[Any]:
    """Return a flat list of Candidate objects for all template elements."""
    # Templates are external input; bound traversal to avoid pathological
    # nesting exhausting the Python call stack.
    if _depth > 64:
        warning(f"candidate_elements: max depth exceeded at {parent_path!r}")
        return []

    id_short = _text(element.get("idShort"))
    path = f"{parent_path}/{id_short or '[]'}" if parent_path else id_short or "[]"

    result: list[Any] = []
    model_type = _text(element.get("modelType"))

    if model_type not in {"", "Submodel", "SubmodelElementList", "SubmodelElementCollection"}:
        result.append(
            Candidate(
                id_short=id_short,
                path=path,
                model_type=model_type,
                semantic_id=_semantic_id(element),
                value_type=_text(element.get("valueType")),
                element=element,
            )
        )

    for child in _children(element):
        result.extend(candidate_elements(child, path, _depth + 1))
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Scoring & best-match selection
# ──────────────────────────────────────────────────────────────────────────────

def score(row: Any, candidate: Any) -> int:
    """Compute matching score between an InputRow and a Candidate.

    Score weights:
        semanticId exact match  +45
        idShort exact match     +40
        semantic substring hit  +10
        idShort in path          +8
        modelType match          +4
    """
    row_sem = _normalized_semantic(row.semantic_id)
    candidate_sem = _normalized_semantic(candidate.semantic_id)
    value = 0
    if row.id_short and row.id_short == candidate.id_short:
        value += 40
    if row_sem and candidate_sem and row_sem == candidate_sem:
        value += 45
    if row_sem and candidate_sem and (row_sem in candidate_sem or candidate_sem in row_sem):
        value += 10
    if row.id_short and row.id_short.lower() in candidate.path.lower():
        value += 8
    if _expected_model_type(row.field_type) == candidate.model_type:
        value += 4
    return value


def best_candidate(
    row: Any,
    candidates: list[Any],
    used_paths: set[str],
) -> tuple[Any | None, int]:
    """Return (best_candidate, best_score) for the given row.

    Raises no exception. Returns (None, 0) when no candidate scores above
    MIN_ACCEPTANCE_SCORE.

    Weak matches are rejected, near ties are logged, and equal scores prefer
    the shallowest candidate path for a conservative structural interpretation.
    """
    best: Any = None
    best_score = 0
    runner_up_score = 0

    for candidate in candidates:
        if candidate.path in used_paths:
            continue
        candidate_score = score(row, candidate)
        if candidate_score > best_score:
            runner_up_score = best_score
            best = candidate
            best_score = candidate_score
        elif candidate_score > runner_up_score:
            runner_up_score = candidate_score
        elif candidate_score == best_score and best is not None:
            # Prefer the shallowest path when scores are equal because it is the
            # least specific interpretation and therefore the least surprising.
            if len(candidate.path) < len(best.path):
                runner_up_score = best_score
                best = candidate

    # Reject weak matches rather than generating plausible-looking wrong data.
    if best_score < MIN_ACCEPTANCE_SCORE:
        return None, best_score

    # Preserve the match but make ambiguity visible in the stage log.
    if best is not None and best_score - runner_up_score <= AMBIGUITY_WINDOW:
        classified(
            f"AMBIGUOUS match: row={row.id_short!r} "
            f"best_score={best_score} runner_up={runner_up_score} "
            f"→ {best.path!r}"
        )

    return best, best_score
