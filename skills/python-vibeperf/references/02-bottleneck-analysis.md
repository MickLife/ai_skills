# 瓶颈分析

## 目标

本阶段的目标是深入分析性能基线数据，准确定位性能瓶颈和热点函数，理解性能问题的根本原因。

## 过程与规则

**状态管理：**
- 进入本阶段时，更新 `docs/perf/rounds/<timestamp>/PROGRESS.md`，将状态标记为“进行中”。
- 完成本阶段时，更新 `PROGRESS.md`，将状态标记为“已完成”，并简要记录发现的核心性能瓶颈。

1.**项目背景与代码理解**
   - 顺着入口脚本的执行流来阅读代码，不要阅读无关的业务代码，理清核心调用链路。
   - 只读取python语言代码，其他语言的代码性能不做优化
   - 完成静态代码阅读后，应更新 `docs/perf/CODEBASE_CONTEXT.md`，写清楚项目文件结构及每个文件的主要功能。
   - 后续浏览代码文件时，优先查询 `docs/perf/CODEBASE_CONTEXT.md`，减少重复读取代码造成的 token 消耗


2.  **生成与分析性能追踪数据**
   - 使用 `analyze_viztracer.py` 脚本分析 01 阶段生成的追踪数据（JSON 文件）
   - 为每个 trace 文件生成对应TOP100耗时函数累计耗时统计（如 `BASELINE_REPORT-<entry_name>-<dataset_name>.md`）
   - 参考调用命令：

```python
python skills/python-vibeperf/scripts/analyze_viztracer.py \
<output_json_path> \
-o <output_report_path> \
-n 100
```

3. **性能瓶颈分析**
   - **读取并执行 `brainstorming` 技能**：使用 Read 工具读取系统可用技能列表中的 `brainstorming` 技能文档，并严格遵循其指令，与用户一起深挖技术根因。
   - 分析函数调用关系和执行流程，明确各个大模块的耗时情况
   - 分析TOP5模块的静态代码，找出算法复杂度较高的函数
   - 分析TOP5模块的静态代码，找出数据结构方面不合理的地方
   - 分析累计耗时TOP函数，找出性能瓶颈相关函数
   - 输出性能瓶颈专题索引页 `BOTTLENECK_INDEX.md` 和多个专题报告 `BOTTLENECK-{A,B,C...}-{name}.md`，为后续的需求拆解提供数据支撑
   
   **索引页 `BOTTLENECK_INDEX.md` 包含**：
   - 性能画像概览：代码都有哪些模块，函数调用链，性能最差的TOP外层模块列表
   - 瓶颈专题索引：列出所有识别出的瓶颈专题及其对应的报告链接
   - 优先级建议：根据耗时占比和优化潜力给出整体的优先级排序

   **专题报告 `BOTTLENECK-{A,B,C...}-{name}.md` 包含**：
   - 针对每个瓶颈单独出报告。对于每一处可能优化的代码位置，分不同的章节展开详细的代码分析。
   - 每个代码位置章节，必须回答以下三个问题：
     1. 当前代码实现是否符合高性能python编程要求，为什么存在性能问题？
     2. 有哪些可能的性能提升手段？
     3. 对于每个可能的修改方案，评估实现难度、性能提升效果、重构风险。
   - **重要约束**：在回答上述问题之前，**必须先使用 Read 工具读取 `skills/python-vibeperf/knowledge/INDEX.md`**，并顺藤摸瓜查阅相关分类的经验文档。默认只读取 `cases/README.md` 的案例摘要索引；只有当前问题与某个案例高度相似或需要核验证据时，才读取单个案例正文。确保分析报告中的建议有知识库的最佳实践作为支撑。
   - 潜在风险和注意事项


**约束条件：**

- 必须基于真实的性能数据进行分析
- 不进行代码修改，只进行分析和评估
- 确保分析结论有数据支撑

## 输出产物

- `docs/perf/CODEBASE_CONTEXT.md`
- `docs/perf/rounds/<timestamp>/02-bottleneck-analysis/BASELINE_REPORT-<entry_name>-<dataset_name>.md`：由 `analyze_viztracer.py` TOPN耗时函数累计耗时统计
- `docs/perf/rounds/<timestamp>/02-bottleneck-analysis/BOTTLENECK_INDEX.md`：瓶颈专题索引页
- `docs/perf/rounds/<timestamp>/02-bottleneck-analysis/BOTTLENECK-{A,B,C...}-{name}.md`：各个性能瓶颈专题报告
