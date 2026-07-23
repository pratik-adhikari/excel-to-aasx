"""Value normalisation utilities for the AAS transform pipeline.

Value coercion is kept separate from template matching so both the transform
stage and focused tests can use the same normalization rules.
All functions here are pure transformations on strings or dicts/lists
with no dependency on row-matching or template-traversal logic.

Public API (re-exported from transform for backward compat):
    infer_value_type, normalize_value, normalize_uri_value,
    normalize_date, normalize_datetime, infer_content_type,
    normalize_instance_payload, deduplicate_language_strings,
    remove_template_qualifiers, deduplicate_child_idshorts,
    remove_empty_idshorts, fill_element, fill_dummy_value, dummy_value_for
"""

from __future__ import annotations

import datetime
import re
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

from excel_to_aasx.cli_output import warning


# ──────────────────────────────────────────────────────────────────────────────
# Shared helpers that this module depends on from transform (imported lazily to
# avoid circular imports; transform still owns the dataclass definitions).
# ──────────────────────────────────────────────────────────────────────────────

def _text(value: Any) -> str:
    """Return str(value).strip() or '' for None/empty."""
    if value is None:
        return ""
    return str(value).strip()


LANGUAGE_STRING_FIELDS = ("description", "displayName", "preferredName", "shortName", "definition")

PLACEHOLDER_VALUES = {"", "#", "-", "n/a", "N/A", "not specified", "Not specified"}


# ──────────────────────────────────────────────────────────────────────────────
# Value type inference
# ──────────────────────────────────────────────────────────────────────────────

def infer_value_type(field_type: str) -> str:
    lowered = field_type.lower()
    if "boolean" in lowered:
        return "xs:boolean"
    if "datetime" in lowered:
        return "xs:dateTime"
    if re.search(r"\bdate\b", lowered):
        return "xs:date"
    if "decimal" in lowered:
        return "xs:decimal"
    if "double" in lowered:
        return "xs:double"
    if "integer" in lowered or "int" in lowered:
        return "xs:integer"
    if "uri" in lowered:
        return "xs:anyURI"
    return "xs:string"


# ──────────────────────────────────────────────────────────────────────────────
# Value normalisation
# ──────────────────────────────────────────────────────────────────────────────

def normalize_value(value: str, value_type: str) -> str:
    if value_type == "xs:boolean":
        # Excel exports commonly use localized boolean spellings; normalize the
        # known forms while leaving unknown values visible for validation.
        normalised = value.strip().lower()
        if normalised in {"true", "1", "yes", "ja", "wahr"}:
            return "true"
        if normalised in {"false", "0", "no", "nein", "falsch"}:
            return "false"
        warning(f"invalid xs:boolean value {value!r} — keeping as-is (will fail AAS Core validation)")
        return normalised
    if value_type == "xs:date":
        return normalize_date(value)
    if value_type == "xs:dateTime":
        return normalize_datetime(value)
    if value_type == "xs:anyURI":
        return normalize_uri_value(value)
    return value


def normalize_uri_value(value: str) -> str:
    normalized = re.sub(r"^\s*\[DUMMY\]\s*", "", value).strip()
    if not normalized:
        return normalized
    parts = urlsplit(normalized)
    if parts.scheme:
        return urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                quote(parts.path, safe="/%:@"),
                quote(parts.query, safe="=&?/%:@"),
                quote(parts.fragment, safe="=&?/%:@"),
            )
        )
    return quote(normalized, safe="/%:@;,.()_-")


def normalize_date(value: str) -> str:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T00:00:00(?:\+00:00)?", value):
        return value[:10]
    if re.fullmatch(r"\d+(\\.0)?", value):
        serial = int(float(value))
        base = datetime.date(1899, 12, 30)
        return (base + datetime.timedelta(days=serial)).isoformat()
    return value


def normalize_datetime(value: str) -> str:
    if value.endswith(("Z", "z")):
        return f"{value[:-1]}+00:00"
    if re.fullmatch(r"\d+(\\.0)?", value):
        return f"{normalize_date(value)}T00:00:00"
    return value


