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

Expected file names are defined in:

```text
configs/companies/schunk.json
```

Reusable worksheet mappings are inherited from:

```text
configs/formats/idta-schunk-workbook.json
```

For one exact workbook, copy the company config and reduce only the `workbooks`
list:

```bash
cp configs/companies/schunk.json configs/companies/schunk-single.json
```

Then edit:

```json
{
  "extends": "../formats/idta-schunk-workbook.json",
  "company": "schunk-single",
  "inputDir": "data/input/schunk",
  "outputRoot": "data/generated/schunk-single",
  "workbooks": ["EGP 40-N-N-B.xlsx"]
}
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
