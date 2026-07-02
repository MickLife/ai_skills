"""Build multimodal input packages for cloud map quality inspection.

The package should include tiled assets, rendering instructions, semantic color
legend, enabled detector definitions, and strict output requirements.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build VLM input package for quality inspection.")
    parser.add_argument("--input-manifest", required=True, help="Input manifest JSON path.")
    parser.add_argument("--tile-manifest", required=True, help="Tile manifest JSON path.")
    parser.add_argument("--registry", required=True, help="Issue registry JSON path.")
    parser.add_argument("--semantic-legend", required=True, help="Semantic color legend markdown path.")
    parser.add_argument("--rendering-spec", required=True, help="Rendering spec markdown path.")
    parser.add_argument("--schema", required=True, help="Inspection result schema path.")
    parser.add_argument("--output", required=True, help="Output JSON package path.")
    args = parser.parse_args()

    manifest = json.loads(Path(args.input_manifest).read_text(encoding="utf-8"))
    tile_manifest = json.loads(Path(args.tile_manifest).read_text(encoding="utf-8"))
    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    enabled_checks = set(manifest["enabled_checks"])
    detector_definitions = {}

    registry_root = Path(args.registry).resolve().parent.parent
    for issue in registry.get("issues", []):
        if issue["issue_type"] not in enabled_checks:
            continue
        definition_path = registry_root / issue["definition_file"]
        detector_definitions[issue["issue_type"]] = {
            "metadata": issue,
            "definition": definition_path.read_text(encoding="utf-8"),
        }

    package = {
        "region_id": manifest["region_id"],
        "enabled_checks": manifest["enabled_checks"],
        "assets": manifest["assets"],
        "tile_manifest": tile_manifest,
        "semantic_legend": Path(args.semantic_legend).read_text(encoding="utf-8"),
        "rendering_spec": Path(args.rendering_spec).read_text(encoding="utf-8"),
        "detector_definitions": detector_definitions,
        "result_schema": json.loads(Path(args.schema).read_text(encoding="utf-8")),
        "model_instruction": (
            "请根据 enabled_checks 检查当前云端地图资产。先列出证据，再给出结论。"
            "只输出符合 inspection_result_schema 的 JSON，不要编造地图坐标、对象存储路径或不存在的资产。"
        ),
    }

    Path(args.output).write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
