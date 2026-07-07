# 输出格式规范（HTML 单文件设计文档）

`codebase-architect` **只产出 HTML 格式**的架构设计文档。本文规定其章节结构与字段规范。模板见 `templates/architecture.html.tmpl` 与 `templates/submodule-section.html.tmpl`；视图选型与抽象提炼见 `architecture-views.md`。

## 产物清单

```
./docs/
├── ARCHITECTURE.html        # 唯一交付物：自包含单文件设计文档（含全部章节 + 子模块章节）
├── module_tree.json         # 分层分解结果（数据）
├── entry-trace.json         # 仅入口模式：与入口相关的文件集合（数据）
├── metadata.json            # 运行元数据（数据）
└── assets/                  # 可选：仅当选择本地内联 mermaid.min.js 做离线渲染时
```

- 交付物是**单个 HTML 文件**，内联 CSS + 内联 JS，双击即可打开。
- 图表用 Mermaid（`<pre class="mermaid">`）；顶层系统上下文图可选手绘内联 `<svg>`。
- 不产出任何 `.md` 文档。JSON 为结构化数据 sidecar，非文档。

## HTML 文档硬性要求

- **左侧导航栏**：由内联 JS 从 `h1~h4` 自动生成目录，支持点击平滑跳转 + 随滚动高亮当前章节。无需手写目录。
- **浅色暖色调**：使用模板中的 CSS 变量配色，勿改成冷色/深色。
- **元素样式齐备**：h1–h4、图片(`figure/img`)、表格、多级列表(嵌套 `ul/ol`)、代码块(`pre`)、加粗(`strong`)、斜体(`em`)、内联代码(`code`)均有样式。
- **表格不撑破布局**：每个 `<table>` 必须用 `<div class="table-wrap">…</div>` 包裹；长的类名/文件路径/模块名放进 `<span class="src-ref">`，靠单元格换行留在栏内，宽表则在表内横向滚动——绝不允许把右侧正文栏撑宽。
- **自包含**：CSS/JS 内联；Mermaid 默认 CDN，离线时可 vendored 到 `assets/`。禁止依赖其他外部资源。
- **可回溯**：每条论断附 `path:line`（用 `<span class="src-ref">`）。
- **诚实标注缺口**：无法提炼的设计点用下述标记，禁止留空当已知。

### 无法提取的 HTML 标记

**政策**（何时标、如何区分"未分析部分"、如何写清缺口/来源）是单一事实源，见 `architecture-views.md#一`。此处只给 HTML 写法（样式已在模板中定义）：

- 行内：`<span class="badge unknown">无法从代码中提取</span>`（表格单元格、句中）。
- 成块：
  ```html
  <div class="callout-unknown">
    <strong>缺口：</strong>{{缺什么}}。原因：{{为何判定不了}}。建议：{{确认途径}}。
  </div>
  ```

## 章节结构（ARCHITECTURE.html）

以下是**全集菜单**，不是必填清单。按下面"章节裁剪原则"选择纳入，并对最终纳入的章节**连续编号**（不留空号）。标注见 `architecture-views.md` 选型。

1. **标题 + 元信息卡**：项目名、一句话定位、根路径、模式、语言、时间、LOC/模块数、深度。
2. **引言**：文档目的与读者、系统定位、范围与非目标。
3. **架构级抽象（核心，必写）**：
   - 系统上下文（黑盒 I/O 图）。
   - 系统输入表 / 系统输出表（含 `file:line`）。
   - 核心领域概念 / 数据抽象（类图或 ER 图，仅核心实体）。
   - 关键处理阶段（管道流水图）。
   - 设计目标与质量属性（附证据）。
