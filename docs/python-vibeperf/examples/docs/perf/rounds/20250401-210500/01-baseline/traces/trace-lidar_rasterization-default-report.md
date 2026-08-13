# VizTracer 性能分析报告

**总记录耗时:** 27.14 s

*(注意：由于函数调用存在嵌套，所有函数的耗时总和可能会大于总记录耗时)*


## 📊 Top 模块耗时排行

| 排名 | 模块名 | 总耗时 | 调用次数 | 平均每次耗时 | 耗时占比 (粗略) |
|------|--------|--------|----------|--------------|----------------|
| 1 | `<module> (C:\Users\Administrator\Documents\python-vibeperf\examples\lidar_rasterization` | 13.57 s | 1 | 13.57 s | 50.0% |
| 2 | `generate_lidar_points (C:\Users\Administrator\Documents\python-vibeperf\examples\lidar_rasterization` | 8.65 s | 1 | 8.65 s | 31.9% |
| 3 | `LiDARPointCloudRasterizer.rasterize (C:\Users\Administrator\Documents\python-vibeperf\examples\lidar_rasterization` | 4.88 s | 1 | 4.88 s | 18.0% |
| 4 | `Random.uniform (C:\ProgramData\Miniconda3\Lib\random` | 12.88 ms | 5 | 2.58 ms | 0.0% |
| 5 | `LiDARPointCloudRasterizer.create_grid (C:\Users\Administrator\Documents\python-vibeperf\examples\lidar_rasterization` | 11.01 ms | 1 | 11.01 ms | 0.0% |
| 6 | `LiDARPointCloudRasterizer.get_occupancy_list (C:\Users\Administrator\Documents\python-vibeperf\examples\lidar_rasterization` | 10.78 ms | 1 | 10.78 ms | 0.0% |
| 7 | `<genexpr> (C:\Users\Administrator\Documents\python-vibeperf\examples\lidar_rasterization` | 3.13 ms | 2 | 1.57 ms | 0.0% |

## 🎯 Top 100 最耗时函数排行

| 排名 | 函数名 | 总耗时 | 调用次数 | 平均每次耗时 | 耗时占比 (粗略) |
|------|--------|--------|----------|--------------|----------------|
| 1 | `<module> (C:\Users\Administrator\Documents\python-vibeperf\examples\lidar_rasterization.py:1)` | 13.57 s | 1 | 13.57 s | 50.0% |
| 2 | `generate_lidar_points (C:\Users\Administrator\Documents\python-vibeperf\examples\lidar_rasterization.py:63)` | 8.65 s | 1 | 8.65 s | 31.9% |
| 3 | `LiDARPointCloudRasterizer.rasterize (C:\Users\Administrator\Documents\python-vibeperf\examples\lidar_rasterization.py:26)` | 4.88 s | 1 | 4.88 s | 18.0% |
| 4 | `Random.uniform (C:\ProgramData\Miniconda3\Lib\random.py:498)` | 12.88 ms | 5 | 2.58 ms | 0.0% |
| 5 | `LiDARPointCloudRasterizer.create_grid (C:\Users\Administrator\Documents\python-vibeperf\examples\lidar_rasterization.py:14)` | 11.01 ms | 1 | 11.01 ms | 0.0% |
| 6 | `LiDARPointCloudRasterizer.get_occupancy_list (C:\Users\Administrator\Documents\python-vibeperf\examples\lidar_rasterization.py:55)` | 10.78 ms | 1 | 10.78 ms | 0.0% |
| 7 | `<genexpr> (C:\Users\Administrator\Documents\python-vibeperf\examples\lidar_rasterization.py:112)` | 3.13 ms | 2 | 1.57 ms | 0.0% |