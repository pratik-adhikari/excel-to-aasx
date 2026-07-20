"""Load company-specific pipeline configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_COMPANY_CONFIG = Path("configs/companies/schunk.json")


def load_company_config(path: Path | None) -> dict[str, Any]:
    config_path = path or DEFAULT_COMPANY_CONFIG
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["_path"] = str(config_path)
    return config


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
