# Limitations

This project makes Excel-to-AASX generation reproducible and reviewable. It
does not make arbitrary spreadsheets semantically correct AAS instances.

## Strong Guarantees

The pipeline can guarantee:

- workbook content is extracted into stable JSON evidence;
- configured official templates are used as the structural source;
- generated AAS JSON is checked by schema and SDK validation;
- project rules reject known bad outputs such as parser metadata leakage;
- AASX packages are roundtrip-read before success is reported;
- mapping, validation, dummy-value, and packaging decisions are logged.

## Weak Guarantees

The pipeline cannot fully guarantee:

- every Excel row belongs to the chosen submodel;
- every visual section heading was interpreted correctly;
- every unit, value, file, image, and lifecycle field is business-correct;
- copied template rows in Excel represent real product data;
- a missing value should be empty, dummy-generated, or manually supplied;
- a UI visualization tab will render every valid AAS element.

## Why Full Automation Is Limited

Excel contains layout and presentation signals, not a formal AAS mapping. A
merged cell, color, blank row, or nearby heading can be meaningful to a human
while still being ambiguous to software.

```mermaid
flowchart TD
    A[Excel cell value] --> B{Has clear idShort and semantic ID?}
    B -- yes --> C[Can map with high confidence]
    B -- no --> D{Can template path or section context disambiguate?}
    D -- yes --> E[Map with evidence and confidence]
    D -- no --> F[Flag for manual review]
```

## Dummy Values

Mandatory fields are derived from the selected IDTA template, not from the
Excel sheet title or visual layout. In the current implementation, a leaf
element is treated as mandatory when the template contains:

```text
qualifiers[].type = SMT/Cardinality
qualifiers[].value = One
```

Dummy generation currently applies only to these leaf element types:

| AAS element type | Missing value behavior |
| --- | --- |
| `Property` | Fill `value` according to `valueType` |
| `MultiLanguageProperty` | Fill English text with `Not Available` |
| `File` | Fill `/dummy/not-available.txt` and default `contentType` if needed |
| `Range` | Fill both `min` and `max` |

Container elements such as `SubmodelElementCollection` and
`SubmodelElementList` are not dummy-filled directly. Their children are checked
recursively.

Dummy values used by type:

| `valueType` | Dummy value |
| --- | --- |
| `xs:string` and unknown types | `Not Available` |
| `xs:boolean` | `false` |
| integer types | `-1` |
| decimal/float/double types | `-1.0` |
| `xs:date` | `1970-01-01` |
| `xs:dateTime` | `1970-01-01T00:00:00` |
| `xs:anyURI` | `https://example.org/dummy/not-available` |

The purpose is visibility and structural completeness. If the template says a
field is mandatory but Excel provides no value, the generated AAS still exposes
the element and the report records the dummy decision.

Dummy values are marked with:

```text
SourceValueStatus = DummyGenerated
```

Dummy-generated rows are also listed in `mapping-report.json` under:

```text
submodels[].dummyGeneratedRows
```

This is not real product data. It is a review signal.

## Missing Excel Values

Some Excel rows describe a parameter but have no `Actual Value`. If the element
is not mandatory, the pipeline should keep the element visible when it can be
placed safely, but mark the source status instead of inventing product data.

Such elements are marked with:

```text
SourceValueStatus = MissingInExcel
```

This distinction matters:

| Status | Meaning |
| --- | --- |
| `MissingInExcel` | Excel mentioned the element, but did not provide an actual value |
| `DummyGenerated` | The template required a value, so the pipeline inserted a typed placeholder |

## Supplementary Files

If Excel references a local image or PDF but the real file is not available,
the package step may add a placeholder supplementary file. This keeps AASX
packaging technically valid, but the placeholder is not a substitute for the
real document.

## Production Requirement

For production use, treat the generated reports as mandatory review artifacts.
High-confidence automation is acceptable only when:

- input workbook formats are controlled;
- template versions are pinned;
- mapping reports are reviewed;
- validation is clean;
- unresolved or low-confidence rows block release;
- accepted mappings become versioned configuration or tests.
