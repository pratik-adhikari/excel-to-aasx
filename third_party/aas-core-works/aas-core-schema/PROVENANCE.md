# AAS Core JSON Schema Provenance

`schema.json` is a vendored generated artifact used by
`excel_to_aasx.validate` for JSON Schema validation.

It was copied from:

```text
Repository: https://github.com/aas-core-works/aas-core-codegen
Commit: e1de3f45216ce8b5dd116367a8668dd7f9e29a9a
Path: dev/test_data/main/jsonschema/expected/aas_core_meta.v3/expected_output/schema.json
```

The upstream generator test data records this AAS meta-model source:

```text
Repository: https://github.com/aas-core-works/aas-core-meta
Commit: f1d97f60b34d2dc97a8004ccfb3fc28487b91c7a
Path: aas_core_meta/v3.py
```

The full `aas-core-codegen` repository is intentionally not vendored. The
pipeline needs only this generated schema file at runtime.
