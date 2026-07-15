# excel-to-aasx

Auditable Excel-to-AASX generation pipeline.

Planned scope:

```text
Excel workbook
  -> complete neutral JSON extraction
  -> official template matching
  -> template-shaped AAS JSON
  -> validation
  -> AASX package
```

This project should stay independent from any BaSyx server/runtime deployment.
Server repositories can consume the generated `.aasx` files or call this tool
from CI.
