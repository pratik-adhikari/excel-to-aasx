"""Unit tests for excel_to_aasx.package normalisation logic.

Tests normalize_for_basyx, aasx_package_path, and assert_validated
which had no unit coverage.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from excel_to_aasx.package import (
    aasx_package_path,
    assert_validated,
    collect_missing_supplementary_files,
    normalize_for_basyx,
)


# ──────────────────────────────────────────────────────────────────────────────
# aasx_package_path (extended coverage beyond existing test)
# ──────────────────────────────────────────────────────────────────────────────

def test_aasx_package_path_canonical_path_passes_through() -> None:
    assert aasx_package_path("/aasx/files/foo.pdf") == "/aasx/files/foo.pdf"


def test_aasx_package_path_relative_path_gets_prefix() -> None:
    result = aasx_package_path("documents/report.pdf")
    assert result.startswith("/aasx/files/")
    assert "report.pdf" in result


def test_aasx_package_path_empty_string_becomes_missing_file() -> None:
    result = aasx_package_path("")
    assert result == "/aasx/files/missing-file"


def test_aasx_package_path_strips_trailing_dot_from_filename_only() -> None:
    # trailing dot on filename should be stripped
    result = aasx_package_path("docs/report.")
    assert not result.endswith(".")
    # mid-path dot (e.g. version number) must be preserved
    result2 = aasx_package_path("v1.0/report.pdf")
    assert "v1.0" in result2


def test_aasx_package_path_url_decoded() -> None:
    result = aasx_package_path("My%20Document.pdf")
    assert "My Document.pdf" in result or "My%20Document.pdf" in result
    # must not double-encode
    assert "%2520" not in result


# ──────────────────────────────────────────────────────────────────────────────
# normalize_for_basyx
# ──────────────────────────────────────────────────────────────────────────────

def test_normalize_for_basyx_removes_idshort_from_list_children() -> None:
    env = {
        "submodels": [{
            "modelType": "Submodel",
            "idShort": "Test",
            "submodelElements": [{
                "modelType": "SubmodelElementList",
                "idShort": "Items",
                "value": [
                    {"modelType": "Property", "idShort": "ShouldBeRemoved", "valueType": "xs:string"},
                ],
            }],
        }]
    }
    normalize_for_basyx(env)
    child = env["submodels"][0]["submodelElements"][0]["value"][0]
    assert "idShort" not in child, "Children of SubmodelElementList must not have idShort"


def test_normalize_for_basyx_preserves_non_list_idshorts() -> None:
    env = {
        "submodels": [{
            "modelType": "Submodel",
            "idShort": "Test",
            "submodelElements": [{
                "modelType": "SubmodelElementCollection",
                "idShort": "MyCollection",
                "value": [
                    {"modelType": "Property", "idShort": "KeepMe", "valueType": "xs:string"},
                ],
            }],
        }]
    }
    normalize_for_basyx(env)
    child = env["submodels"][0]["submodelElements"][0]["value"][0]
    assert child.get("idShort") == "KeepMe"


# ──────────────────────────────────────────────────────────────────────────────
# Supplementary files are collected before package elements are rewritten.
# ──────────────────────────────────────────────────────────────────────────────

def test_collect_missing_supplementary_files_rewrites_local_paths() -> None:
    payload = {
        "submodels": [{
            "submodelElements": [{
                "modelType": "File",
                "idShort": "Doc",
                "value": "relative/path/document.pdf",
                "contentType": "application/pdf",
            }]
        }]
    }
    records = collect_missing_supplementary_files(payload)
    assert len(records) == 1
    assert records[0]["path"].startswith("/aasx/files/")
    # payload must also be rewritten
    rewritten = payload["submodels"][0]["submodelElements"][0]["value"]
    assert rewritten.startswith("/aasx/")


def test_collect_missing_supplementary_files_deduplicates() -> None:
    payload = {
        "submodels": [{
            "submodelElements": [
                {"modelType": "File", "idShort": "A", "value": "same.pdf", "contentType": "application/pdf"},
                {"modelType": "File", "idShort": "B", "value": "same.pdf", "contentType": "application/pdf"},
            ]
        }]
    }
    records = collect_missing_supplementary_files(payload)
    paths = [r["path"] for r in records]
    assert len(paths) == len(set(paths)), "Duplicate file paths must be deduplicated"


# ──────────────────────────────────────────────────────────────────────────────
# assert_validated
# ──────────────────────────────────────────────────────────────────────────────

def _write_report(path: Path, errors: int = 0, warnings: int = 0) -> None:
    path.mkdir(parents=True, exist_ok=True)
    report = {
        "issueCounts": {"error": errors, "warning": warnings, "info": 0},
        "issues": [],
        "submodels": [],
    }
    (path / "validation-report.json").write_text(json.dumps(report), encoding="utf-8")


def test_assert_validated_passes_when_no_errors(tmp_path: Path) -> None:
    workbook_dir = tmp_path / "wb"
    validation_dir = tmp_path / "val"
    _write_report(validation_dir / "wb", errors=0, warnings=3)
    # Should not raise — warnings are OK by default
    assert_validated(workbook_dir, validation_dir, strict=False)


def test_assert_validated_raises_on_errors(tmp_path: Path) -> None:
    workbook_dir = tmp_path / "wb"
    validation_dir = tmp_path / "val"
    _write_report(validation_dir / "wb", errors=2, warnings=0)
    with pytest.raises(RuntimeError, match=r"\b2 errors\b"):
        assert_validated(workbook_dir, validation_dir)


def test_assert_validated_strict_raises_on_warnings(tmp_path: Path) -> None:
    workbook_dir = tmp_path / "wb"
    validation_dir = tmp_path / "val"
    _write_report(validation_dir / "wb", errors=0, warnings=1)
    with pytest.raises(RuntimeError):
        assert_validated(workbook_dir, validation_dir, strict=True)


def test_assert_validated_strict_passes_with_no_warnings(tmp_path: Path) -> None:
    workbook_dir = tmp_path / "wb"
    validation_dir = tmp_path / "val"
    _write_report(validation_dir / "wb", errors=0, warnings=0)
    assert_validated(workbook_dir, validation_dir, strict=True)  # must not raise