4. **场景视图（+1）**（按需）：3~5 个关键用例/场景表（触发者、目标、涉及模块）。
5. **逻辑视图**（按需）：领域模型类图；关键状态机状态图。
6. **进程视图**（按需）：关键运行路径时序图；跨角色流程泳道图；并发与通信说明。
7. **开发视图**（常用）：模块/包组织组件图；模块清单表；依赖关系（分层是否被破坏、循环依赖）。
8. **物理视图**（按需）：部署拓扑图。库/CLI 可精简或注明"单进程，不适用"。
9. **数据流视图 DFD**（按需，数据加工型强烈建议）：上下文图 → 0 层 →（必要时）1 层。
10. **跨仓视图**（仅多仓）：仓库清单、跨仓依赖图、跨仓边详表、契约消费图。见 `multi-repo.md`。
11. **子模块详细设计**（复杂时）：每个被拆解的子模块一节，用 `submodule-section.html.tmpl`。
12. **通用机制**（按需）：错误处理、配置、日志与监控、资源与生命周期、安全。
13. **关键设计决策与权衡**（按需）：决策表（决策/动机/取舍/证据）。
14. **附录**（必写）：术语表、注意事项/未分析部分、无法提取的设计点、参考。

### 章节裁剪原则（视图是菜单，不是清单）

- **必写（骨架）**：引言、架构级抽象、附录（含"无法提取的设计点"）。
- **常用**（多模块项目几乎总能从代码得到）：开发视图（模块组织/依赖）。
- **按需**（有真实内容才纳入）：场景、逻辑、进程、物理视图；DFD（数据加工型强烈建议）；通用机制/决策（有实质内容）；子模块（复杂才展开）；跨仓（多仓）。
- **宁缺毋滥**：没有真实内容的视图直接删章，禁止占位符/套话硬填（硬填＝变相臆测）。
- **动态编号**：按最终纳入的章节连续编号，不留空号。
- **图文并茂**：每个视图先文字讲设计意图，再图，图后关键点解读；无解读的图视为未完成。

## 子模块章节规范（submodule-section）

当某模块超 token 预算或内部再分层时展开。每节含：路径/语言/规模/拆解原因元卡、职责、子模块 I/O 契约表、内部结构图（组件/类图）、关键运行路径时序图、关键函数/类型表、依赖关系、设计要点与坑点。视图按该子模块真实需要选用，不堆图。

## metadata.json

```json
{
  "root": "<根路径>",
  "mode": "full | entry",
  "depth": "overview | deep",
  "output_format": "html",
  "repos": [{"name": "...", "path": "...", "role": "..."}],
  "entry_points": ["src/core/engine.py::run_pipeline", "handle_request"],
  "token_budget": 100000,
  "module_count": 12,
  "views_included": ["logical", "process", "development", "dfd"],
  "submodules_expanded": ["core.scheduler", "io.codec"],
  "timestamp": "ISO-8601",
  "host_agent": "<按能力描述>"
}
```

## entry-trace.json（仅入口模式）

```json
{
  "roots": [{"file": "...", "symbol": "...", "line": 42}],
  "forward_closure": ["file_a.py", "shared/types.h"],
  "reverse_closure": ["cli/main.py"],
  "pruned_top_level": ["tests/", "scripts/", "frontend/"],
  "rationale": "仅追踪 run_pipeline 的被调用者与直接调用者"
}
```

## module_tree.json

```json
{
  "name": "root",
  "path": ".",
  "tokens": 250000,
  "children": [
    {"name": "core", "path": "src/core", "tokens": 80000, "children": [],
     "deps_to": ["shared"], "deps_from": ["api"], "files": [], "needs_split": false}
  ]
}
```

## 通用规范

- 所有路径用相对根的正斜杠形式。
- 所有引用为 `path:line` 或 `path:startLine-endLine`，放进 `<span class="src-ref">`。
- 每个 Mermaid 块写入前按 `architecture-views.md#七` 自检语法。
- 配色统一走模板 CSS 变量与 Mermaid `themeVariables`（暖色）。
- 不出现 Cursor/Claude/Codex 等产品名；`host_agent` 按能力描述。
