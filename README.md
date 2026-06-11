# Dev Skills

这个仓库用于集中管理个人创作的 Cursor Agent Skills。每个 Skill 都放在 `skills/<skill-name>/` 下，并尽量保持自包含，方便复制到个人或项目的 `.cursor/skills/` 目录中使用。

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

## Skills

- `dead-code-scanner`: 扫描 Python 工程死代码候选，并要求 AI 逐条复核动态调用误报。
