# 方法论（methodology）

`codebase-architect` 的详细方法论。SKILL.md 故意精简，本文件仅在 agent 需要完整流程时加载。

## 指导原则

1. **事实先行，解读在后。** 脚本采集结构化事实（文件树、token 估算、依赖边、入口解析），agent 读真实代码写设计叙述。禁止叙述未读过的内容。
2. **保留架构上下文。** 切分大库时，把父模块上下文带给子模块分析，使模块文档能正确引用相邻模块（借鉴 CodeWiki 分层分解）。
3. **预算驱动递归。** 每个分析单元有 token 预算；超预算则递归拆分，而非截断。
4. **Agent 无关。** 交付物不出现产品名，仅按能力描述工具。

## 阶段一：侦察

目标：用低成本得到一幅准确的"存在性地图"。

1. 运行 `scripts/scan_tree.py --root <root> [--include ...] [--exclude ...]`。
   - 输出：JSON 文件清单，含 `path`、`lang`、`lines`、`tokens`（≈ 行数×4 启发式）与树汇总。
   - 尊重 `.gitignore` 与内置默认排除（`.git`、`node_modules`、`__pycache__`、`build/`、`dist/`、`.venv` 等）。
2. 识别构建系统与项目文件：
   - Python：`pyproject.toml`、`setup.py`、`setup.cfg`、`requirements*.txt`、`Pipfile`、`poetry.lock`、`conda*.yml`。
   - C/C++：`CMakeLists.txt`、`meson.build`、`BUILD.bazel`/`WORKSPACE`、`Makefile`、`conanfile.*`、`vcpkg.json`、`.vcxproj`。
3. 识别仓库边界：
   - `<root>/.git` 存在且无嵌套 `.git` → 单仓模式。
   - 多个兄弟目录各有 `.git` → 多仓模式（见 `multi-repo.md`）。
   - 混合/monorepo：把顶层包/工作区视为逻辑仓，但仍是单根。
4. 记录栈摘要：语言 + LOC 分布、构建系统、入口线索（`main.py`、`app.py`、`__main__.py`、`main.c/cpp`、CMake `add_executable`）。

### Token 预算

默认每模块预算：**100k tokens** 输入，可配置。聚类目标是让每个模块文件 token 总和低于此值。叶子模块（无更细拆分意义）使用更小预算（默认 16k），分块汇总。

## 阶段二：分解

目标：把代码库切成保持上下文的内聚模块。

1. 运行 `scripts/deps_scan.py --root <root>` 得到静态依赖图：
   - Python 边：`import x`、`from x import y`，相对 import 按包根解析。
   - C/C++ 边：`#include "..."` 与 `#include <...>`，按从构建文件推断的 include 路径解析。
2. **分层分解**（借鉴 CodeWiki）：
   - 从目录聚类起步。
   - 合并体量小且依赖内聚的兄弟目录（合计仍在预算内）。
   - 按子依赖聚类拆分超预算目录（动态规划思路：最大化簇内边、最小化跨簇边，且不超预算）。
   - 递归深度上限默认 3，避免过度碎片化。
3. 输出 `module_tree.json`：嵌套 `{name, path, files, tokens, children, deps_to, deps_from}`。

### 入口模式

用户给入口时，分解改为**剪枝**而非替换：

1. 用 `scripts/find_entry.py` 解析每个入口 → `(file, symbol, line)` 列表。
2. 在依赖图上构建**可达闭包**：
   - 前向：从根沿 import/include 追踪可达文件（被调用者 / 被包含头 / 实际使用的被导入模块）。
   - 反向：import/include 了根文件的文件（调用者）。
   - 符号级入口（`file::func`）额外 grep 该符号调用点以精炼前向闭包。
3. 把模块树限制在闭包内，显式标记根，输出 `entry-trace.json` 含闭包与剪枝理由。
4. 必须附"未分析部分"小节，列出闭包外的主要顶层模块，明确范围。

## 阶段三：深挖

