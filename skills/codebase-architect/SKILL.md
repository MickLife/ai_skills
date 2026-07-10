---
name: codebase-architect
description: |
  分析 Python 和/或 C/C++ 代码库（单仓库或多仓库），产出自包含的 HTML 架构设计文档。当用户要求"总结代码架构"、"生成设计文档/ARCHITECTURE"、"理解项目结构"、"梳理某个功能跨模块/跨仓库的链路"、"从入口函数/文件追踪设计"时使用。支持用户指定入口（函数、文件、类、方法）。文档从代码提炼整架构级抽象（系统 I/O、核心概念、处理阶段），并**按需**从 4+1 视图 / UML / DFD / 泳道图中选用合理视图表达（视图章节按内容裁剪，不是必填清单），浅色暖色调、带左侧自动目录。Agent 无关：可在 Claude Code / Cursor / Codex / Gemini CLI 等任何符合 agentskills 规范的运行时内运行，借助宿主 agent 的模型与文件/grep/bash 工具完成。
author: pure_cursor
license: MIT
compatibility: |
  必需：文件系统访问（Read、Glob/Grep、Bash）+ 宿主 agent 自身 LLM。
  可选：Task/子代理工具，用于分层并行分解。
languages: python, c, cpp
---

# codebase-architect

为 Python / C/C++ 代码库产出**单文件 HTML 架构设计文档**，原生支持**多仓库**布局与**入口驱动**分析。核心不是逐文件罗列，而是**从代码提炼整架构级抽象**，再**按需**用 4+1 视图 / UML / DFD / 泳道图表达。可在任意 coding agent 内运行，借助*宿主* agent 的模型 + 几个轻量静态分析脚本完成。

> 本文是入口与路由：只给"何时用、要什么输入、走哪几步、遵守哪些规则、去读哪份参考"。细节都在 `references/`，按需加载，不在此复述。

## 何时使用

- 用户说"总结这个代码库"、"梳理架构"、"生成设计文档 / ARCHITECTURE"。
- 为 Python 或 C/C++ 项目（或二者混合）出架构设计文档。
- 用户指向一个父目录下的多个仓库，希望看到跨仓关系。
- 用户指定具体入口（`--entry src/core/engine.py::run_pipeline`、`--entry handle_request`、`--entry MyClass.process`、`--entry src/server/main.c`），希望聚焦追踪而非全量扫描。
- 用户刚接手陌生代码库，需要架构设计层面的概览（而不只是 API 参考）。

**不适用 / 需降级并提醒用户：**

- 主语言非 Python/C/C++（如以 Rust/Go/JS/TS 为主）：脚本只解析 py/c/cpp，其余语言只能作为**边界/外部依赖**标注，深度分析能力有限——如实告知。
- 纯配置/资源/数据仓、无实质逻辑：给最小结构说明即可，不硬套视图。
- 超大 monorepo / 多仓且未指定入口：先建议缩小范围或改用入口模式（见"规模护栏"）。

## 启动前先收集的输入

向用户询问（或从工作区推断）：

1. **根路径**——单仓库目录，或包含多个仓库的父目录。
2. **入口点**（可选）——`file`、`file::function`、`file::Class.method`、或裸符号名（在根下 grep 解析）。
3. **范围过滤**（可选）——`--include` / `--exclude` glob，例如 `*.cpp,*.h`、排除 `tests,build`。
4. **深度**——`overview` 或 `deep`（默认）：
   - `overview`：引言 + 架构级抽象 + 开发视图（模块图/清单）+ 附录，图从简，不逐模块深挖、不展开子模块。
   - `deep`：完整四阶段 + 按需视图 + 复杂模块子模块章。

输出格式固定为 **HTML**（单文件、浅色暖色调、左侧自动目录）。若用户只给根路径，按 `deep` + 全量模式执行。

**规模护栏**：先看 `scan_tree.py` 的 `estimated_modules` / 总 token。若整体规模远超预算（模块数很多、总量数百万 token），**先停下与用户确认**：缩小范围、指定入口、或改用 `overview`——不要默默硬啃全量。

## 四阶段方法论

完整流程、token 预算、分层分解、动态拆分派发、失败降级见 `references/methodology.md`。概览：

1. **侦察**——`scripts/scan_tree.py`：文件树 + token 估算、构建系统、仓库边界。
2. **分解**——`scripts/deps_scan.py`：依赖图驱动分层聚类；超预算模块标 `needs_split`。入口模式改为只保留与入口相关的文件。
3. **深挖**——读真实代码，逐模块提炼设计事实（有子代理则并行）。
4. **合成**——**先提炼架构级抽象，再按需选视图**，产出单一 HTML（模板 `templates/architecture.html.tmpl`）。

## 文档章节结构

文档是整架构设计，不是逐文件罗列。**视图章节是候选菜单，不是必填清单**：有对应设计内容才纳入，否则删章（空视图硬填＝变相臆测），最终**动态连续编号**。

