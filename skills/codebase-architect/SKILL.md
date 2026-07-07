---
name: codebase-architect
description: |
  分析 Python 和/或 C/C++ 代码库（单仓库或多仓库），产出自包含的 HTML 架构设计文档。当用户要求"总结代码架构"、"生成设计文档/ARCHITECTURE"、"理解项目结构"、"梳理某个功能跨模块/跨仓库的链路"、"从入口函数/文件追踪设计"时使用。支持用户指定入口（函数、文件、类、方法）。文档从代码提炼整架构级抽象（系统 I/O、核心概念、处理阶段），按 4+1 视图 / UML / DFD / 泳道图组织，浅色暖色调、带左侧自动目录。Agent 无关：可在 Claude Code / Cursor / Codex / Gemini CLI 等任何符合 agentskills 规范的运行时内运行，借助宿主 agent 的模型与文件/grep/bash 工具完成。
author: pure_cursor
license: MIT
compatibility: |
  必需：文件系统访问（Read、Glob/Grep、Bash）+ 宿主 agent 自身 LLM。
  可选：Task/子代理工具，用于分层并行分解。
languages: python, c, cpp
---

# codebase-architect

为 Python / C/C++ 代码库产出**单文件 HTML 架构设计文档**，原生支持**多仓库**布局与**入口驱动**分析。核心不是逐文件罗列，而是**从代码提炼整架构级抽象**，再用 4+1 视图 / UML / DFD / 泳道图表达。可在任意 coding agent 内运行，借助*宿主* agent 的模型 + 几个轻量静态分析脚本完成。

## 何时使用

- 用户说"总结这个代码库"、"梳理架构"、"生成设计文档 / ARCHITECTURE"。
- 为 Python 或 C/C++ 项目（或二者混合）出架构设计文档。
- 用户指向一个父目录下的多个仓库，希望看到跨仓关系。
- 用户指定具体入口——`--entry src/core/engine.py::run_pipeline`、`--entry handle_request`、`--entry MyClass.process`、`--entry src/server/main.c`——希望做聚焦追踪而非全量扫描。
- 用户刚接手陌生代码库，需要架构设计层面的概览（而不只是 API 参考）。

## 启动前先收集的输入

向用户询问（或从工作区推断）：

1. **根路径**——单仓库目录，或包含多个仓库的父目录。
2. **入口点**（可选），支持以下任一形式：
   - `path/to/file.py` 或 `path/to/file.c`（整文件作为根）
   - `path/to/file.py::function_name`
   - `path/to/file.py::ClassName.method`
   - 裸符号名 `handle_request`（在根下 grep 解析）
3. **范围过滤**（可选）——`--include` / `--exclude` glob，例如 `*.cpp,*.h`、排除 `tests,build`。
4. **深度**——`overview`（快，单趟）或 `deep`（默认，完整四阶段）。除非库很大或用户要求快速，否则默认 `deep`。

输出格式固定为 **HTML**（单文件、浅色暖色调、左侧自动目录）。若用户只给根路径，按 `deep` + 无入口过滤（全量模式）执行。

## 四阶段方法论（概要）

详见 `references/methodology.md`：

1. **侦察（Recon）**——运行 `scripts/scan_tree.py` 得到带每文件行数/token 估算的文件树（尊重 `.gitignore`）。识别技术栈、构建系统（CMake/Meson/Bazel/setuptools/poetry/pyproject）与仓库边界。多仓时按 `references/multi-repo.md` 清点每个兄弟仓。
2. **分解（Decompose）**——分层分解切分模块（借鉴 CodeWiki 的动态规划思路）：按目录 + 依赖内聚聚类，遵守每模块 token 预算（约 100k）。用 `scripts/deps_scan.py` 构建 Python import / C++ include 图驱动聚类。超预算模块标记 `needs_split`，留待子模块章展开。入口模式下按用户根做可达闭包剪枝——见 `references/methodology.md#入口模式`。
3. **深挖（Deep-dive）**——为每个模块（或每个入口子树）读真实代码，提炼设计事实（职责、I/O 契约、关键函数/类型、内部设计、依赖、坑点）。若宿主有 Task/子代理工具，按每模块 token 预算并行派发（借鉴 cartographer-cursor）；否则顺序处理。语言专属阅读指南：`references/python-analysis.md`、`references/cpp-analysis.md`。
4. **合成与交付（Synthesize）**——**先提炼架构级抽象**（系统边界与 I/O、核心领域概念、关键处理阶段、质量属性、设计决策），**再按 4+1 视图组织章节并为每种意图选合理视图**（类图/状态图/时序图/泳道图/组件图/部署图/DFD），复杂模块在"子模块详细设计"章展开。产出单一 HTML。视图选型见 `references/architecture-views.md`，章节规范见 `references/output-format.md`。

## 文档章节结构（HTML）

不是浮于代码表面的目录，而是整架构设计。骨架（按项目类型裁剪，详见 `output-format.md`）：

1. 引言（目的/读者、系统定位、范围与非目标）
2. **架构级抽象（核心）**：系统上下文黑盒 I/O、输入/输出契约表、核心领域概念（类图/ER）、关键处理阶段、质量属性与约束
3. 场景视图（+1 用例）
4. 逻辑视图（类图、状态图）
5. 进程视图（时序图、泳道图、并发通信）
6. 开发视图（组件/包图、模块清单、依赖）
7. 物理视图（部署图，可选）
8. 数据流视图 DFD（上下文图→分层，数据加工型必写）
9. 子模块详细设计（复杂时逐个展开）
10. 横切关注
11. 关键设计决策与权衡
12. 附录（术语表、未分析部分、参考）

