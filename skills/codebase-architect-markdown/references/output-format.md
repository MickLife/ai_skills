# Markdown 输出规范

## 产物

```text
docs/
├── ARCHITECTURE.md
├── diagrams/
│   ├── *.mmd
│   ├── *.svg                 # 可选
│   └── render-manifest.json
├── modules/*.md              # 仅复杂模块
├── module_tree.json
├── entry-trace.json          # 仅入口模式
└── metadata.json
```

`ARCHITECTURE.md` 是入口。复杂模块才拆到 `modules/`；主文档保留摘要和相对链接。

## 章节菜单

最终文档只保留有真实内容的章节并连续编号。

### 必写

- 引言：目的、读者、范围、未分析部分。
- 架构级抽象：系统边界、输入输出、核心概念、处理阶段。
- 附录：术语、限制、无法从代码中提取的设计点、证据约定。

### 常用或按需

- 场景：有清晰使用路径时。
- 模块设计：多模块项目常用。
- 运行流程：存在非平凡调用、任务或并发时。
- 数据流：数据加工型项目。
- 状态与核心类型：确有状态机或重要类型关系时。
- 部署：多进程、容器、主机或动态库部署关系。
- 多仓关系：多仓模式。
- 通用机制：错误、配置、日志监控、资源、安全确有设计内容时。
- 子模块：超预算或内部结构复杂时。

## Markdown 排版

- 使用标准标题、列表、代码围栏、链接和图片，避免依赖 HTML。
- 每段只表达一个主题；长文先给结论，再给证据。
- 图片使用相对路径，并写有意义的替代文字。
- 不使用颜色作为唯一信息载体。
- 不使用 `<details>`、`<picture>` 或需要特定渲染器的提示框。

### 表格规则

表格只用于内容短、列数少的数据，例如“模块 / 职责 / 语言”。

以下内容不要放入表格：

- 很长的类名、函数签名。
- 深层文件路径。
- 多行设计说明。
- 多条证据。

改用分段列表：

```markdown
### TransformAndSerializePipelineHandler

- **位置：** `src/core/engine/pipeline/transform_handler.py:128-256`
- **职责：** 执行转换和序列化。
- **输入：** `ImageBatch`
- **输出：** `ArtifactSet`
- **证据：** `run_and_flush_all_stages()`
```

## 图形嵌入

以 `render-manifest.json` 为准：

- `mode: svg`：嵌入已存在的 SVG，并链接 `.mmd`。
- `mode: mermaid`：直接嵌入 Mermaid 围栏，不引用不存在的 SVG。

两种模式都必须提供“设计意图”和“关键解读”。具体写法见 `diagram-patterns.md`。

## 证据与未知

- 代码证据格式：`repo/path/to/file.py:12-30`。
- 用户上下文注明“来源：用户提供”。
- 代码无法证明的内容写“无法从代码中提取”，并说明缺口、原因和建议确认途径。
- 不把命名习惯、常见架构模式当成本项目的事实。

## JSON sidecar

`metadata.json` 至少包含：

```json
{
  "mode": "full",
  "depth": "deep",
  "output_format": "markdown",
  "diagram_mode": "mermaid",
  "repositories": [],
  "entry_points": [],
  "views_included": [],
  "modules_expanded": [],
  "timestamp": "ISO-8601"
}
```

`module_tree.json` 记录模块文件、token、子模块、入/出依赖。`entry-trace.json` 记录入口和相关文件范围。

## 交付前检查

- 删除所有 `{{placeholder}}` 和空章节。
- 标题无重复且编号连续。
- 图像、模块文档和源码链接均存在。
- Mermaid 围栏闭合；图有文字解释。
- 长标识符未塞入 Markdown 表格。
- 运行 `scripts/validate_markdown.py docs/ARCHITECTURE.md`。
