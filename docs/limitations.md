# Limitations

This project can make Excel-to-AASX generation reproducible and auditable. It
cannot guarantee perfect semantic conversion for arbitrary spreadsheets.

## What Works Best

- Workbooks following AAS/DPP-style sheet structure.
- Rows with stable `idShort` values.
- Rows with semantic IDs.
- Sheets that correspond to official IDTA submodel templates.
- Human-reviewed mapping reports.

## Known Limitations

- Arbitrary Excel layouts cannot be converted with full confidence.
- Merged cells, formatting, comments, and hyperlinks can be extracted, but their
  semantic meaning still needs interpretation.
- Missing mandatory AAS values may require dummy placeholders or manual input.
- Local image/PDF filenames are not real file content unless the source files
  are available.
- Template selection is currently configuration-driven. Automatic high-confidence
  template detection should be added as a separate future stage.
- Validation proves structural correctness, not business truth.
- AASX packaging can include placeholder supplementary files, but placeholders
  are evidence of missing source data, not real product documentation.

## Industry Scope

The realistic claim is:

```text
Auditable generation of AASX packages from semi-structured AAS/DPP Excel
workbooks using official templates and validation reports.
```

The unrealistic claim is:

```text
Any Excel file can be converted automatically into a perfect AASX file.
```
