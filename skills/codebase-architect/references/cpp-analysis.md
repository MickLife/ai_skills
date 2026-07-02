# C / C++ 静态分析指南

产出设计文档时如何阅读与建模 C/C++ 代码库。本文是 `methodology.md` 的 C/C++ 专属配套。C 与 C++ 是不同语言，模块务必注明是哪一种。

## 翻译单元与头文件模型

- **翻译单元（TU）**：一个 `.c`/`.cpp`/`.cc`/`.cxx` 文件经预处理后的产物。
- **头文件**（`.h`/`.hpp`/`.hh`/`.hxx`/`.h++`）是文本包含，非模块（除非使用 C++20 modules——检测 `export module X;`，并对 `module`/`import` 特殊处理）。
- **include 图 ≠ 调用图**。`deps_scan.py` 提取 include 边；调用图由 agent 读代码推断。
- include 解析：
  - `#include "rel/path.h"` → 先相对包含文件目录解析，再查 include 路径。
  - `#include <lib/header.h>` → 仅查构建系统提供的 include 路径。
  - 未解析的 include 列出，不猜测。

## 构建系统识别（决定 include 路径与 target）

- **CMake**：`CMakeLists.txt`。提取 `add_executable`、`add_library`、`target_include_directories`、`target_link_libraries`、`target_sources`、`FetchContent`、`add_subdirectory`——这些定义真正的模块边界与跨仓依赖。
- **Meson**：`meson.build`。提取 `executable()`、`library()`、`subdir()`、`dependency()`。
- **Bazel**：`BUILD`/`BUILD.bazel`。提取 `cc_library`、`cc_binary`、`cc_test`、`deps`、`hdrs`、`copts`，从 `WORKSPACE`/`MODULE.bazel` 提取 external repo。
- **Make**：`Makefile`/`*.mk`。target、`CFLAGS`/`CXXFLAGS`/`INCLUDES`。
- **Conan / vcpkg**：依赖清单；在设计文档依赖表中记版本。
- **无构建文件**：降级为按目录聚类，在"注意事项"中标注。

## `deps_scan.py` 对 C/C++ 提取内容

- `#include "..."` 与 `#include <...>` 边（含行号）。
- 尽力从构建系统推断 include 路径并解析。
- C++20 modules：`export module M;`、`import M;`、`import :sub;` 边。
- 前向声明（`class Foo;`）不是边，但按文件记录，帮助 agent 理解类型面。

调用图与所有权模型由 agent 读代码补充。

## 需识别的入口

- `int main(int argc, char** argv)` / `wmain` / `WinMain`。
- CMake `add_executable(...)` target。
- 导出库入口符号（Windows `__declspec(dllexport)`、Linux `__attribute__((visibility("default")))`）。
- 插件/注册模式：`REGISTER_MODULE`、工厂 map、`__attribute__((constructor))`。
- RTOS/嵌入式：task、ISR handler、`app_main`（ESP-IDF）、线程入口函数。

裸符号入口如 `process_packet`，`find_entry.py` 在 `.c/.cpp/.h/.hpp` 中 grep 匹配 `\<process_packet\>\s*\(` 的定义；有歧义时请用户按目录收窄。

## 设计文档需捕获的内容

- **组件/模块边界**：与构建 target 对齐（`cc_library`/`add_library` 通常即模块）。
- **公共 API**：target 公共 include 路径下的头；导出 vs 内部。
- **所有权与生命周期**：裸 `new`/`delete`、`malloc`/`free`、RAII 包装、`std::unique_ptr`/`shared_ptr`、自定义智能指针、arena/region 分配器——C++ 设计文档的核心。
- **并发**：线程、互斥、原子、无锁结构、条件变量、future/promise、线程池、`std::execution`/senders。标注共享状态与加锁纪律。
- **错误处理**：异常（及哪些边界 `noexcept`/`throw()`）、错误码、`std::expected`/`tl::expected`、Result 类型、errno、断言。
- **内存模型与 ABI**：跨 ABI 边界的 struct 布局、`#pragma pack`、字节序、位域、带版本的结构体。
- **模板与泛型**：重度模板元编程（类型列表、SFINAE/concepts）单列一节解释编译期设计。
- **平台/条件编译**：`#ifdef _WIN32`、编译器宏、平台专属源文件。
- **链接**：静态 vs 动态、导出宏、符号可见性、ODR 考量。

## 常见 C/C++ 坑点

- 头文件 include 环（A 含 B 含 A）——通常用前向声明打破，记录该模式。
- 多态基类缺虚析构。
- 派生对象按值传递被切片。
- 循环中迭代器失效。
- 未定义行为：有符号溢出、越界、use-after-free、非原子共享状态数据竞争。
- 跨 TU 静态初始化顺序陷阱。
- 对 `const` 或平凡可拷贝类型 `std::move`（无效果）。
- 宏副作用（`MAX(i++, j++)`）。
- 某些平台共享库中函数局部 `static` 的线程不安全延迟初始化。
- 改头未升 SO-name 导致 ABI 破坏。

## C vs C++——明确区分

始终注明模块用哪种语言。混合代码库常见 C 核 + C++ 包装，或 C++ 带 `extern "C"` 边界。文档化：

- `extern "C"` 边界及其存在原因（FFI、插件 ABI、C 消费方）。
- 头文件是否需同时作为 C 与 C++ 编译（用 `#ifdef __cplusplus` 守卫）。
- 何处刻意回避 C++ 特性（嵌入式/内核约束）。

## 跨仓（见 `multi-repo.md`）

- 独立仓库中的共享头经 `#include <shared/...>` + CMake/Bazel include 路径消费。
- CMake `FetchContent`/`add_subdirectory(../other_repo)`/Bazel external repo 构成真实跨仓构建边——记录之。
- 跨仓静态/动态库依赖：注明哪个仓库产出产物、哪个消费。