- **必写骨架**：引言 + 架构级抽象（系统 I/O、核心领域概念、关键处理阶段、质量属性）+ 附录（含"无法提取的设计点"）。
- **按需**：场景 / 逻辑 / 进程 / 开发 / 物理 / DFD / 通用机制 / 决策 / 子模块 / 跨仓视图。

完整菜单、裁剪原则、字段规范、JSON sidecar 见 `references/output-format.md`；抽象提炼与视图选型见 `references/architecture-views.md`。

## 输出结构

```
./docs/
├── ARCHITECTURE.html        # 唯一交付物：单文件自包含设计文档
├── module_tree.json         # 分层分解结果（数据）
├── entry-trace.json         # 仅入口模式：与入口相关的文件集合（数据）
├── metadata.json            # 运行元数据（数据）
└── assets/                  # 可选：仅当本地内联 mermaid.min.js 做离线渲染时
```

只产出 HTML 设计文档；JSON 为结构化数据 sidecar，不产出任何 `.md` 文档。

## 硬性规则

- **先抽象后视图。** 先提炼架构级抽象（I/O、核心概念、处理阶段），再选视图画图；禁止写成逐文件流水账。
- **读真实代码。** 每条论断可追溯到实际打开过的文件（附 `path:line`）；禁止臆造 API、模块、行为。
- **不臆测。** 提炼不出的设计点标注"无法从代码中提取"，不推测、不凭经验补全（政策见 `architecture-views.md#一`，HTML 标记见 `output-format.md`）。
- **视图按需，空则删章。** 没内容就删掉该视图章，禁止占位符/套话硬填（＝变相臆测）。
- **图必有解读。** 图前讲设计意图、图后给关键点；单图顶层节点 > 9 就拆分/分层（自检见 `architecture-views.md#七`）。
- **HTML 规范。** 单文件自包含、浅色暖色调、左侧自动目录可跳转、元素样式齐备（详见 `output-format.md`）。
- **遵守预算。** 模块超预算就标 `needs_split` 并在子模块章递归展开，绝不静默截断。
- **Agent 无关。** 交付物不出现 Cursor/Claude/Codex 等产品名；按能力称呼工具。

## 如何调用辅助脚本

脚本均为标准库 Python 3.8+，向 stdout 输出 JSON，通过宿主 agent 的 Bash 工具运行；只采集结构化事实，架构级解读由 agent 完成。

```bash
python scripts/scan_tree.py --root /path [--include "*.py,*.cpp,*.h"] [--exclude "tests,build"]
python scripts/find_entry.py --root /path --entry "src/core/engine.py::run_pipeline" --entry "handle_request"
python scripts/deps_scan.py --root /path --format json
```

## 多仓库模式

根下无单一 `.git`、或多个兄弟目录各有 `.git` → 多仓模式：清点仓库 → 按"契约/共享头 → 核心库 → 服务 → 工具"优先级扫描 → 映射跨仓边 → 加"跨仓视图"章。完整方法见 `references/multi-repo.md`。

## 入口模式

用户指定入口时**不做全量扫描**：`find_entry.py` 解析入口 → 顺依赖关系找出与入口相关的文件（它调用的 + 调用它的）→ 采用精简章节集（局部 I/O + 以主路径为中心的进程视图 + 附"未分析部分"）。算法见 `references/methodology.md#入口模式`。

## 参考文档（按需加载）

- `references/methodology.md`——四阶段全流程、token 预算、分层分解、动态拆分派发、入口关联范围、失败降级、质量门。
- `references/architecture-views.md`——**架构级抽象提炼**（含诚实标注政策）+ 4+1/UML/DFD/泳道图选型 + Mermaid 自检。
- `references/output-format.md`——HTML 章节菜单与裁剪原则、字段规范、无法提取标记、JSON sidecar 结构。
- `references/python-analysis.md`——Python 静态分析要点（包/import/类型/异步/跨语言调用）。
- `references/cpp-analysis.md`——C/C++ 静态分析要点（TU/include 图/构建 target/链接 ABI/模板/RAII）。
- `references/multi-repo.md`——仓库清点、优先扫描顺序、跨仓边映射。
- `templates/architecture.html.tmpl`——主文档模板（暖色主题 + 左侧目录 + 全元素样式 + 章节骨架）。
- `templates/submodule-section.html.tmpl`——子模块章节 partial。以模板为起点复制，不要覆盖原文件。

## 执行清单

- [ ] 收集根路径、入口（若有）、范围过滤、深度；`scan_tree.py` 后按规模护栏判断是否需先确认范围。
- [ ] （多仓）清点仓库；（入口）解析根并找出与入口相关的文件。
- [ ] `deps_scan.py` 构建依赖图，标记 `needs_split`。
- [ ] 深挖各模块提炼设计事实（有子代理则并行）。
- [ ] 提炼架构级抽象；按需选视图；复杂模块展开子模块章。
- [ ] 用 `architecture.html.tmpl` 合成单文件 HTML；删除未用视图章并连续编号；校验 Mermaid、目录跳转、配色与样式。
- [ ] 写 `metadata.json`（含 `views_included`、`submodules_expanded`）。
- [ ] 核对每条论断有 `file:line`；无法提取的设计点已标注，全文无臆测。
