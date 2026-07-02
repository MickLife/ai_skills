"""Prepare and tile inspection assets.

This placeholder records the expected interface. Implement image tiling,
trajectory overlays, and tile metadata generation with project-specific tools.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare assets for cloud map quality inspection.")
    parser.add_argument("--input-manifest", required=True, help="Input manifest JSON path.")
    parser.add_argument("--registry", required=True, help="Issue registry JSON path.")
    parser.add_argument("--output-dir", required=True, help="Directory for generated tiles.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(Path(args.input_manifest).read_text(encoding="utf-8"))
    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    runtime_options = manifest.get("runtime_options", {})

    tile_manifest = {
        "status": "placeholder",
        "region_id": manifest["region_id"],
        "enabled_checks": manifest["enabled_checks"],
        "registered_issues": [issue["issue_type"] for issue in registry.get("issues", [])],
        "assets": manifest["assets"],
        "tile_size": runtime_options.get("tile_size", 1024),
        "overlap": runtime_options.get("overlap", 128),
        "tiles": [],
        "message": "TODO: tile image-like assets, prepare overlays, and generate per-tile metadata.",
    }

    (output_dir / "tile_manifest.json").write_text(
        json.dumps(tile_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
