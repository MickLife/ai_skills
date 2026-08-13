# 性能基线测试执行记录

## 环境信息

| 项目 | 值 |
|------|-----|
| Python 版本 | 3.13.11 |
| 操作系统 | Windows Server (win32 10.0.20348) |
| VizTracer 版本 | 1.1.1 |
| 测试时间 | 2025-04-01 21:05:00 |

## 纯净运行记录

### 执行命令

```powershell
python examples/lidar_rasterization.py
```

### 执行结果

```
Python version: 3.13.11
LiDAR Point Cloud Rasterization Performance Test
==================================================
Generating 5000000 LiDAR points...
Point generation time: 5.63s

Initializing 500x500 grid...
Grid initialization time: 0.01s

Rasterizing 5000000 points...
Rasterization time: 3.73s

Extracting occupancy list...
Occupancy extraction time: 0.01s

==================================================
Total execution time: 9.38s
Occupied cells: 31739
Total cells: 250000
```

### 性能数据汇总

| 阶段 | 耗时 | 占比 |
|------|------|------|
| 点生成 (generate_lidar_points) | 5.63s | 60.0% |
| 网格初始化 (create_grid) | 0.01s | 0.1% |
| 栅格化 (rasterize) | 3.73s | 39.7% |
| 占用提取 (get_occupancy_list) | 0.01s | 0.1% |
| **总计** | **9.38s** | **100%** |

**输出数据验证**:
- 占用单元格数: 31,739
- 总单元格数: 250,000
- 占用率: 12.7%

## VizTracer 追踪运行记录

### 执行命令

```powershell
python -m viztracer -o docs/perf/rounds/20250401-210500/01-baseline/traces/trace-lidar_rasterization-default.json --tracer_entries 20000000 --ignore_c_function --ignore_frozen --min_duration 0.5ms examples/lidar_rasterization.py
```

### 执行结果

```
Python version: 3.13.11
LiDAR Point Cloud Rasterization Performance Test
==================================================
Generating 5000000 LiDAR points...
Point generation time: 8.65s

Initializing 500x500 grid...
Grid initialization time: 0.01s

Rasterizing 5000000 points...
Rasterization time: 4.88s

Extracting occupancy list...
Occupancy extraction time: 0.01s

==================================================
Total execution time: 13.56s
Occupied cells: 31728
Total cells: 250000

Total Entries: 14
```

### 追踪数据说明

- **追踪条目数**: 14（min_duration=0.5ms 过滤后）
- **追踪文件**: `docs/perf/rounds/20250401-210500/01-baseline/traces/trace-lidar_rasterization-default.json`
- **查看命令**: `vizviewer trace-lidar_rasterization-default.json`

### 分析命令

```powershell
python skills/python-vibeperf/scripts/analyze_viztracer.py docs/perf/rounds/20250401-210500/01-baseline/traces/trace-lidar_rasterization-default.json -o docs/perf/rounds/20250401-210500/01-baseline/traces/trace-lidar_rasterization-default-report.md -n 20
```

## 热点函数识别

根据 VizTracer 报告，主要性能瓶颈函数：

| 排名 | 函数名 | 耗时 | 占比 | 调用次数 |
|------|--------|------|------|----------|
| 1 | `generate_lidar_points` | 8.65s | 31.9% | 1 |
| 2 | `LiDARPointCloudRasterizer.rasterize` | 4.88s | 18.0% | 1 |
| 3 | `LiDARPointCloudRasterizer.create_grid` | 11.01ms | 0.0% | 1 |
| 4 | `LiDARPointCloudRasterizer.get_occupancy_list` | 10.78ms | 0.0% | 1 |

## 基线结论

1. **主要瓶颈**: 点生成 (`generate_lidar_points`) 和 栅格化 (`rasterize`) 是两大热点函数
2. **次要瓶颈**: 网格初始化和占用提取耗时极短，优化优先级低
3. **优化方向**: 重点优化点生成和栅格化算法的效率
4. **追踪开销**: VizTracer 带来约 40-50% 的性能开销（纯净运行 9.38s vs 追踪运行 13.56s）

## 下一步行动

进入 **阶段2: 性能瓶颈分析**，深入阅读代码，分析热点函数的具体瓶颈所在。
