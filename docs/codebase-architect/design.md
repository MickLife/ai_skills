
## Markdown 架构图兼容性

`codebase-architect-markdown` 不把某个阅读器的 Mermaid 能力当作前提：

1. 每张图始终保存 `.mmd` 源文件。
2. 本地存在 Mermaid CLI (`mmdc`) 时可生成并嵌入 SVG。
3. 没有渲染器时直接使用 Mermaid 代码块。
4. 图前后的文字说明保证 OpenCode TUI 或纯文本阅读仍能理解设计。
