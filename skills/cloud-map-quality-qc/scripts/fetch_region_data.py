"""Fetch cloud map inspection assets from object storage.

This is a placeholder script. Wire it to the project's object storage SDK before
using it in production.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch assets for cloud map quality inspection.")
    parser.add_argument("--input-manifest", required=True, help="Input manifest JSON path or object storage URI.")
    parser.add_argument("--output-dir", required=True, help="Local output directory.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = Path(args.input_manifest)
    manifest = None
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    placeholder_manifest = {
        "region_id": manifest.get("region_id") if manifest else None,
        "source_manifest": args.input_manifest,
        "enabled_checks": manifest.get("enabled_checks", []) if manifest else [],
        "assets": manifest.get("assets", []) if manifest else [],
        "status": "placeholder",
        "message": "TODO: connect to object storage and download only the assets required by enabled checks.",
    }

    (output_dir / "input_manifest.local.json").write_text(
        json.dumps(placeholder_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
