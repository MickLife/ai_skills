---
name: codebase-architect
description: |
  分析 Python 和/或 C/C++ 代码库（单仓库或多仓库），产出自包含的设计文档。当用户要求"总结代码架构"、"生成设计文档/ARCHITECTURE"、"理解项目结构"、"梳理某个功能跨模块/跨仓库的链路"、"从入口函数/文件追踪设计"时使用。支持用户指定入口（函数、文件、类、方法）。Agent 无关：可在 Claude Code / Cursor / Codex / Gemini CLI 等任何符合 agentskills 规范的运行时内运行，借助宿主 agent 的模型与文件/grep/bash 工具完成。
author: pure_cursor
license: MIT
compatibility: |
  必需：文件系统访问（Read、Glob/Grep、Bash）+ 宿主 agent 自身 LLM。
  可选：Task/子代理工具，用于分层并行分解。
languages: python, c, cpp
---

# codebase-architect

为 Python / C/C++ 代码库产出自包含**设计文档**，原生支持**多仓库**布局与**入口驱动**分析。可在任意 coding agent 内运行，借助*宿主* agent 的模型 + 几个轻量静态分析脚本完成。

## 何时使用

- 用户说"总结这个代码库"、"梳理架构"、"生成设计文档 / ARCHITECTURE.md"。
- 为 Python 或 C/C++ 项目（或二者混合）出设计文档。
- 用户指向一个父目录下的多个仓库，希望看到跨仓关系。
- 用户指定具体入口——`--entry src/core/engine.py::run_pipeline`、`--entry handle_request`、`--entry MyClass.process`、`--entry src/server/main.c`——希望做聚焦追踪而非全量扫描。
- 用户刚接手陌生代码库，需要结构 + 设计层面的概览（而不只是 API 参考）。

## 启动前先收集的输入

向用户询问（或从工作区推断）：

1. **根路径**——单仓库目录，或包含多个仓库的父目录。
2. **入口点**（可选），支持以下任一形式：
   - `path/to/file.py` 或 `path/to/file.c`（整文件作为根）
   - `path/to/file.py::function_name`
   - `path/to/file.py::ClassName.method`
   - 裸符号名 `handle_request`（在根下 grep 解析）
3. **范围过滤**（可选）——`--include` / `--exclude` glob，例如 `*.cpp,*.h`、排除 `tests,build`。
4. **输出格式**——`markdown`（默认，可移植）或 `html`（自包含单文件 + 内联 SVG/Mermaid）。仅在不确定时询问。
5. **深度**——`overview`（快，单趟）或 `deep`（默认，完整四阶段）。除非库很大或用户要求快速，否则默认 `deep`。

若用户只给根路径，按 `deep` + `markdown` + 无入口过滤（全量模式）执行。

## 四阶段方法论（概要）

详见 `references/methodology.md`：

1. **侦察（Recon）**——运行 `scripts/scan_tree.py` 得到带每文件行数/token 估算的文件树（尊重 `.gitignore`）。识别技术栈、构建系统（CMake/Meson/Bazel/setuptools/poetry/pyproject）与仓库边界。多仓时按 `references/multi-repo.md` 清点每个兄弟仓。
2. **分解（Decompose）**——分层分解切分模块（借鉴 CodeWiki 的动态规划思路）：按目录 + 依赖内聚聚类，遵守每模块 token 预算（约 100k）。用 `scripts/deps_scan.py` 构建 Python import / C++ include 图驱动聚类。入口模式下，按用户根做可达闭包剪枝（调用者 + 被调用者 / include 树）——见 `references/methodology.md#入口模式`。
3. **深挖（Deep-dive）**——为每个模块（或每个入口子树）读真实代码出模块文档。若宿主有 Task/子代理工具，按每模块 token 预算并行派发（借鉴 cartographer-cursor）；否则顺序处理。语言专属阅读指南：`references/python-analysis.md`、`references/cpp-analysis.md`。
4. **合成与交付（Synthesize）**——把模块文档上卷成一份 `ARCHITECTURE`：系统总览、模块图、跨仓图（若多仓）、数据流、关键时序图、关键函数表、坑点、扩展点。使用 `templates/`。Mermaid 图必须先校验语法再写入。`html` 输出则内联 CSS + 手绘 SVG + 轻量 JS，无任何外部资源。

## 输出结构

默认（markdown）：

