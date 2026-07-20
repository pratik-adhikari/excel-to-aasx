SHELL := /bin/bash

COMPANY ?= schunk
COMPANY_CONFIG ?= configs/companies/$(COMPANY).json
COMPANY_OUTPUT_ROOT ?= data/generated/$(COMPANY)
REFERENCE_DIR ?= third_party/admin-shell-io/submodel-templates
EXTRACTION_ROOT ?= data/extraction

.DEFAULT_GOAL := help

.PHONY: help extract transform validate package generate collect test

help:
	@awk 'BEGIN {FS = ":.*##"; printf "excel-to-aasx commands:\n\n"} /^[a-zA-Z_-]+:.*?##/ {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

extract: ## Step 1: Extract complete workbook JSON from configured Excel files
	@python3 -m excel_to_aasx.extract \
		--company-config $(COMPANY_CONFIG) \
		--output-dir $(COMPANY_OUTPUT_ROOT)/xlsx-json-step1

transform: extract ## Step 2: Map extracted JSON into official-template-shaped AAS JSON
	@python3 -m excel_to_aasx.transform \
		--company-config $(COMPANY_CONFIG) \
		--input-dir $(COMPANY_OUTPUT_ROOT)/xlsx-json-step1 \
		--reference-dir $(REFERENCE_DIR) \
		--output-dir $(COMPANY_OUTPUT_ROOT)/xlsx-json-step2

validate: transform ## Step 3: Validate generated AAS JSON
	@python3 -m excel_to_aasx.validate \
		--company-config $(COMPANY_CONFIG) \
		--input-dir $(COMPANY_OUTPUT_ROOT)/xlsx-json-step2 \
		--reference-dir $(REFERENCE_DIR) \
		--output-dir $(COMPANY_OUTPUT_ROOT)/xlsx-json-step3

package: validate ## Step 4: Package validated AAS JSON as AASX
	@python3 -m excel_to_aasx.package \
		--input-dir $(COMPANY_OUTPUT_ROOT)/xlsx-json-step2 \
		--validation-dir $(COMPANY_OUTPUT_ROOT)/xlsx-json-step3 \
		--output-dir $(COMPANY_OUTPUT_ROOT)/xlsx-json-step4

generate: package ## Run extraction through AASX packaging
	@echo "AASX files generated under $(COMPANY_OUTPUT_ROOT)/xlsx-json-step4"

collect: extract ## Collect Step 1 JSON outputs into one review folder
	@python3 -m excel_to_aasx.collect_extraction \
		--company-config $(COMPANY_CONFIG) \
		--output-root $(EXTRACTION_ROOT)

test: ## Run tests
	@python3 -m pytest tests
