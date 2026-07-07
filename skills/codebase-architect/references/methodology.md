# 方法论（methodology）

`codebase-architect` 的详细方法论。SKILL.md 故意精简，本文件仅在 agent 需要完整流程时加载。

## 指导原则

1. **事实先行，解读在后。** 脚本采集结构化事实（文件树、token 估算、依赖边、入口解析），agent 读真实代码写设计叙述。禁止叙述未读过的内容。
2. **诚实优先，缺口留白。** 提炼不出来的设计共识/要点，禁止推测或凭经验补全，显式标注"无法从代码中提取"（见 `architecture-views.md#一` 的诚实标注一节）。看似合理的猜测比留白更有害。
3. **保留架构上下文。** 切分大库时，把父模块上下文带给子模块分析，使模块文档能正确引用相邻模块（借鉴 CodeWiki 分层分解）。
4. **预算驱动递归。** 每个分析单元有 token 预算；超预算则递归拆分，而非截断。
5. **Agent 无关。** 交付物不出现产品名，仅按能力描述工具。

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
2. 顺依赖关系找出**与入口相关的文件集合**：
   - 前向：从根沿 import/include 追踪它用到的文件（被调用者 / 被包含头 / 实际使用的被导入模块）。
   - 反向：import/include 了根文件的文件（调用它的）。
   - 符号级入口（`file::func`）额外 grep 该符号调用点以精炼前向范围。
3. 把模块树限制在这个相关文件集合内，显式标记根，输出 `entry-trace.json` 含相关范围与裁剪理由。
4. 必须附"未分析部分"小节，列出相关范围外的主要顶层模块，明确边界。

## 阶段三：深挖

目标：基于真实代码提炼每个模块的设计事实，作为阶段四合成的素材。

1. 对模块树中每个模块（叶子优先），读取其文件（及提供上下文所需的相关头/导入），记录：
   - 职责（一段话）。
   - 模块级 I/O 契约：输入（来源/形态）、输出（去向/形态），附 `file:line`。
   - 关键函数/类型（符号、file:lines、用途、重要参数/返回、可见性）。
   - 内部设计：控制流/处理阶段、核心数据结构、并发、错误处理、生命周期/所有权。
   - 依赖（入/出），附 `file:line`。
   - 坑点与陷阱（竞态、C++ 所有权/生命周期、Python GIL/async、缓存怪癖、历史修补）。
   - 设计取舍与扩展点。
   > 这些素材最终不是单独成文，而是上卷进单一 HTML 设计文档的对应视图章节；复杂模块另在"子模块详细设计"章展开（见 `templates/submodule-section.html.tmpl`）。视图选型见 `architecture-views.md`。
2. **子代理并行**（借鉴 cartographer-cursor）：
   - 宿主若有 Task/子代理工具，把独立叶子模块并行派发，各自带 token 预算与父上下文摘要副本。
   - 若无，顺序处理，方法论依然成立，仅更慢。
   - 禁止两个子代理写同一文件；模块文档相互独立，合成阶段单线程。
3. **动态拆分派发**（借鉴 CodeWiki）：子代理若发现模块仍过大、无法在响应预算内汇总，则发出 `needs-split` 标记并提议子簇，由编排器重新派发子模块。

## 阶段四：合成与交付（架构级抽象 + 视图化）

目标：把阶段三的模块事实**提炼成整架构级设计**，产出单一自包含 HTML 文档。灵魂是先抽象、再选视图、最后画图——不做浮于代码表面的罗列。

1. **先提炼架构级抽象**（方法见 `architecture-views.md#一`）：系统边界与黑盒 I/O 契约、核心领域概念、关键处理阶段、质量属性与约束、关键设计决策，均附代码证据。
2. **按需选视图组织章节**：为每种设计意图选合理视图，视图/图/Mermaid 选型见 `architecture-views.md#二~七`；章节菜单与裁剪原则见 `output-format.md`。没内容的视图删章，不硬凑。
3. **复杂模块拆解**：阶段二/三中被标 `needs_split` 的模块，在"子模块详细设计"章逐个展开（`submodule-section.html.tmpl`），复用同一套视图方法。
4. **产出单一 HTML**：用 `templates/architecture.html.tmpl`；HTML 硬性要求（自包含、暖色、自动目录、样式齐备、Mermaid 自检、`path:line` 引用）与 `metadata.json` 结构均见 `output-format.md`。

## 质量门

宣布完成前：
- 架构级抽象章齐备：系统 I/O 契约、核心概念、处理阶段、质量属性，均有代码证据。
- 关键函数表每行都有 agent 实际读过的 `file:lines` 引用。
- 每条坑点都有代码引用或代码注释佐证。
- 每个视图都对应真实设计意图（无为凑格式硬画的图）；所有 Mermaid 块通过语法自检。
- 无法从代码/上下文提炼的设计点已显式标注"无法从代码中提取"，全文无臆测、无凭空补全的内容。
- HTML 左侧目录能覆盖全部 h1–h4 并可跳转；配色为浅色暖色调；样式元素齐备。
- `metadata.json` 存在且与产出文件一致。
- （入口模式）`entry-trace.json` 与"未分析部分"小节齐备。
- （多仓）跨仓章节存在，每条跨仓边都标注源行（import/include/构建文件行）。

## 失败模式与降级

- **未识别构建系统**（无 CMake/Bazel 等）：降级为按目录解析 include；在文档"注意事项"中说明假设。
- **头文件找不到**：include 图标为未解析 `#include <x>`；列入"未解析 include"，不得猜测。
- **混合语言模块**：各语言子树分别用对应参考（`python-analysis.md` / `cpp-analysis.md`）；显式文档化跨语言调用边界（pybind11、ctypes、cffi、SWIG、手写扩展）。
- **无子代理工具**：顺序运行，仍按模块预算分块读取。
- **单趟装不下**：默认转入口模式或 `overview` 深度；请用户收窄范围。
