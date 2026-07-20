# Quickstart

## Install

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

Initialize reference repositories:

```bash
git submodule update --init --recursive
```

## Prepare Input

Copy Schunk workbooks into:

```text
data/input/schunk/
```

The expected file names are listed in:

```text
configs/companies/schunk.json
```

## Generate AASX

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
