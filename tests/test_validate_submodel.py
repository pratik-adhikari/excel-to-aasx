"""Unit tests for excel_to_aasx.validate.validate_submodel.

Tests the main structural validation function that was previously untested.
"""

from __future__ import annotations

from excel_to_aasx.validate import validate_submodel, allowed_expansion


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _minimal_submodel(id_short: str = "Nameplate") -> dict:
    return {
        "modelType": "Submodel",
        "idShort": id_short,
        "id": f"https://example.org/{id_short}",
        "semanticId": {"type": "ExternalReference", "keys": [
            {"type": "GlobalReference", "value": f"https://example.org/sm/{id_short}"}
        ]},
        "submodelElements": [],
    }


def _property(id_short: str, value_type: str = "xs:string", value: str | None = None) -> dict:
    el: dict = {
        "modelType": "Property",
        "idShort": id_short,
        "valueType": value_type,
    }
    if value is not None:
        el["value"] = value
    return el


def _mlp(id_short: str, entries: list[dict]) -> dict:
    return {
        "modelType": "MultiLanguageProperty",
        "idShort": id_short,
        "value": entries,
    }


# ──────────────────────────────────────────────────────────────────────────────
# validate_submodel tests
# ──────────────────────────────────────────────────────────────────────────────

def test_validate_submodel_identical_submodels_has_no_issues() -> None:
    sm = _minimal_submodel("Nameplate")
    issues = validate_submodel(sm, sm)
    errors = [i for i in issues if i["severity"] == "error"]
    assert errors == [], f"Expected no errors for identical submodels; got: {errors}"


def test_validate_submodel_idshort_mismatch_is_error() -> None:
    generated = _minimal_submodel("Nameplate")
    reference = _minimal_submodel("TechnicalData")
    issues = validate_submodel(generated, reference)
    codes = [i["code"] for i in issues]
    assert "idshort-mismatch" in codes


def test_validate_submodel_semantic_id_mismatch_is_error() -> None:
    generated = _minimal_submodel("Nameplate")
    reference = _minimal_submodel("Nameplate")
    # make the semantic IDs different
    reference["semanticId"]["keys"][0]["value"] = "https://example.org/sm/Other"
    issues = validate_submodel(generated, reference)
    codes = [i["code"] for i in issues]
    assert "semantic-id-mismatch" in codes


def test_validate_submodel_unknown_path_is_warning() -> None:
    generated = _minimal_submodel("Nameplate")
    generated["submodelElements"] = [
        _property("UnknownField", value="hello"),
    ]
    reference = _minimal_submodel("Nameplate")
    # reference has no elements — UnknownField is not in the reference template
    issues = validate_submodel(generated, reference)
    warnings = [i for i in issues if i["severity"] == "warning" and i["code"] == "non-reference-element"]
    assert len(warnings) == 1


def test_validate_submodel_known_allowed_expansion_is_not_warned() -> None:
    """Paths in allowedExpansions must not trigger non-reference-element warning."""
    generated = _minimal_submodel("Nameplate")
    generated["submodelElements"] = [
        _property("Street", value="Hauptstrasse 1"),
    ]
    reference = _minimal_submodel("Nameplate")
    issues = validate_submodel(
        generated,
        reference,
        allowed_expansions={"Nameplate": {"Street"}},
    )
    warnings = [i for i in issues if i["code"] == "non-reference-element"]
    assert warnings == [], "Allowed expansion paths must not produce a warning"


def test_validate_submodel_invalid_boolean_value_is_error() -> None:
    generated = _minimal_submodel("Nameplate")
    generated["submodelElements"] = [
        _property("IsComplete", value_type="xs:boolean", value="maybe"),
    ]
    reference = _minimal_submodel("Nameplate")
    reference["submodelElements"] = [
        _property("IsComplete", value_type="xs:boolean"),
    ]
    issues = validate_submodel(generated, reference)
    codes = [i["code"] for i in issues]
    assert "invalid-value-type" in codes


def test_validate_submodel_invalid_integer_value_is_error() -> None:
    generated = _minimal_submodel("Nameplate")
    generated["submodelElements"] = [
        _property("Count", value_type="xs:integer", value="not-a-number"),
    ]
    reference = _minimal_submodel("Nameplate")
    reference["submodelElements"] = [
        _property("Count", value_type="xs:integer"),
    ]
    issues = validate_submodel(generated, reference)
    codes = [i["code"] for i in issues]
    assert "invalid-value-type" in codes


def test_validate_submodel_valid_integer_value_has_no_error() -> None:
    generated = _minimal_submodel("Nameplate")
    generated["submodelElements"] = [
        _property("Count", value_type="xs:integer", value="42"),
    ]
    reference = _minimal_submodel("Nameplate")
    reference["submodelElements"] = [
        _property("Count", value_type="xs:integer"),
    ]
    issues = validate_submodel(generated, reference)
    errors = [i for i in issues if i["severity"] == "error"]
    assert errors == []


def test_validate_submodel_mlp_missing_language_is_error() -> None:
    generated = _minimal_submodel("Nameplate")
    generated["submodelElements"] = [
        _mlp("Name", [{"text": "Hello"}]),  # missing 'language' key
    ]
    reference = _minimal_submodel("Nameplate")
    reference["submodelElements"] = [
        _mlp("Name", [{"language": "en", "text": "Name"}]),
    ]
    issues = validate_submodel(generated, reference)
    codes = [i["code"] for i in issues]
    assert "invalid-multilanguage-value" in codes


# ──────────────────────────────────────────────────────────────────────────────
# allowed_expansion tests
# ──────────────────────────────────────────────────────────────────────────────

def test_allowed_expansion_returns_true_for_configured_path() -> None:
    assert allowed_expansion(
        "Nameplate",
        "AddressInformation/Street",
        {},
        allowed_expansions={"Nameplate": {"AddressInformation/Street"}},
    )


def test_allowed_expansion_returns_false_for_unknown_path() -> None:
    assert not allowed_expansion(
        "Nameplate",
        "SomeUnknownPath",
        {},
        allowed_expansions={"Nameplate": {"AddressInformation/Street"}},
    )


def test_allowed_expansion_uses_default_when_no_config_supplied() -> None:
    # Default expansions include Nameplate/AddressInformation/Street
    assert allowed_expansion("Nameplate", "AddressInformation/Street", {})