```
./docs/
├── ARCHITECTURE.md          # 顶层设计文档（从这里开始读）
├── modules/
│   ├── <module1>.md         # 模块级设计文档
│   └── <module2>.md
├── cross-repo-map.md        # 仅多仓时生成
├── module_tree.json         # 分层分解结果
├── entry-trace.json         # 仅入口模式：可达闭包
├── metadata.json            # 运行元数据（根、入口、时间戳）
└── index.html               # 仅 --output html 时生成
```

始终生成 `AGENTS.md`（一页快速参考 + 指向 `docs/ARCHITECTURE.md`），方便其他 agent 冷启动。

## 硬性规则

- **读真实代码。** 设计文档中每一条论断都要能追溯到实际打开过的文件。禁止臆造 API、模块或行为。
- **校验图表。** 每个 Mermaid 代码块写入前必须语法自检。HTML 输出中，顶层架构图优先手绘内联 SVG（借鉴 codebase-summary）；时序/数据流再用 Mermaid。
- **标注文件路径。** 关键函数表与坑点中必须给出相对路径 + 行范围。
- **遵守预算。** 模块超预算就继续递归拆分，绝不静默截断。
- **Agent 无关。** 交付物中不得出现 Cursor/Claude/Codex 等产品名。SKILL 正文里按能力称呼工具（"若可用子代理/Task 工具"）。

## 如何调用辅助脚本

脚本均为标准库 Python 3.8+，向 stdout 输出 JSON，通过宿主 agent 的 Bash 工具运行。

```bash
# 侦察：文件树 + token/行数估算，尊重 .gitignore
python scripts/scan_tree.py --root /path/to/repo [--include "*.py,*.cpp,*.h"] [--exclude "tests,build"]

# 入口解析：定位匹配用户入口规格的文件/符号
python scripts/find_entry.py --root /path/to/repo --entry "src/core/engine.py::run_pipeline" --entry "handle_request"

# 依赖图：Python import + C/C++ #include 边
python scripts/deps_scan.py --root /path/to/repo --format json
```

脚本只采集**结构化事实**；**设计层面的解读**由 agent 完成。三个脚本均为纯标准库、可离线运行。

## 多仓库模式

当根目录包含多个仓库目录（根下无单一 `.git`，或多个兄弟目录各有 `.git`）：

1. 清点每个兄弟仓（由构建文件 + 入口线索推断角色）。
2. 按优先级扫描：共享头/契约 → 核心库 → 服务 → 前端/工具（见 `references/multi-repo.md`）。
3. 映射跨仓边：跨仓 Python import、跨仓 `#include` 共享头、构建系统跨仓依赖（CMake `add_subdirectory`/FetchContent、Bazel external repo、pip -e 安装）。
4. 产出 `cross-repo-map.md` + 一张以仓库为一等节点的顶层架构图。

## 入口模式

用户指定入口时，**不做全量扫描**：

1. 用 `find_entry.py` 把每个入口解析到具体文件/符号。
2. 在依赖图上做前向 + 反向可达闭包（被调用者 + 调用者 / include 树）——见 `references/methodology.md#入口模式`。
3. 产出聚焦该闭包的设计文档：控制流、数据流、关键协作者、主路径时序图。附"未分析部分"小节，明确范围边界。

## 参考文档（按需加载）

- `references/methodology.md`——完整四阶段、分层分解、token 预算、动态委派、入口闭包算法。
- `references/python-analysis.md`——Python 静态分析要点：包、`__init__.py`、相对/绝对 import、pyproject/setuptools/poetry、类型、异步入口。
- `references/cpp-analysis.md`——C/C++ 静态分析要点：翻译单元、include 图、前向声明、CMake/Meson/Bazel target、链接/ABI、模板、RAII。
- `references/multi-repo.md`——仓库清点、优先扫描顺序、跨仓边映射。
- `references/output-format.md`——ARCHITECTURE / 模块 / 跨仓文档的字段级规范。
- `templates/`——以此为起点复制，不要覆盖 `.tmpl` 原文件。

## 执行清单

- [ ] 收集根路径、入口（若有）、范围过滤、输出格式、深度。
- [ ] 运行 `scan_tree.py`；记录 token 预算与模块计划。
- [ ] （多仓）清点仓库，确认父目录布局。
- [ ] （入口）解析根，计算可达闭包。
- [ ] 用 `deps_scan.py` 构建依赖图。
- [ ] 产出各模块文档（有子代理则并行）。
- [ ] 合成 `ARCHITECTURE.md` + `AGENTS.md`；校验所有 Mermaid。
- [ ] （多仓）产出 `cross-repo-map.md`。
- [ ] 写 `metadata.json`（根、入口、时间戳、所用模型）。
- [ ] 核对每条论断都有 file:line 引用。
