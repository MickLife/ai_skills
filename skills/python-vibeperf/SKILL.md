---
name: python-vibeperf
description: Use when analyzing Python script performance bottlenecks or optimizing code performance
---

# Python 性能优化

## 概述

本技能提供系统化的 Python 性能分析与优化流程，通过建立性能基线、分析热点函数、设计优化方案、实施优化并验证效果，帮助提升 Python 代码的执行效率。

核心流程包括3个步骤：建立性能基线、性能瓶颈分析（含代码理解）、专题迭代与总结。

## 触发条件

当用户提出以下类型的需求时，应触发本技能：

- "帮我分析一下这个 Python 脚本的性能瓶颈"
- "优化 xxx.py 这个 Python 脚本的性能"
- "用 viztracer 跑一下这个项目的性能分析，看看哪里慢"
- "这个 Python 项目在高并发场景下响应太慢，帮我做系统级的性能调优"

## 依赖

本技能依赖 `superpowers` skill。

如未安装，请先安装：
- 仓库地址：https://github.com/cline/superpowers

## 核心流程

本技能遵循以下3步流程：

1. **建立性能基线** - 使用 viztracer 等工具建立性能基线，收集性能数据 [详细指南](references/01-performance-profiling.md)
2. **性能瓶颈分析** - 顺着入口脚本阅读代码理解项目背景，分析性能数据，定位热点函数和性能瓶颈 [详细指南](references/02-bottleneck-analysis.md)
3. **专题迭代与总结** - 针对用户指定的单一瓶颈专题，将优化需求拆解为具体的优化方向和任务，并进行迭代优化。当前专题完成后循环处理下一个专题 [详细指南](references/03-topic-optimization.md)

各阶段的详细执行指南请参考 `references/` 目录下的对应文档。
在瓶颈分析和方案设计阶段，必须先读取 `skills/python-vibeperf/knowledge/INDEX.md`，再按索引查阅相关原则、库级经验或领域模式；默认只读取 `cases/README.md` 摘要索引，不读取完整案例正文。
viztracer工具的使用严格遵循文档：[viztracer-guide.md](references/viztracer-guide.md)，工具的运行参数需向用户确认后再执行


## 产物结构

```
docs/perf/
  CODEBASE_CONTEXT.md  # 全局代码上下文，跨轮次共享，及时更新
  rounds/
    YYYYMMDD-HHMMSS/
      PROGRESS.md  # 本轮次的进度管理文件
      01-baseline/
        BASELINE_REQUEST.md
        BASELINE_RUN.md
        traces/
          trace-<entry_name>-<dataset_name>.json
      02-bottleneck-analysis/
        BASELINE_REPORT-<entry_name>-<dataset_name>.md
        BOTTLENECK_INDEX.md
        BOTTLENECK-A-<name>.md
        BOTTLENECK-B-<name>.md
      03-topic-optimization/
        topic-A-<name>/
          01-REQUIREMENTS.md
          02-SOLUTION_DESIGN-<sub_req_name1>.md
          03-OPTIMIZATION_EXECUTION-<sub_req_name1>.md
          04-SOLUTION_DESIGN-<sub_req_name2>.md
          05-OPTIMIZATION_EXECUTION-<sub_req_name2>.md
          06-OPTIMIZATION_REPORT.md
        topic-B-<name>/
          ...

skills/python-vibeperf/knowledge/  # 性能优化知识库（用于自我进化）
  INDEX.md
  _TEMPLATE.md
  principles/  # 跨库、跨领域的通用性能原则
    core-strategies.md
    data-structures.md
    concurrency-and-io.md
    memory-management.md
    vectorization.md
  libraries/  # 依赖特定库 API 或版本行为的优化模式
    numpy.md
    scipy.md
    shapely.md
    pyproj.md
    loguru.md
  domains/  # 跨多个库的问题域模式
    spatial-computing.md
    json-serialization.md
  cases/  # 真实案例证据，默认只读 README 摘要索引
    README.md
```

## 自我进化 (Self-Evolution)

本技能配套了一个独立的进化技能 `python-vibeperf-evolution`。
推荐用户在完成优化后，主动调用 `/python-vibeperf-evolution` 技能来沉淀优化经验。该独立技能必须先完成通用性验证和分类决策，再将可迁移模式写入 `principles/`、`libraries/` 或 `domains/`；尚未抽象为通用模式的真实项目结果只能写入 `cases/` 作为证据，不能直接追加为最佳实践。

## 约束

- 严格实行上述3个阶段的流程，在每个阶段产物撰写完成后，提交用户拍板确认，用户确认之前，不要进入下一阶段
- 严禁在方案和目标明确概率<95%的情况下编写任何代码、实验数据、测试用例
- 严禁在整个优化重构过程中改变算法，要严格保证算法和输出数据一致性，先建立算法一致性相关的测试用例再进行代码修改
- 顺序执行各个子优化任务，避免并行任务执行引入可能的bug
- 代码优化全程与产物内容使用中文；文件名保留英文
- 每轮优化必须更新 `PROGRESS.md` 记录全局任务进度，允许用户指定从某一阶段开始工作，但应检查前置阶段的产物是否存在

## Superpowers 子技能使用

在性能优化的各个阶段，应合理使用 superpowers 的子技能：

**重要执行规范**：AI 在执行到需要使用子技能的步骤时，**严禁自行脑补**。必须使用 `Read` 工具，从系统提供的 `<available_skills>` 列表中找到对应技能的绝对路径并读取其 `SKILL.md` 文件，然后严格按照该文件内的流程执行。

- **项目背景收集、性能瓶颈识别、需求拆解、实验选型探讨** - 读取并执行 `brainstorming`
- **计划撰写与方案收敛** - 读取并执行 `writing-plans`
- **计划执行** - 读取并执行 `executing-plans`
- **补充测试用例** - 读取并执行 `test-driven-development`
- **代码review** - 读取并执行 `requesting-code-review`
- **验证优化效果 (Fallback)** - 仅在测试失败或性能未达标时，读取并执行 `systematic-debugging` 寻找根因
- **提交代码** - 读取并执行 `verification-before-completion` 确保绿灯后提交
