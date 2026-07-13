# C/C++ 分析要点

## 构建目标优先

模块边界优先依据构建系统，而不是只看目录：

- CMake：`add_library`、`add_executable`、`target_link_libraries`、`target_include_directories`。
- Meson：`library()`、`executable()`、`dependency()`。
- Bazel：`cc_library`、`cc_binary`、`deps`。
- Make/Conan/vcpkg：目标、编译参数和依赖清单。

有 `compile_commands.json` 时将其作为编译参数和头文件搜索路径的首选证据。没有时必须说明 include/call 关系是尽力分析。

## 文件与依赖

- `.c/.cpp/.cc/.cxx` 是编译入口；头文件被文本包含。
- include 图不等于调用图。
- 引号头先相对当前文件解析；尖括号头依赖构建系统 include 路径。
- C++20 module 用 `module/import` 单独记录。

## 入口

- `main`、`wmain`、`WinMain`。
- 构建系统的可执行目标。
- 导出库符号、插件注册、工厂表。
- 嵌入式 task、ISR、`app_main`。

## 设计事实

- 公共头文件和导出符号代表公共接口。
- `unique_ptr/shared_ptr`、RAII 包装、`malloc/free`、arena 说明所有权。
- 线程、互斥、原子、条件变量、线程池说明并发方式。
- 异常、错误码、`expected`/Result、断言说明错误策略。
- `extern "C"`、导出宏、结构体布局说明跨语言或二进制兼容边界。

## 风险

- 宏、条件编译、虚函数、函数指针、模板实例化会让静态调用关系不完整。
- 重点关注 include 环、资源释放、数据竞争、静态初始化顺序和二进制兼容变化。
- 不把“可能调用”写成“确定调用”；无法确认时明确标记。