目标：基于真实代码的逐模块设计文档。

1. 对模块树中每个模块（叶子优先）：
   - 读取其文件（及提供上下文所需的相关头/导入）。
   - 用 `templates/module-doc.md.tmpl` 产出模块文档：
     - 职责（一段话）。
     - 关键文件表（路径、角色）。
     - 关键函数/类型表（符号、file:lines、用途、重要参数/返回）。
     - 内部设计：控制流、数据结构、并发、错误处理。
     - 依赖（入/出），附 file:line 引用。
     - 坑点与陷阱（竞态、C++ 所有权/生命周期、Python GIL/async、缓存怪癖、历史修补）。
     - 扩展点。
     - Mermaid：一张模块级组件或时序图。
2. **子代理并行**（借鉴 cartographer-cursor）：
   - 宿主若有 Task/子代理工具，把独立叶子模块并行派发，各自带 token 预算与父上下文摘要副本。
   - 若无，顺序处理，方法论依然成立，仅更慢。
   - 禁止两个子代理写同一文件；模块文档相互独立，合成阶段单线程。
3. **动态委派**（借鉴 CodeWiki）：子代理若发现模块仍过大、无法在响应预算内汇总，则发出 `needs-split` 标记并提议子簇，由编排器重新派发子模块。

## 阶段四：合成与交付

目标：一份连贯的设计文档。

1. 自底向上上卷：
   - 父模块汇总子模块职责与子间关系。
   - 顶层 `ARCHITECTURE.md`（用 `templates/ARCHITECTURE.md.tmpl`）覆盖：系统总览、设计目标、模块图、关键数据流、横切关注、部署/构建、术语表。
2. 图表（多模态合成，借鉴 CodeWiki）：
   - **架构图**：顶层组件视图。HTML 输出则手绘内联 SVG（借鉴 codebase-summary）；markdown 用 Mermaid `flowchart`。
   - **数据流**：Mermaid `flowchart` 或 `stateDiagram-v2`。
   - **时序图**：为 2–3 条最重要运行路径（入口模式下为主入口路径）画 Mermaid `sequenceDiagram`。
   - **依赖图**：模块间边的 Mermaid `flowchart`；图过大时按簇分 `subgraph`。
3. **写入前校验每个 Mermaid 块**。常见修复：含特殊字符的标签加引号、勿用 `end` 作节点 id、转义 `()`。
4. 生成 `AGENTS.md`：一页快速参考（栈、构建/运行/测试命令、模块图链接、主要坑点）。
5. 写 `metadata.json`：`{root, repos[], entry_points[], mode, depth, output_format, timestamp, host_agent, token_budget, module_count}`。
6. （HTML 模式）内联所有 CSS、手绘 SVG、轻量 JS（粘性目录、可折叠节）。禁止 CDN、网络字体、远程图片。

## 质量门

宣布完成前：
- 关键函数表每行都有 agent 实际读过的 `file:lines` 引用。
- 每条坑点都有代码引用或代码注释佐证。
- 所有 Mermaid 块通过语法自检。
- `metadata.json` 存在且与产出文件一致。
- （入口模式）`entry-trace.json` 与"未分析部分"小节齐备。
- （多仓）`cross-repo-map.md` 存在，每条跨仓边都标注源行（import/include/构建文件行）。

## 失败模式与降级

- **未识别构建系统**（无 CMake/Bazel 等）：降级为按目录解析 include；在文档"注意事项"中说明假设。
- **头文件找不到**：include 图标为未解析 `#include <x>`；列入"未解析 include"，不得猜测。
- **混合语言模块**：各语言子树分别用对应参考（`python-analysis.md` / `cpp-analysis.md`）；显式文档化 FFI 边界（pybind11、ctypes、cffi、SWIG、手写扩展）。
- **无子代理工具**：顺序运行，仍按模块预算分块读取。
- **单趟装不下**：默认转入口模式或 `overview` 深度；请用户收窄范围。
