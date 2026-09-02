# Dev Skills

这个仓库用于集中管理个人创作的 Agent Skills。每个 Skill 都放在 `skills/<skill-name>/` 下并尽量保持自包含，可复制到 Cursor、OpenCode 或其他兼容 Agent Skills 的运行环境。

## Skills

| Skill | Purpose                                                                                  |
| --- |------------------------------------------------------------------------------------------|
| `dead-code-scanner` | 冗余代码清理：扫描 Python 工程中的死代码候选，并用 wave、子 agent 分片和报告校验支持大型仓库复核。                              |
| `codebase-architect` | 文档生成：分析 Python/C/C++ 单仓或多仓代码，生成按需视图组织的 HTML 架构设计文档。                                      |
| `codebase-architect-markdown` | 文档生成：分析 Python/C/C++ 单仓或多仓代码，生成 Markdown 架构设计文档，并以 Mermaid/SVG 混合模式兼容 OpenCode、Gitee 和 GitHub。 |
| `python-vibeperf` | Python 工程系统级性能分析与优化：建立基线、定位瓶颈、专题迭代，附知识库自我进化。                                             |
| `python-vibeperf-evolution` | python-vibeperf 配套技能：验证并沉淀性能优化经验到知识库。                                                    |
| `cloud-map-quality-qc` | 检查云图/地图类观察结果、图层关系和输出质量。                                                                  |

## 安装位置

- Cursor 项目：`.cursor/skills/<skill-name>/`
- OpenCode 项目：`.opencode/skills/<skill-name>/`
- OpenCode 全局：`~/.config/opencode/skills/<skill-name>/`
- 跨 Agent 项目：`.agents/skills/<skill-name>/`

复制整个 Skill 目录，保留其中的 `references/`、`templates/`、`scripts/` 和 `tests/`。Agent 会按需加载 `SKILL.md`；脚本和模板使用 Skill 内的相对路径。

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

每个子目录都是一个独立 Skill，目录名应与 `SKILL.md` frontmatter 中的 `name` 保持一致。

## Conventions

- 每个 Skill 使用小写字母、数字和连字符命名。
- 每个 Skill 必须包含 `SKILL.md`，并在 frontmatter 中声明 `name` 和 `description`。
- 可执行工具放在该 Skill 自己的 `scripts/` 目录下。
- 测试放在该 Skill 自己的 `tests/` 目录下。
- 运行产生的报告、缓存、虚拟环境和临时扫描结果不提交。
