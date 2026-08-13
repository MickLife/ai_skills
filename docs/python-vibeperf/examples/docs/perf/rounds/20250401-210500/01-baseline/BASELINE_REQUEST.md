# 性能基线测试需求

## 测试目标

为 `examples/lidar_rasterization.py` 脚本建立性能基线，收集真实性能数据，为后续优化提供客观依据。

## 测试脚本

- **路径**: `examples/lidar_rasterization.py`
- **功能**: LiDAR点云栅格化处理

## 脚本参数

脚本使用硬编码参数，无需额外输入：

| 参数 | 值 | 说明 |
|------|-----|------|
| num_points | 5,000,000 | 生成的LiDAR点数量 |
| width | 500 | 栅格网格宽度 |
| height | 500 | 栅格网格高度 |
| resolution | 0.5 | 栅格分辨率 |

## 测试类型

### 1. 纯净运行（无 VizTracer）

**目的**: 获取真实的执行时间作为优化效果对比基准

**命令**:
```bash
python examples/lidar_rasterization.py
```

**关注指标**:
- 点生成时间
- 网格初始化时间
- 栅格化时间
- 占用提取时间
- 总执行时间

### 2. VizTracer 追踪运行

**目的**: 生成详细的函数级性能数据，用于瓶颈分析

**命令**:
```bash
python -m viztracer -o <output_path> --tracer_entries 20000000 --ignore_c_function --ignore_frozen --min_duration 0.5ms examples/lidar_rasterization.py
```

**参数配置**:
- `--tracer_entries 20000000`: 最大追踪条目数 2000万
- `--ignore_c_function`: 忽略 C 函数调用，减少数据量
- `--ignore_frozen`: 忽略冻结模块
- `--min_duration 0.5ms`: 只记录耗时超过 0.5ms 的函数

**输出文件**: `docs/perf/rounds/20250401-210500/01-baseline/traces/trace-lidar_rasterization-default.json`

## 预期结果

基线数据应包含：
1. 各阶段纯执行时间
2. 函数级调用耗时统计
3. 热点函数识别

## 成功标准

- [x] 纯净运行成功完成并输出各阶段耗时
- [x] VizTracer 追踪运行成功并生成 JSON 文件
- [x] 分析报告成功生成
