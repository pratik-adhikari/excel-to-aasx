SHELL := /bin/bash

COMPANY ?= schunk
COMPANY_CONFIG ?= configs/companies/$(COMPANY).json
COMPANY_OUTPUT_ROOT ?= data/generated/$(COMPANY)
REFERENCE_DIR ?= third_party/admin-shell-io
EXTRACTION_ROOT ?= data/extraction
TEMPLATES_DIR ?= data/templates/$(COMPANY)
PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python

.DEFAULT_GOAL := help

.PHONY: help setup templates extract transform validate package generate collect test

help:
	@awk 'BEGIN {FS = ":.*##"; printf "excel-to-aasx commands:\n\n"} /^[a-zA-Z_-]+:.*?##/ {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Initialize required Git submodules and verify reference inputs
	@git submodule update --init --recursive
	@test -d "$(REFERENCE_DIR)/published" || { echo "Missing IDTA template submodule at $(REFERENCE_DIR)" >&2; exit 1; }
	@test -f third_party/aas-core-works/aas-core-schema/schema.json || { echo "Missing AAS core schema at third_party/aas-core-works/aas-core-schema/schema.json" >&2; exit 1; }
	@if [ ! -x "$(VENV_PYTHON)" ]; then \
		echo "Creating virtual environment at $(VENV)"; \
		$(PYTHON) -m venv "$(VENV)"; \
	fi
	@"$(VENV_PYTHON)" -m pip install -e '.[dev]'
	@echo "Repository references and Python environment are ready."

templates: ## Copy only the required IDTA template JSON files to data/templates/<company>/
	@"$(VENV_PYTHON)" scripts/copy_templates.py \
		--company-config $(COMPANY_CONFIG) \
		--reference-dir $(REFERENCE_DIR) \
		--dest-dir $(TEMPLATES_DIR)

extract: ## Step 1: Extract complete workbook JSON from configured Excel files
	@bash scripts/run-stage.sh step1-extract $(COMPANY_OUTPUT_ROOT) "$(VENV_PYTHON)" -m excel_to_aasx.extract \
		--company-config $(COMPANY_CONFIG) \
		--output-dir $(COMPANY_OUTPUT_ROOT)/xlsx-json-step1

transform: extract ## Step 2: Map extracted JSON into official-template-shaped AAS JSON
	@bash scripts/run-stage.sh step2-transform $(COMPANY_OUTPUT_ROOT) "$(VENV_PYTHON)" -m excel_to_aasx.transform \
		--company-config $(COMPANY_CONFIG) \
		--input-dir $(COMPANY_OUTPUT_ROOT)/xlsx-json-step1 \
		--reference-dir $(REFERENCE_DIR) \
		--output-dir $(COMPANY_OUTPUT_ROOT)/xlsx-json-step2

validate: transform ## Step 3: Validate generated AAS JSON
	@bash scripts/run-stage.sh step3-validate $(COMPANY_OUTPUT_ROOT) "$(VENV_PYTHON)" -m excel_to_aasx.validate \
		--company-config $(COMPANY_CONFIG) \
		--input-dir $(COMPANY_OUTPUT_ROOT)/xlsx-json-step2 \
		--reference-dir $(REFERENCE_DIR) \
		--output-dir $(COMPANY_OUTPUT_ROOT)/xlsx-json-step3

package: validate ## Step 4: Package validated AAS JSON as AASX
	@bash scripts/run-stage.sh step4-package $(COMPANY_OUTPUT_ROOT) "$(VENV_PYTHON)" -m excel_to_aasx.package \
		--input-dir $(COMPANY_OUTPUT_ROOT)/xlsx-json-step2 \
		--validation-dir $(COMPANY_OUTPUT_ROOT)/xlsx-json-step3 \
		--output-dir $(COMPANY_OUTPUT_ROOT)/xlsx-json-step4

generate: package ## Run extraction through AASX packaging
	@echo "AASX packages : $(COMPANY_OUTPUT_ROOT)/aasx/"

collect: extract ## Collect Step 1 JSON outputs into one review folder
	@bash scripts/run-stage.sh collect-extraction $(COMPANY_OUTPUT_ROOT) "$(VENV_PYTHON)" -m excel_to_aasx.collect_extraction \
		--company-config $(COMPANY_CONFIG) \
		--output-root $(EXTRACTION_ROOT)

test: ## Run tests
	@PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$(VENV_PYTHON)" -m pytest tests