def infer_content_type(value: str) -> str:
    # Inspect the URL path suffix so a query string or directory name cannot
    # incorrectly determine the MIME type.
    path_part = urlsplit(value).path or value
    suffix = PurePosixPath(path_part).suffix.lower()
    content_type = {
        ".pdf":  "application/pdf",
        ".png":  "image/png",
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(suffix)
    if content_type:
        return content_type
    # Schunk-specific: URLs containing FWEBP or fwebp token (no file extension)
    if "fwebp" in value.lower():
        return "image/webp"
    return "application/octet-stream"


# ──────────────────────────────────────────────────────────────────────────────
# Dummy value generation
# ──────────────────────────────────────────────────────────────────────────────

def dummy_value_for(value_type: str) -> str:
    return {
        "xs:boolean":  "false",
        "xs:date":     "2000-01-01",
        "xs:dateTime": "2000-01-01T00:00:00",
        "xs:integer":  "0",
        "xs:decimal":  "0.0",
        "xs:double":   "0.0",
        "xs:anyURI":   "https://example.org/[DUMMY]",
    }.get(value_type, "[DUMMY]")


# ──────────────────────────────────────────────────────────────────────────────
# Payload post-processing (pure dict/list transformations)
# ──────────────────────────────────────────────────────────────────────────────

def deduplicate_language_strings(field: str, values: Any) -> Any:
    if not isinstance(values, list):
        return values

    merged: dict[str, dict[str, str]] = {}
    ordered_languages: list[str] = []
    for item in values:
        if not isinstance(item, dict) or "language" not in item:
            return values
        language = _text(item.get("language")) or "en"
        item_text = _text(item.get("text"))
        if language not in merged:
            merged[language] = {**item, "language": language}
            ordered_languages.append(language)
            continue
        if field == "shortName":
            continue
        existing_text = _text(merged[language].get("text"))
        if item_text and item_text not in existing_text:
            merged[language]["text"] = (
                f"{existing_text}\n{item_text}" if existing_text else item_text
            )

    result = [merged[language] for language in ordered_languages]
    if field == "shortName":
        result = [item for item in result if len(_text(item.get("text"))) <= 18]
    return result


def remove_template_qualifiers(element: dict[str, Any]) -> None:
    qualifiers = element.get("qualifiers")
    if not isinstance(qualifiers, list):
        return
    kept = []
    seen_types: set[str] = set()
    for qualifier in qualifiers:
        if not isinstance(qualifier, dict):
            kept.append(qualifier)
            continue
        if qualifier.get("kind") == "TemplateQualifier":
            continue
        qualifier_type = _text(qualifier.get("type"))
        if qualifier_type and qualifier_type in seen_types:
            continue
        if qualifier_type:
            seen_types.add(qualifier_type)
        kept.append(qualifier)
    if kept:
        element["qualifiers"] = kept
    else:
        element.pop("qualifiers", None)


def deduplicate_child_idshorts(element: dict[str, Any]) -> None:
    from excel_to_aasx.transform import aas_idshort  # avoid circular at module level
    for field in ("submodelElements", "value"):
        children_value = element.get(field)
        if not isinstance(children_value, list):
            continue
        seen: dict[str, int] = {}
        for child in children_value:
            if not isinstance(child, dict):
                continue
            id_short = _text(child.get("idShort"))
            if not id_short:
                continue
            count = seen.get(id_short, 0) + 1
            seen[id_short] = count
            if count == 1:
                continue
            child["idShort"] = aas_idshort(f"{id_short}_{count}", "Value")


def remove_empty_idshorts(element: Any) -> None:
    if isinstance(element, dict):
        if element.get("idShort") == "":
            element.pop("idShort", None)
        for value in element.values():
            remove_empty_idshorts(value)
    elif isinstance(element, list):
        for item in element:
            remove_empty_idshorts(item)


def normalize_instance_payload(payload: Any, parent_model_type: str = "") -> None:
    if isinstance(payload, dict):
        if parent_model_type == "SubmodelElementList":
            payload.pop("idShort", None)

        for field in LANGUAGE_STRING_FIELDS:
            if field in payload:
                payload[field] = deduplicate_language_strings(field, payload[field])
                if payload[field] == []:
                    payload.pop(field)

        remove_template_qualifiers(payload)
        deduplicate_child_idshorts(payload)

        model_type = _text(payload.get("modelType"))
        for value in payload.values():
            normalize_instance_payload(value, model_type)
    elif isinstance(payload, list):
        for item in payload:
            normalize_instance_payload(item, parent_model_type)
