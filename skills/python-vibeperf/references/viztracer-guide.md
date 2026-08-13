# VizTracer 使用指南

## 文档目的

本指南提供 VizTracer 工具的使用方法，帮助建立 Python 代码的性能基线，通过性能追踪生成 JSON 格式的性能数据，用于后续的性能分析和优化。

## 如何执行性能测试

### 基本用法

VizTracer 是一个低开销的 Python 性能分析工具，可以追踪 Python 代码的执行过程并生成 JSON 格式的性能数据。

#### 命令行运行脚本

在命令行运行 Python 脚本，追踪整个脚本的性能：

```bash
viztracer -o <output_json_path> --tracer_entries 20000000 --ignore_c_function --ignore_frozen --min_duration 0.5ms <script_path>
# 或
python -m viztracer -o <output_json_path> --tracer_entries 20000000 --ignore_c_function --ignore_frozen --min_duration 0.5ms <script_path>
```

**默认参数说明：**

- `--tracer_entries 20000000`：最大追踪条目数，默认调整为 2000 万条
- `--ignore_c_function`：忽略 C 函数调用，减少追踪数据量
- `--ignore_frozen`：忽略冻结模块，减少追踪数据量
- `--min_duration 0.5ms`：只记录耗时超过 0.5ms 的函数调用。注意，在 viztracer 中，min_duration 参数的默认单位是 微秒 (us, microseconds)。在命令行中使用时：如果你只写数字而不带单位（例如 --min_duration 500），它会被解析为 500 微秒。你也可以显式指定单位，如 0.5ms（毫秒）、300ns（纳秒）或 5.5us（微秒）。

**需要向用户确认：**

- `<script_path>`：脚本文件的路径
- `<output_json_path>`：输出 JSON 文件的保存位置和命名规则
- 脚本需要哪些参数？参数值是什么？
- 是否需要调整默认参数配置？

### 关键参数配置

在使用 VizTracer 进行性能分析时，需要根据实际情况配置以下关键参数：

#### 1. 输出文件名

使用 `-o` 参数指定输出 JSON 文件的路径和名称：

```bash
viztracer -o <output_json_path> <script_path>
```

**需要向用户确认：**

- `<output_json_path>`：输出 JSON 文件的保存位置和命名规则

#### 2. 追踪深度

默认追踪所有函数调用，可以通过 `--max_stack_depth` 限制追踪深度：

```bash
viztracer --max_stack_depth 10 my_script.py
```

**需要向用户确认：**

- 是否需要限制追踪深度？建议的深度值是多少？

#### 3. 函数参数追踪

如果需要记录函数的输入参数，使用 `--log_func_args`：

```bash
viztracer --log_func_args my_script.py
```

**需要向用户确认：**

- 是否需要记录函数参数？（注意：这会增加性能开销）

### 性能分析流程

1. **运行性能追踪**
   运行性能测试，生成 JSON 文件：

   ```bash
   viztracer -o <output_json_path> --tracer_entries 20000000 --ignore_c_function --ignore_frozen --min_duration 0.5ms <script_path>
   ```

2. **生成性能报告**
   对每个 trace 分别执行解析命令生成子报告：

   ```bash
   python skills/python-vibeperf/scripts/analyze_viztracer.py <output_json_path> -o <output_report_path> -n 100
   ```

   如果存在多个 trace，应在 `<output_report_path>` 中汇总各入口/数据集的热点结论、共同瓶颈与差异点，并标明每段结论对应的 trace 文件。



### 注意事项

- VizTracer 会带来一定的性能开销（通常 < 10%），在分析性能敏感代码时需要注意

- 确保输出 JSON 文件的路径存在，否则会报错

## 参考文档

- **VizTracer GitHub 项目**：https://github.com/gaogaotiantian/viztracer
- **VizTracer 官方文档**：https://viztracer.readthedocs.io/
- **VizTracer 基本用法**：https://github.com/gaogaotiantian/viztracer/blob/master/docs/source/basic_usage.rst
- **VizTracer 过滤功能**：https://github.com/gaogaotiantian/viztracer/blob/master/docs/source/filter.rst
