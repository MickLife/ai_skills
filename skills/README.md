# Skills Index

每个子目录都是一个独立 Skill，目录名应与 `SKILL.md` frontmatter 中的 `name` 保持一致。

## Available Skills

| Skill | Purpose |
| --- | --- |
| `dead-code-scanner` | 扫描 Python 工程中的死代码候选，并用 wave、子 agent 分片和报告校验支持大型仓库复核。 |
| `codebase-architect` | 分析 Python/C/C++ 单仓或多仓代码，生成按需视图组织的 HTML 架构设计文档。 |
| `codebase-architect-markdown` | 分析 Python/C/C++ 单仓或多仓代码，生成 Markdown 架构设计文档，并以 Mermaid/SVG 混合模式兼容 OpenCode、Gitee 和 GitHub。 |
| `cloud-map-quality-qc` | 检查云图/地图类观察结果、图层关系和输出质量。 |

## OpenCode

把整个 Skill 目录复制到项目的 `.opencode/skills/` 或 `.agents/skills/`。OpenCode 会按需加载 `SKILL.md`；脚本和模板使用 Skill 内的相对路径，不依赖 Cursor 专属工具。
