# excel-to-aasx

Standalone Excel-to-AASX generation package.

This repository converts configured supplier Excel workbooks into auditable AAS
JSON and AASX packages. It is intentionally separate from any BaSyx
server/runtime repository.

## Pipeline

```text
Excel workbook
  -> neutral extraction JSON
  -> official-template-shaped AAS JSON
  -> validation reports
  -> AASX package
```

## Common Commands

```bash
git submodule update --init --recursive
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
make generate COMPANY=schunk
```

## Documentation

```text
docs/README.md
docs/architecture.md
docs/quickstart.md
docs/limitations.md
docs/third-party.md
```

The key rule is simple: use official templates and maintained AAS tooling for
standard behavior, and keep only project-specific extraction, mapping, and
evidence code in this package.