多仓时插入"跨仓视图"章（仓库清单、跨仓依赖图、跨仓边详表、契约消费图）。

## 输出结构

```
./docs/
├── ARCHITECTURE.html        # 唯一交付物：单文件自包含设计文档（含全部章节 + 子模块章节）
├── module_tree.json         # 分层分解结果（数据）
├── entry-trace.json         # 仅入口模式：可达闭包（数据）
├── metadata.json            # 运行元数据（数据）
└── assets/                  # 可选：仅当选择本地内联 mermaid.min.js 做离线渲染时
```

只产出 HTML 设计文档；JSON 为结构化数据 sidecar，不产出任何 `.md` 文档。

## 硬性规则

- **先抽象后视图。** 先从代码提炼架构级抽象（I/O、核心概念、处理阶段），再选视图画图。禁止把文档写成逐文件流水账。
- **读真实代码。** 每一条论断都要能追溯到实际打开过的文件。禁止臆造 API、模块或行为。
- **不臆测，诚实标注缺口。** 若某设计共识/设计要点（如设计意图、非功能目标、历史约束、外部契约语义等）无法从代码或用户提供的上下文中提炼出证据，**禁止推测或凭经验编造**，必须显式标注"无法从代码中提取"（HTML 用 `<span class="badge unknown">无法从代码中提取</span>` 或 `.callout-unknown` 块），并尽量说明缺什么、为何无法判定、建议的确认途径。宁可留白标注，也不要用看似合理的猜测污染文档。
- **视图要有依据。** 每个视图对应真实设计意图，按 `architecture-views.md` 选型；没有真实依据的图不要硬画。
- **校验图表。** 每个 Mermaid 块写入前必须语法自检（`architecture-views.md#七`）。顶层系统上下文图可选手绘内联 SVG。
- **HTML 规范。** 单文件自包含、浅色暖色调、左侧自动目录可跳转、样式元素齐备（h1–h4/图片/表格/多级列表/代码块/加粗/斜体/内联代码）。
- **标注文件路径。** 关键函数表、坑点、决策表等必须给出 `path:line`。
- **遵守预算。** 模块超预算就标 `needs_split` 并在子模块章递归展开，绝不静默截断。
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

脚本只采集**结构化事实**；**架构级解读与视图化**由 agent 完成。三个脚本均为纯标准库、可离线运行。

## 多仓库模式

当根目录包含多个仓库目录（根下无单一 `.git`，或多个兄弟目录各有 `.git`）：

1. 清点每个兄弟仓（由构建文件 + 入口线索推断角色）。
2. 按优先级扫描：共享头/契约 → 核心库 → 服务 → 前端/工具（见 `references/multi-repo.md`）。
3. 映射跨仓边：跨仓 Python import、跨仓 `#include` 共享头、构建系统跨仓依赖（CMake `add_subdirectory`/FetchContent、Bazel external repo、pip -e 安装）。
4. 在 HTML 中加入"跨仓视图"章：仓库为一等节点的跨仓依赖图 + 跨仓边详表 + 契约消费图。

## 入口模式

用户指定入口时，**不做全量扫描**：

1. 用 `find_entry.py` 把每个入口解析到具体文件/符号。
2. 在依赖图上做前向 + 反向可达闭包（被调用者 + 调用者 / include 树）——见 `references/methodology.md#入口模式`。
3. 产出聚焦该闭包的设计文档：以主入口路径的时序图/泳道图为中心，配控制流、数据流、关键协作者。附"未分析部分"小节，明确范围边界。

## 参考文档（按需加载）

- `references/methodology.md`——完整四阶段、分层分解、token 预算、动态委派、入口闭包算法、合成与视图化。
- `references/architecture-views.md`——**架构级抽象提炼** + 4+1 视图 / UML / DFD / 泳道图选型与 Mermaid 表达。
- `references/output-format.md`——HTML 单文件设计文档的章节结构与字段规范。
- `references/python-analysis.md`——Python 静态分析要点：包、`__init__.py`、相对/绝对 import、pyproject/setuptools/poetry、类型、异步入口。
- `references/cpp-analysis.md`——C/C++ 静态分析要点：翻译单元、include 图、前向声明、CMake/Meson/Bazel target、链接/ABI、模板、RAII。
- `references/multi-repo.md`——仓库清点、优先扫描顺序、跨仓边映射。
- `templates/architecture.html.tmpl`——主文档模板（暖色主题 + 左侧目录 + 全元素样式 + 章节骨架）。
- `templates/submodule-section.html.tmpl`——子模块章节 partial。以模板为起点复制，不要覆盖原文件。

## 执行清单

- [ ] 收集根路径、入口（若有）、范围过滤、深度。
- [ ] 运行 `scan_tree.py`；记录 token 预算与模块计划。
- [ ] （多仓）清点仓库，确认父目录布局。
- [ ] （入口）解析根，计算可达闭包。
- [ ] 用 `deps_scan.py` 构建依赖图；标记 `needs_split` 模块。
- [ ] 深挖各模块提炼设计事实（有子代理则并行）。
- [ ] **提炼架构级抽象**：系统 I/O、核心概念、处理阶段、质量属性、设计决策。
- [ ] 按 4+1/DFD/UML/泳道图为每种意图选视图；复杂模块展开子模块章。
- [ ] 用 `architecture.html.tmpl` 合成单文件 HTML；校验所有 Mermaid、左侧目录可跳转、配色与样式达标。
- [ ] 写 `metadata.json`（含 `views_included`、`submodules_expanded`）。
- [ ] 核对每条论断都有 file:line 引用；无法提取的设计点已标注"无法从代码中提取"，全文无臆测内容。
