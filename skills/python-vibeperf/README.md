# python-vibeperf

Python 工程系统级性能分析与优化技能：建立性能基线（viztracer）→ 定位热点瓶颈 → 专题迭代优化，并以 Markdown 结构化记录进度，配套自我进化知识库。

本目录为 skill 运行时内容，可直接复制到 Agent 环境的 `skills/python-vibeperf/`。示例、测试与宣传资产放在仓库的其他位置，见下文。

## 目录结构

```
skills/python-vibeperf/
├── SKILL.md                    # 技能主文档（3 阶段流程、约束、产物说明）
├── requirements.txt            # viztracer + numpy
├── references/                 # 各阶段执行参考（profiling / 瓶颈分析 / 专题优化 / viztracer 指南）
├── knowledge/                  # 性能优化知识库（principles / libraries / domains / cases）
└── scripts/analyze_viztracer.py  # 解析 viztracer JSON 生成 TOP100 报告
```

## 配套内容（仓库级位置）

```
docs/python-vibeperf/
├── examples/                   # 示例程序 + 一次完整优化案例的产物
│   ├── lidar_rasterization.py         # 慢版本（优化前）
│   ├── lidar_rasterization_optimized.py # NumPy 向量化版本（优化后）
│   ├── experiments/            # 性能对比实验脚本
│   └── docs/perf/              # 案例：LiDAR 栅格化完整优化轮次（baseline/瓶颈/设计/报告）
├── presentation.html           # 宣传演示页
├── AI_Development_Workflows_Analysis.md  # AI 开发工作流分析文章
└── assets/                     # 宣传图片（header、cards、slides）

tests/python-vibeperf/          # 优化前后一致性 + 性能达标测试（12 项）
```

## 快速验证

```bash
pip install -r <skill-directory>/requirements.txt
python -m pytest tests/python-vibeperf/
```

## 使用

按 `SKILL.md` 的 3 阶段流程执行。入口示例：

- 用 `docs/python-vibeperf/examples/lidar_rasterization.py` 练习性能分析与优化。
- 案例产物 `docs/python-vibeperf/examples/docs/perf/` 展示完整轮次的产物目录结构，可作为输出模板参考。
- 优化经验沉淀请使用配套技能 `python-vibeperf-evolution`。

## 依赖

- `viztracer`：性能追踪与火焰图
- `numpy`：示例程序与测试
- 可选 `superpowers`：流程中按需调用的 brainstorming / writing-plans / TDD 等子技能
