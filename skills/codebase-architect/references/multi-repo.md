# 多仓库分析指南

`codebase-architect` 多仓模式的方法与跨仓关系映射。当根目录含多个仓库时启用。

## 触发条件

- 根目录无单一 `.git`，且多个兄弟子目录各有 `.git` → 多仓模式。
- 或用户显式声明"这些是多个仓库"。
- monorepo（单一 `.git` 下多个包/workspace）按单根处理，但可借鉴本指南的"逻辑仓"切分。

## 前置约束

借鉴 ekuttan/codewiki 的做法：**所有仓库须位于同一父目录下**。若用户给的根是一个仓库而非父目录，先询问是否切换到其父目录，或逐一分析后手动汇总。

## 阶段 A：仓库清点

对每个兄弟目录，从构建文件 + 入口线索推断角色：

| 线索 | 推断角色 |
|---|---|
| `pyproject.toml` + `fastapi`/`flask` 依赖 | 后端服务 / API |
| `package.json` 但本项目关注 Python/C++ | 前端 / 工具（标注为非主分析目标） |
| `CMakeLists.txt` 含 `add_library(... SHARED)` 且有公共头目录 | 共享库 / 核心库 |
| 仅含 `.h`/`.hpp` + `CMake` `INTERFACE` 库 | 共享头 / 契约仓 |
| `add_executable` 为主 | 可执行服务 / 工具 |
| `setup.py` + `pybind11` | Python 绑定仓（FFI 边界） |
| `WORKSPACE`/`MODULE.bazel` 引用其他仓 | Bazel 聚合仓 |
| 含 `proto`/`idl`/`schema` | 契约 / schema 仓 |

输出 `repo_inventory.json`：`[{name, path, role, lang, build_system, entry_hints}]`。

## 阶段 B：按优先级扫描

顺序很关键——先扫被依赖的，后扫依赖方，使后扫者能引用前者的摘要：

1. **共享头 / 契约仓**（types、proto、schema、接口库）。
2. **核心库**（被多服务依赖的通用库）。
3. **服务 / 可执行**（核心业务）。
4. **前端 / 工具 / 脚本**。

每扫一个仓，把结果写入 scratch，只把**紧凑摘要**（角色、公共 API、导出符号、对外头）带入下一仓，避免上下文爆炸。

## 阶段 C：跨仓边映射

逐类枚举跨仓依赖，每条边都要能指到源行：

- **跨仓 Python import**：仓 A 中 `from shared_lib import x`，`shared_lib` 是仓 B 的顶层包。源行 = import 行。常见于 `pip install -e ../shared_lib` 或同 workspace 多包。
- **跨仓 C/C++ include**：仓 A 中 `#include <shared/types.h>`，头来自仓 B 的公共 include 目录。源行 = include 行；解析依据 = CMake `target_include_directories` / Bazel `hdrs` + `includes`。
- **CMake 跨仓构建边**：`add_subdirectory(../other_repo ...)`、`FetchContent_Declare(...)`、`find_package(<other>)`。源 = `CMakeLists.txt` 行。
- **Bazel 跨仓构建边**：`@other_repo//pkg:target`、`MODULE.bazel` `bazel_dep`。源 = `BUILD`/`MODULE.bazel` 行。
- **Python ↔ C/C++ FFI 跨仓**：仓 A（Python）通过 pybind11/cffi/ctypes 调用仓 B（C++ 库）。标注绑定技术、GIL 释放点、所有权边界。
- **共享运行时契约**：消息 schema、事件名、API 契约定义在契约仓，被多仓消费——单独画一张契约消费图。

## 阶段 D：跨仓产出

- `cross-repo-map.md`（用 `templates/cross-repo-map.md.tmpl`）：
  - 仓库清单表（名称、路径、角色、语言、构建系统）。
  - 跨仓依赖图（Mermaid，仓库为一等节点）。
  - 逐边详表：类型、源仓→目标仓、源行、说明。
  - 契约消费图（哪些仓定义/消费哪些契约）。
  - 构建/部署拓扑（哪些仓产出哪些产物，谁链接谁）。
- 顶层 `ARCHITECTURE.md` 中嵌入仓库级架构图（HTML 用手绘内联 SVG，markdown 用 Mermaid）。
- `AGENTS.md` 中加一段"如何跨仓开发"（改契约时影响谁、如何重建）。

## 注意事项

- 若某仓为非主语言（如前端 JS/TS），仍记录其角色与对外契约，但不做深度设计分析——在"未分析部分"声明。
- 跨仓 include 路径解析失败时，列出"未解析跨仓 include"，请用户补充 include 路径配置。
- 子代理并行时，按仓或按模块派发均可，但**契约仓必须先于消费方完成**，否则跨仓边无法标注源行。
