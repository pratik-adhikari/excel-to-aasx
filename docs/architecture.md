# Architecture

`excel-to-aasx` is a standalone generation tool. It is not a BaSyx server and
does not require Keycloak, MongoDB, or the BaSyx UI to create AASX packages.

## Pipeline

```text
Excel workbook
  -> Step 1 neutral extraction JSON
  -> Step 2 AAS JSON shaped by official IDTA templates
  -> Step 3 validation
  -> Step 4 AASX package
```

## Design Rules

- Keep server/runtime deployment outside this repository.
- Keep generated data under ignored `data/` folders.
- Use official templates and SDKs through third-party repositories.
- Generate evidence reports at every non-trivial step.
- Do not silently claim semantic correctness when the source spreadsheet is
  ambiguous.

## Third-Party Inputs

The project expects these reference repositories under `third_party/`:

```text
third_party/admin-shell-io/submodel-templates
third_party/aas-core-works/aas-core-codegen
third_party/aas-core-works/aas-core3.0-python
```

They should remain unmodified. Project-specific behavior belongs in local
configuration and pipeline code.
