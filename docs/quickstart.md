# Quickstart

## Install

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

Initialize reference submodules:

```bash
git submodule update --init --recursive
```

## Prepare Input

For the default Schunk configuration, put the workbooks in:

```text
data/input/schunk/
```

Expected file names and worksheet mappings are defined in:

```text
configs/companies/schunk.json
```

## Run The Full Pipeline

```bash
make generate COMPANY=schunk
```

Outputs:

```text
data/generated/schunk/xlsx-json-step1/
data/generated/schunk/xlsx-json-step2/
data/generated/schunk/xlsx-json-step3/
data/generated/schunk/xlsx-json-step4/
```

## Run Individual Stages

```bash
make extract COMPANY=schunk
make transform COMPANY=schunk
make validate COMPANY=schunk
make package COMPANY=schunk
```

## Inspect Reports

Important review files:

```text
data/generated/schunk/xlsx-json-step2/<workbook>/mapping-report.json
data/generated/schunk/xlsx-json-step3/<workbook>/validation-report.json
data/generated/schunk/xlsx-json-step4/summary.json
```

If validation reports errors, do not package or deploy the result as trusted
data. Fix the source workbook, config, mapping logic, or template choice.
