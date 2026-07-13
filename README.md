# Dev Skills

这个仓库用于集中管理个人创作的 Agent Skills。每个 Skill 都放在 `skills/<skill-name>/` 下并尽量保持自包含，可复制到 Cursor、OpenCode 或其他兼容 Agent Skills 的运行环境。

## Repository Layout

```text
dev_skills/
├── README.md
├── skills/
│   ├── README.md
│   └── <skill-name>/
│       ├── SKILL.md
│       ├── requirements.txt
│       ├── scripts/
│       └── tests/
└── .gitignore
```

## Conventions

- 每个 Skill 使用小写字母、数字和连字符命名。
- 每个 Skill 必须包含 `SKILL.md`，并在 frontmatter 中声明 `name` 和 `description`。
- 可执行工具放在该 Skill 自己的 `scripts/` 目录下。
- 测试放在该 Skill 自己的 `tests/` 目录下。
- 运行产生的报告、缓存、虚拟环境和临时扫描结果不提交。

## 安装位置

- Cursor 项目：`.cursor/skills/<skill-name>/`
- OpenCode 项目：`.opencode/skills/<skill-name>/`
- 跨 Agent 项目：`.agents/skills/<skill-name>/`
- OpenCode 全局：`~/.config/opencode/skills/<skill-name>/`

复制整个 Skill 目录，保留其中的 `references/`、`templates/`、`scripts/` 和 `tests/`。

## Skills

- `dead-code-scanner`: 扫描 Python 工程死代码候选，通过 wave 迭代、子 agent 分片复核和报告校验降低误删风险。
- `codebase-architect`: 为 Python/C/C++ 单仓或多仓代码生成 HTML 架构设计文档。
- `codebase-architect-markdown`: 为 Python/C/C++ 单仓或多仓代码生成 Markdown 架构设计文档；Mermaid 为可编辑图源，本地存在 `mmdc` 时可增强为 SVG。
- `cloud-map-quality-qc`: 检查云图/地图类观察结果与图层质量。

## Markdown 架构图兼容性

`codebase-architect-markdown` 不把某个阅读器的 Mermaid 能力当作前提：

1. 每张图始终保存 `.mmd` 源文件。
2. 本地存在 Mermaid CLI (`mmdc`) 时可生成并嵌入 SVG。
3. 没有渲染器时直接使用 Mermaid 代码块。
4. 图前后的文字说明保证 OpenCode TUI 或纯文本阅读仍能理解设计。
