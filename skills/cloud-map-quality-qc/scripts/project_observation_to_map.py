"""Project model observations to map coordinates.

This placeholder defines the deterministic boundary between model output and
map coordinates. The VLM should provide tile-local observations; this script
should compute map coordinates from trusted metadata.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Project inspection observations to map coordinates.")
    parser.add_argument("--observation-json", required=True, help="Model observation or result JSON path.")
    parser.add_argument("--tile-manifest", required=True, help="Tile manifest or metadata JSON path.")
    parser.add_argument("--output", required=True, help="Output JSON path with projected locations.")
    args = parser.parse_args()

    observation = json.loads(Path(args.observation_json).read_text(encoding="utf-8"))
    tile_manifest = json.loads(Path(args.tile_manifest).read_text(encoding="utf-8"))

    projected = {
        "status": "placeholder",
        "observation": observation,
        "tile_manifest": tile_manifest,
        "message": "TODO: compute map locations from tile_refs, pixel bboxes, polygons, polylines, or coverage cells.",
    }

    Path(args.output).write_text(json.dumps(projected, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
