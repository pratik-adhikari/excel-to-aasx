"""Load company-specific pipeline configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# Keep the symbol for callers that imported it before company selection became
# explicit. A None default prevents one company's identifiers from leaking into
# another company's generated AAS documents.
DEFAULT_COMPANY_CONFIG: None = None


def load_company_config(path: Path | None) -> dict[str, Any]:
    if path is None:
        raise ValueError(
            "--company-config is required; no default company config is set. "
            "Pass the path to a configs/companies/<company>.json file."
        )
    config_path = path
    config = load_config_with_extends(config_path)
    config["_path"] = str(config_path)
    return config


def load_config_with_extends(
    path: Path,
    _seen: frozenset[str] | None = None,
) -> dict[str, Any]:
    # Resolve the complete inheritance chain before merging so every stage uses
    # exactly the same effective configuration and cycles fail deterministically.
    seen = _seen or frozenset()
    resolved = str(path.resolve())
    if resolved in seen:
        raise ValueError(f"Circular extends detected: {resolved}")
    config = json.loads(path.read_text(encoding="utf-8"))
    extends = config.pop("extends", None)
    if not extends:
        return config

    parent_path = (path.parent / extends).resolve()
    parent = load_config_with_extends(parent_path, seen | {resolved})
    return deep_merge(parent, config)


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def sheet_templates(config: dict[str, Any]) -> dict[str, tuple[str, str]]:
    return {
        item["sheet"]: (item["submodelIdShort"], item["template"])
        for item in config.get("sheets", [])
    }


def reference_files(config: dict[str, Any]) -> dict[str, str]:
    return {
        item["submodelIdShort"]: item["template"]
        for item in config.get("sheets", [])
    }
