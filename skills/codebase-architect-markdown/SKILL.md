---
name: codebase-architect-markdown
description: Use when a user asks to summarize, explain, map, or document a Python/C/C++ codebase or selected entry points as Markdown, including multi-repository architecture and design views.
license: MIT
compatibility: OpenCode and Agent Skills-compatible coding agents with file read, search, and shell access; optional subagents and mmdc.
metadata:
  output-format: markdown
  primary-languages: python,c,cpp
---

# Markdown Codebase Architect

从真实代码提炼架构，输出可移植的 Markdown 文档。支持单仓、多仓、指定函数/文件入口。GLM 等模型负责分析；图是否渲染由阅读器或本地 `mmdc` 决定。

## 输入

先确定：

1. 根路径：单仓或多仓父目录。
2. 可选入口：`file`、`file::function`、`file::Class.method`、裸符号。
3. 可选过滤：include/exclude glob。
4. 深度：`overview` 或默认 `deep`。

主语言不是 Python/C/C++ 时，先说明深度分析能力有限。

## 流程

1. **侦察**：运行 `scan_tree.py`，识别规模、语言、构建系统、仓库边界。超大项目先请用户缩小范围、指定入口或改用 `overview`。
2. **分解**：运行 `deps_scan.py`；按目录与依赖关系划分模块。入口模式只保留与入口相关的文件。
3. **深挖**：读真实代码，记录模块职责、输入输出、关键类型/函数、运行路径、依赖与风险；可并行分析独立模块。
4. **合成**：先写系统边界、输入输出、核心概念与处理阶段，再按需选择设计视图。用 `templates/ARCHITECTURE.md.tmpl` 生成文档并运行校验。

完整方法见 `references/methodology.md`。

## 图的混合输出

每张图以 `docs/diagrams/<name>.mmd` 为唯一源：

- 本地存在 `mmdc`：运行 `render_diagrams.py`，正文嵌入 SVG，并链接 `.mmd`。
- 没有 `mmdc`：正文直接使用 Mermaid 围栏，不安装依赖、不联网。
- 图前写“设计意图”，图后写“关键解读”；任何环境不显示图时，正文仍须独立可懂。

图形选择、兼容语法见 `references/architecture-views.md` 和 `references/diagram-patterns.md`。

## 硬性规则

- 只写能由代码或用户上下文支持的结论，并附 `path:line`；无法确认时明确写“无法从代码中提取”。
- 视图章节是菜单，不是清单；没有内容就删除。
- Mermaid 使用保守语法，不写自定义颜色、HTML 标签、点击事件；单图顶层节点不超过 9 个。
- Markdown 表格只放短字段；长类名、文件路径、模块名用列表或独立段落。
- 不依赖 Cursor 专属工具名，不调用外部绘图 API。
- 模块超出预算就拆分，不静默截断。

## 工具

```bash
python scripts/scan_tree.py --root /path
python scripts/find_entry.py --root /path --entry "src/main.py::main"
python scripts/deps_scan.py --root /path --format json
python scripts/render_diagrams.py --diagrams docs/diagrams --config templates/mermaid-config.json
python scripts/validate_markdown.py docs/ARCHITECTURE.md
```

## 按需参考

- `references/methodology.md`：四阶段、入口范围、多仓、模块拆分、质量门。
- `references/output-format.md`：章节菜单、排版、长标识符、混合图嵌入。
- `references/architecture-views.md`：抽象提炼、视图选择、不臆测。
- `references/diagram-patterns.md`：兼容 Mermaid 模板。
- `references/python-analysis.md`、`cpp-analysis.md`：语言专项。
- `references/multi-repo.md`：多仓扫描与跨仓关系。

## 输出

```text
docs/
├── ARCHITECTURE.md
├── diagrams/*.mmd
├── diagrams/*.svg          # 仅 mmdc 可用时
├── modules/*.md            # 仅复杂模块需要拆分时
├── module_tree.json
├── entry-trace.json        # 仅入口模式
└── metadata.json
```

完成前删除未用章节和占位符，连续编号，运行 `validate_markdown.py`。文档中不得引用不存在的 SVG。
