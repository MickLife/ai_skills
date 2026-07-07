# 输出格式规范（HTML 单文件设计文档）

`codebase-architect` **只产出 HTML 格式**的架构设计文档。本文规定其章节结构与字段规范。模板见 `templates/architecture.html.tmpl` 与 `templates/submodule-section.html.tmpl`；视图选型与抽象提炼见 `architecture-views.md`。

## 产物清单

```
./docs/
├── ARCHITECTURE.html        # 唯一交付物：自包含单文件设计文档（含全部章节 + 子模块章节）
├── module_tree.json         # 分层分解结果（数据）
├── entry-trace.json         # 仅入口模式：可达闭包（数据）
├── metadata.json            # 运行元数据（数据）
└── assets/                  # 可选：仅当选择本地内联 mermaid.min.js 做离线渲染时
```

- 交付物是**单个 HTML 文件**，内联 CSS + 内联 JS，双击即可打开。
- 图表用 Mermaid（`<pre class="mermaid">`）；顶层系统上下文图可选手绘内联 `<svg>`。
- 不产出任何 `.md` 文档。JSON 为结构化数据 sidecar，非文档。

## HTML 文档硬性要求

- **左侧导航栏**：由内联 JS 从 `h1~h4` 自动生成目录，支持点击平滑跳转 + 滚动高亮（scrollspy）。无需手写目录。
- **浅色暖色调**：使用模板中的 CSS 变量配色，勿改成冷色/深色。
- **元素样式齐备**：h1–h4、图片(`figure/img`)、表格、多级列表(嵌套 `ul/ol`)、代码块(`pre`)、加粗(`strong`)、斜体(`em`)、内联代码(`code`)均有样式。
- **自包含**：CSS/JS 内联；Mermaid 默认 CDN，离线时可 vendored 到 `assets/`。禁止依赖其他外部资源。
- **可回溯**：每条论断附 `path:line`（用 `<span class="src-ref">`）。
- **诚实标注缺口**：无法从代码/上下文提炼的设计点，禁止臆测，用下述"无法提取"标注（不得留空当作已知）。

### 无法提取的标注规范

当某设计共识/要点无法从代码或用户上下文得到证据时，用统一标注（样式已在模板中定义）：

- 行内标注：`<span class="badge unknown">无法从代码中提取</span>`，用于表格单元格、句中。
- 成块标注：
  ```html
  <div class="callout-unknown">
    <strong>缺口：</strong>{{缺什么}}。原因：{{代码中为何判定不了}}。建议：{{问谁 / 看哪份外部文档 / 跑什么实验}}。
  </div>
  ```
- 若依据来自用户提供的上下文而非代码，注明"（来源：用户提供的上下文）"。
- 与"未分析部分"区分：确有其事但本次未展开 → 归入附录"未分析部分"；代码里根本判定不了 → 用"无法提取"标注。

## 章节结构（ARCHITECTURE.html）

按此顺序组织；标注"可选"的章节按项目类型裁剪（见 `architecture-views.md` 选型）。

1. **标题 + 元信息卡**：项目名、一句话定位、根路径、模式、语言、时间、LOC/模块数、深度。
2. **引言**：文档目的与读者、系统定位、范围与非目标。
3. **架构级抽象（核心，必写）**：
   - 系统上下文（黑盒 I/O 图）。
   - 系统输入表 / 系统输出表（含 `file:line`）。
   - 核心领域概念 / 数据抽象（类图或 ER 图，仅核心实体）。
   - 关键处理阶段（管道流水图）。
   - 设计目标与质量属性（附证据）。
4. **场景视图（+1）**：3~5 个关键用例/场景表（触发者、目标、涉及模块）。
5. **逻辑视图**：领域模型类图；关键状态机状态图。
6. **进程视图**：关键运行路径时序图；跨角色流程泳道图；并发与通信说明。
7. **开发视图**：模块/包组织组件图；模块清单表；依赖关系（分层是否被破坏、循环依赖）。
8. **物理视图**（可选）：部署拓扑图。库/CLI 可精简或注明"单进程，不适用"。
9. **数据流视图 DFD**（可选，数据加工型项目必写）：上下文图 → 0 层 →（必要时）1 层。
10. **跨仓视图**（仅多仓）：仓库清单、跨仓依赖图、跨仓边详表、契约消费图。见 `multi-repo.md`。
11. **子模块详细设计**（复杂时）：每个被拆解的子模块一节，用 `submodule-section.html.tmpl`。
12. **横切关注**：错误处理、配置、日志/可观测性、资源与生命周期、安全。
13. **关键设计决策与权衡**：决策表（决策/动机/取舍/证据）。
14. **附录**：术语表、注意事项/未分析部分、参考。

### 章节裁剪原则

- 必写：架构级抽象、逻辑视图、开发视图、附录。
- 按需：物理视图（有部署才写）、DFD（数据加工型才写）、子模块详细设计（复杂才写）、跨仓（多仓才写）。
- 宁缺毋滥：没有真实依据的视图不要硬画。

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
