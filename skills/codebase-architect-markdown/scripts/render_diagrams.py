#!/usr/bin/env python3
"""Render Mermaid sources to SVG when a local mmdc executable is available."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _resolve_executable(executable: str) -> str | None:
    candidate = Path(executable)
    if candidate.is_file():
        return str(candidate.resolve())
    return shutil.which(executable)


def render_directory(
    diagrams_dir: Path,
    *,
    executable: str = "mmdc",
    config: Path | None = None,
) -> dict[str, Any]:
    """Render every .mmd file and write a machine-readable manifest.

    The function never installs dependencies and never performs network calls.
    If mmdc is unavailable, Mermaid source mode remains usable.
    """

    diagrams_dir = Path(diagrams_dir)
    diagrams_dir.mkdir(parents=True, exist_ok=True)
    sources = sorted(diagrams_dir.glob("*.mmd"))
    renderer = _resolve_executable(executable)
    result: dict[str, Any] = {
        "mode": "mermaid",
        "renderer": renderer,
        "sources": [item.name for item in sources],
        "rendered": [],
        "errors": [],
    }

    if renderer:
        for source in sources:
            output = source.with_suffix(".svg")
            command = [
                renderer,
                "-i",
                str(source),
                "-o",
                str(output),
                "-b",
                "transparent",
            ]
            if config is not None:
                command.extend(["-c", str(config)])
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode == 0 and output.is_file():
                result["rendered"].append(output.name)
            else:
                output.unlink(missing_ok=True)
                message = completed.stderr.strip() or completed.stdout.strip()
                result["errors"].append(
                    {"source": source.name, "message": message or "mmdc failed"}
                )

        if len(result["rendered"]) == len(sources) and not result["errors"]:
            result["mode"] = "svg"

    manifest = diagrams_dir / "render-manifest.json"
    manifest.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def result_exit_code(result: dict[str, Any]) -> int:
    """Treat an unavailable renderer as a normal Mermaid-mode fallback."""
    return 1 if result["errors"] else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render docs/diagrams/*.mmd to SVG with a preinstalled mmdc."
    )
    parser.add_argument(
        "--diagrams",
        type=Path,
        default=Path("docs/diagrams"),
        help="Directory containing Mermaid .mmd sources.",
    )
    parser.add_argument("--mmdc", default="mmdc", help="mmdc executable name/path.")
    parser.add_argument("--config", type=Path, help="Optional Mermaid config JSON.")
    args = parser.parse_args()

    result = render_directory(
        args.diagrams,
        executable=args.mmdc,
        config=args.config,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result_exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
