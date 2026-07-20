# Documentation

This folder documents the standalone Excel-to-AASX generator.

## Read Order

1. `architecture.md`
2. `quickstart.md`
3. `third-party.md`
4. `limitations.md`

## Scope Boundary

```text
excel-to-aasx
  owns Excel extraction
  owns template mapping
  owns generated AAS JSON validation
  owns AASX packaging
  owns conversion reports and limitations

runtime repository
  owns BaSyx services
  owns deployment/readback
  owns registries, discovery, security, and cloud runtime work
```

Do not add BaSyx server, MongoDB, Keycloak, or cloud deployment logic to this
package. Those responsibilities belong to a runtime repository.
