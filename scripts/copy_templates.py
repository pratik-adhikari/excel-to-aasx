"""
scripts/copy_templates.py
─────────────────────────
Copy only the IDTA template JSON files that are actually referenced in the
company config (one per sheet) out of the large third_party submodel-templates
repo into a small, project-specific directory.

This avoids committing or shipping the entire 147 MB vendor repo; only the
5 (or however many) files the pipeline uses are materialised in data/templates/.

Usage (called by `make templates`):
    python3 scripts/copy_templates.py \
        --company-config  configs/companies/schunk.json \
        --reference-dir   third_party/admin-shell-io \
        --dest-dir        data/templates/schunk
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from excel_to_aasx.company_config import load_company_config


def load_config(path: Path) -> dict:
    """Load the same fully merged configuration used by pipeline stages."""
    return load_company_config(path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy required IDTA template files from the vendor tree to a compact directory."
    )
    parser.add_argument("--company-config", type=Path, required=True,
                        help="Path to configs/companies/<company>.json")
    parser.add_argument("--reference-dir", type=Path, required=True,
                        help="Root of the admin-shell-io submodel-template submodule")
    parser.add_argument("--dest-dir", type=Path, required=True,
                        help="Destination directory for copied template files")
    args = parser.parse_args()

    config = load_config(args.company_config)
    sheets = config.get("sheets", [])

    if not sheets:
        raise SystemExit(
            "company config declares no sheets; refusing to create an incomplete template set"
        )

    args.dest_dir.mkdir(parents=True, exist_ok=True)

    copied_sources: dict[str, Path] = {}
    missing: list[str] = []
    for sheet in sheets:
        template_rel = sheet.get("template")
        if not template_rel:
            missing.append(f"sheet {sheet.get('sheet')!r} has no 'template' key")
            continue
        src = args.reference_dir / template_rel
        if not src.is_file():
            missing.append(str(src))
            continue
        dst = args.dest_dir / Path(template_rel).name
        previous_source = copied_sources.get(dst.name)
        if previous_source is not None and previous_source != src:
            raise SystemExit(
                "template filename collision: "
                f"{previous_source} and {src} would overwrite {dst}"
            )
        if previous_source is not None:
            continue
        shutil.copy2(src, dst)
        copied_sources[dst.name] = src
        print(f"  copied  {dst}")

    if missing:
        missing_text = "\n".join(f"  - {item}" for item in missing)
        raise SystemExit(f"missing {len(missing)} configured template file(s):\n{missing_text}")

    print(f"\nTemplates ready in {args.dest_dir}/")
    print(f"({len(sheets)} file(s) — only what the pipeline needs, not the full vendor tree)")


if __name__ == "__main__":
    main()
