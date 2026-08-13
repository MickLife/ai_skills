from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "codebase-architect-markdown"
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import render_diagrams  # noqa: E402
import validate_markdown  # noqa: E402
import deps_scan  # noqa: E402
import find_entry  # noqa: E402
import scan_tree  # noqa: E402


class RenderDiagramsTests(unittest.TestCase):
    def test_missing_mmdc_selects_mermaid_mode_without_creating_svg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            diagrams = Path(tmp)
            (diagrams / "system-context.mmd").write_text(
                "flowchart LR\n  User --> System\n", encoding="utf-8"
            )

            result = render_diagrams.render_directory(
                diagrams, executable="definitely-missing-mmdc"
            )

            self.assertEqual("mermaid", result["mode"])
            self.assertEqual([], result["rendered"])
            self.assertFalse((diagrams / "system-context.svg").exists())
            self.assertEqual(0, render_diagrams.result_exit_code(result))

    def test_available_renderer_creates_svg_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            diagrams = root / "diagrams"
            diagrams.mkdir()
            (diagrams / "flow.mmd").write_text(
                "flowchart LR\n  A --> B\n", encoding="utf-8"
            )
            def fake_run(command, **_kwargs):
                output = Path(command[command.index("-o") + 1])
                output.write_text(
                    '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                    encoding="utf-8",
                )
                return mock.Mock(returncode=0, stdout="", stderr="")

            with (
                mock.patch.object(render_diagrams, "_resolve_executable", return_value="mmdc"),
                mock.patch.object(render_diagrams.subprocess, "run", side_effect=fake_run),
            ):
                result = render_diagrams.render_directory(diagrams)

            self.assertEqual("svg", result["mode"])
            self.assertEqual(["flow.svg"], result["rendered"])
            self.assertTrue((diagrams / "flow.svg").exists())
            manifest = json.loads(
                (diagrams / "render-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual("svg", manifest["mode"])
            self.assertEqual(0, render_diagrams.result_exit_code(result))

    def test_renderer_failure_falls_back_and_returns_failure_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            diagrams = Path(tmp)
            (diagrams / "flow.mmd").write_text(
                "flowchart LR\n  A --> B\n", encoding="utf-8"
            )

            with (
                mock.patch.object(
                    render_diagrams, "_resolve_executable", return_value="mmdc"
                ),
                mock.patch.object(
                    render_diagrams.subprocess,
                    "run",
                    return_value=mock.Mock(
                        returncode=1, stdout="", stderr="invalid diagram"
                    ),
                ),
            ):
                result = render_diagrams.render_directory(diagrams)

            self.assertEqual("mermaid", result["mode"])
            self.assertEqual([], result["rendered"])
            self.assertEqual(
                [{"source": "flow.mmd", "message": "invalid diagram"}],
                result["errors"],
            )
            self.assertEqual(1, render_diagrams.result_exit_code(result))


class ValidateMarkdownTests(unittest.TestCase):
    def test_valid_document_passes_with_mermaid_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            diagrams = root / "diagrams"
            diagrams.mkdir()
            (diagrams / "context.mmd").write_text(
                "flowchart LR\n  User --> System\n", encoding="utf-8"
            )
            doc = root / "ARCHITECTURE.md"
            doc.write_text(
                "# 架构设计\n\n"
                "## 系统上下文\n\n"
                "**设计意图：** 展示系统边界。\n\n"
                "```mermaid\nflowchart LR\n  User --> System\n```\n\n"
                "**关键解读：** 用户调用系统。\n\n"
                "- 证据：`src/main.py:10`\n",
                encoding="utf-8",
            )

            errors = validate_markdown.validate_document(doc)

            self.assertEqual([], errors)

    def test_reports_placeholders_unclosed_fence_and_missing_asset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "ARCHITECTURE.md"
            doc.write_text(
                "# {{project_name}}\n\n"
                "![图](diagrams/missing.svg)\n\n"
                "```mermaid\nflowchart LR\n  A --> B\n",
                encoding="utf-8",
            )

            errors = validate_markdown.validate_document(doc)

            joined = "\n".join(errors)
            self.assertIn("占位符", joined)
            self.assertIn("代码围栏", joined)
            self.assertIn("资源不存在", joined)

    def test_warns_on_long_identifiers_inside_markdown_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "ARCHITECTURE.md"
            doc.write_text(
                "# 架构\n\n"
                "| 模块 | 文件 |\n"
                "| --- | --- |\n"
                "| core | src/core/engine/pipeline/stages/"
                "very_long_module_name/transform_handler.py |\n",
                encoding="utf-8",
            )

            errors = validate_markdown.validate_document(doc)

            self.assertTrue(any("宽表格" in item for item in errors))

    def test_diagram_without_intent_or_interpretation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "ARCHITECTURE.md"
            doc.write_text(
                "# 架构\n\n"
                "```mermaid\nflowchart LR\n  A --> B\n```\n",
                encoding="utf-8",
            )

            errors = validate_markdown.validate_document(doc)

            joined = "\n".join(errors)
            self.assertIn("设计意图", joined)
            self.assertIn("关键解读", joined)

    def test_long_path_in_list_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "ARCHITECTURE.md"
            doc.write_text(
                "# 架构\n\n"
                "- **位置：** `src/core/engine/pipeline/stages/"
                "very_long_module_name/transform_handler.py:42`\n",
                encoding="utf-8",
            )

            self.assertEqual([], validate_markdown.validate_document(doc))

    def test_reports_missing_local_document_and_mermaid_source_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "ARCHITECTURE.md"
            doc.write_text(
                "# 架构\n\n"
                "- [核心模块](modules/core.md)\n"
                "- [Mermaid 源码](diagrams/context.mmd)\n",
                encoding="utf-8",
            )

            errors = validate_markdown.validate_document(doc)

            joined = "\n".join(errors)
            self.assertIn("modules/core.md", joined)
            self.assertIn("diagrams/context.mmd", joined)

    def test_valid_svg_diagram_with_source_link_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            diagrams = root / "diagrams"
            diagrams.mkdir()
            (diagrams / "context.svg").write_text("<svg></svg>", encoding="utf-8")
            (diagrams / "context.mmd").write_text(
                "flowchart LR\n  User --> System\n", encoding="utf-8"
            )
            doc = root / "ARCHITECTURE.md"
            doc.write_text(
                "# 架构\n\n"
                "## 系统上下文\n\n"
                "**设计意图：** 展示系统边界。\n\n"
                "![系统上下文图](diagrams/context.svg)\n\n"
                "[Mermaid 源码](diagrams/context.mmd)\n\n"
                "**关键解读：** 用户调用系统。\n",
                encoding="utf-8",
            )

            self.assertEqual([], validate_markdown.validate_document(doc))


class AnalysisScriptTests(unittest.TestCase):
    def test_scan_find_entry_and_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "src" / "app"
            package.mkdir(parents=True)
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "main.py").write_text(
                "from src.app.worker import Worker\n\n"
                "class Service:\n"
                "    def run(self):\n"
                "        return Worker()\n",
                encoding="utf-8",
            )
            (package / "worker.py").write_text(
                "class Worker:\n    pass\n", encoding="utf-8"
            )
            native = root / "native"
            native.mkdir()
            (native / "engine.h").write_text("void run();\n", encoding="utf-8")
            (native / "engine.cpp").write_text(
                '#include "engine.h"\nvoid run() {}\n', encoding="utf-8"
            )

            inventory = scan_tree.scan(root)
            self.assertEqual(5, inventory["summary"]["file_count"])

            entry = find_entry.resolve(root, "src/app/main.py::Service.run")
            self.assertEqual("src/app/main.py", entry["file"])
            self.assertEqual(4, entry["line"])

            graph = deps_scan.scan(root)
            self.assertTrue(
                any(
                    edge.get("resolved") == "src/app/worker.py"
                    for edge in graph["edges"]
                )
            )
            self.assertTrue(
                any(
                    edge.get("resolved") == "native/engine.h"
                    for edge in graph["edges"]
                )
            )


if __name__ == "__main__":
    unittest.main()
