# 输出格式规范

`codebase-architect` 各产出文件的字段级规范。模板见 `templates/`。

## ARCHITECTURE.md（顶层设计文档）

按以下顺序组织：

1. **元信息**：项目名、根路径、分析模式（全量/入口）、深度、生成时间、宿主 agent、token 预算。
2. **执行摘要**：3–5 句话讲清"这是什么系统、解决什么问题、核心设计取舍"。
3. **设计目标与非目标**：明确做什么、不做什么。
4. **系统总览图**：顶层组件视图（HTML 手绘内联 SVG；markdown Mermaid `flowchart`）。
5. **技术栈**：语言、LOC 分布、构建系统、关键依赖及版本。
6. **模块图**：模块间依赖（Mermaid `flowchart` + `subgraph` 分簇）。
7. **模块清单表**：模块名、路径、职责、对应模块文档链接。
8. **关键数据流**：2–3 条主路径的数据流图（Mermaid `flowchart`/`stateDiagram-v2`）。
9. **关键时序**：2–3 条主运行路径时序图（Mermaid `sequenceDiagram`）。
10. **横切关注**：错误处理策略、配置管理、日志/可观测性、并发模型、安全/鉴权。
11. **构建与部署**：如何 build/test/run；产物结构；部署拓扑。
12. **跨仓图**（仅多仓）：见 `cross-repo-map.md` 摘要 + 链接。
13. **关键函数/类型表**：跨模块的"骨干"符号（符号、file:lines、用途）。
14. **坑点与陷阱**：汇总自各模块文档。
15. **扩展点**：新增功能应改哪里。
16. **术语表**：领域与代码术语。
17. **注意事项 / 未分析部分**：假设、未解析项、入口模式下的范围边界。
18. **引用**：所有 file:line 引用应可被读者直接打开。

## modules/<module>.md（模块设计文档）

1. **模块元信息**：名称、路径、语言、所属仓（多仓时）、token 估算、依赖（入/出）。
2. **职责**：一段话。
3. **关键文件表**：路径、角色。
4. **关键函数/类型表**：符号、file:lines、用途、重要参数/返回、可见性（公开/内部）。
5. **内部设计**：控制流、数据结构、并发、错误处理、生命周期/所有权（C++）。
6. **依赖关系**：入依赖表 + 出依赖表，每行 file:line。
7. **设计取舍**：为什么这么做、备选方案。
8. **坑点与陷阱**：附代码引用。
9. **扩展点**：如何在此模块加功能。
10. **图表**：至少一张模块级组件图或时序图（Mermaid）。

## cross-repo-map.md（仅多仓）

1. **仓库清单表**：名称、路径、角色、语言、构建系统、入口。
2. **跨仓依赖图**：仓库为一等节点（Mermaid `flowchart`）。
3. **跨仓边详表**：类型（import/include/build/FFI/契约）、源仓→目标仓、源行、说明。
4. **契约消费图**：契约仓定义的契约被哪些仓消费。
5. **构建/部署拓扑**：各仓产物与链接关系。
6. **跨仓开发指南**：改契约/共享头时的影响面与重建顺序。

## AGENTS.md（一页快速参考）

1. **项目一句话**。
2. **技术栈与构建/运行/测试命令**。
3. **模块地图**：模块名 + 路径 + 一句话职责 + 链接到 `docs/modules/`。
4. **主要坑点**（最多 5 条）。
5. **跨仓提示**（多仓时）：改哪些文件会影响其他仓。
6. **指向 `docs/ARCHITECTURE.md`** 的入口链接。

## metadata.json

```json
{
  "root": "<根路径>",
  "mode": "full | entry",
  "depth": "overview | deep",
  "output_format": "markdown | html",
  "repos": [{"name": "...", "path": "...", "role": "..."}],
  "entry_points": ["src/core/engine.py::run_pipeline", "handle_request"],
  "token_budget": 100000,
  "module_count": 12,
  "timestamp": "ISO-8601",
  "host_agent": "<宿主 agent 名称，按能力描述>"
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
    {"name": "core", "path": "src/core", "tokens": 80000, "children": [...],
     "deps_to": ["shared"], "deps_from": ["api"], "files": [...]}
  ]
}
```

## 通用规范

- 所有路径用相对根的正斜杠形式（跨平台可读）。
- 所有引用为 `path:line` 或 `path:startLine-endLine`。
- Mermaid 写入前必须语法自检。
- HTML 输出：内联 CSS + 手绘 SVG + 轻量 JS，零外部资源。
- 不出现 Cursor/Claude/Codex 等产品名；宿主 agent 字段按能力描述（如 "agent with subagent support"）。
