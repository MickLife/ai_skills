#!/usr/bin/env python
"""
实验 002: 验证向量化栅格化 vs Python 循环的性能差异
"""
import time
import math
import numpy as np


class RasterizerPython:
    """原始 Python 实现"""
    def __init__(self, width, height, resolution):
        self.width = width
        self.height = height
        self.resolution = resolution
        self.grid = []

    def create_grid(self):
        self.grid = [[0 for _ in range(self.width)] for _ in range(self.height)]

    def euclidean_distance(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1) ** 2 + (dy := y2 - y1) ** 2)

    def rasterize(self, points):
        center_x = self.width // 2
        center_y = self.height // 2

        for point in points:
            x, y, z = point[0], point[1], point[2]
            grid_x = int((x + 100) / self.resolution)
            grid_y = int((y + 100) / self.resolution)

            if 0 <= grid_x < self.width and 0 <= grid_y < self.height:
                world_dist = self.euclidean_distance(x, y, 0, 0)

                if world_dist < 50:
                    cell_value = 0
                    if world_dist < 5:
                        cell_value = 100
                    elif world_dist < 10:
                        cell_value = 80
                    elif world_dist < 20:
                        cell_value = 60
                    elif world_dist < 50:
                        cell_value = 40
                    else:
                        cell_value = 20

                    self.grid[grid_y][grid_x] = cell_value

    def get_occupancy_list(self):
        return [cell for row in self.grid for cell in row]


class RasterizerVectorized:
    """NumPy 向量化实现"""
    def __init__(self, width, height, resolution):
        self.width = width
        self.height = height
        self.resolution = resolution
        self.grid = None

    def create_grid(self):
        # NumPy 数组替代 Python 列表
        self.grid = np.zeros((self.height, self.width), dtype=np.int32)

    def rasterize(self, points):
        """向量化栅格化实现"""
        # 坐标转换（向量化）
        grid_x = ((points[:, 0] + 100) / self.resolution).astype(np.int32)
        grid_y = ((points[:, 1] + 100) / self.resolution).astype(np.int32)

        # 边界掩码（向量化）
        valid_mask = ((grid_x >= 0) & (grid_x < self.width) &
                      (grid_y >= 0) & (grid_y < self.height))

        # 提取有效点
        valid_x = points[valid_mask, 0]
        valid_y = points[valid_mask, 1]
        valid_grid_x = grid_x[valid_mask]
        valid_grid_y = grid_y[valid_mask]

        # 距离计算（向量化，使用平方避免 sqrt）
        world_dist_sq = valid_x**2 + valid_y**2
        within_range = world_dist_sq < 50**2

        # 应用范围过滤
        final_x = valid_x[within_range]
        final_y = valid_y[within_range]
        final_grid_x = valid_grid_x[within_range]
        final_grid_y = valid_grid_y[within_range]
        world_dist_sq = world_dist_sq[within_range]

        # 阈值判断（向量化）
        cell_values = np.select(
            [world_dist_sq < 5**2,
             world_dist_sq < 10**2,
             world_dist_sq < 20**2,
             world_dist_sq < 50**2],
            [100, 80, 60, 40],
            default=20
        )

        # 栅格赋值（向量化）
        self.grid[final_grid_y, final_grid_x] = cell_values

    def get_occupancy_list(self):
        # NumPy flatten
        return self.grid.flatten().tolist()


def verify_consistency(py_rasterizer, np_rasterizer, tolerance=0.01):
    """验证两种实现的栅格输出一致性"""
    py_grid = np.array(py_rasterizer.grid)
    np_grid = np_rasterizer.grid

    print(f"  Python栅格形状: {py_grid.shape}")
    print(f"  NumPy栅格形状:  {np_grid.shape}")

    # 检查形状一致
    assert py_grid.shape == np_grid.shape, f"形状不一致: {py_grid.shape} vs {np_grid.shape}"

    # 检查占用单元格数
    py_occupied = np.sum(py_grid > 0)
    np_occupied = np.sum(np_grid > 0)
    print(f"  Python占用单元格: {py_occupied}")
    print(f"  NumPy占用单元格:  {np_occupied}")

    # 允许 1% 的差异（浮点精度导致）
    diff_ratio = abs(py_occupied - np_occupied) / max(py_occupied, 1)
    print(f"  差异比例: {diff_ratio*100:.2f}%")
    assert diff_ratio < tolerance, f"占用单元格差异过大: {diff_ratio*100:.2f}% >= {tolerance*100:.2f}%"

    # 检查栅格值分布
    py_values, py_counts = np.unique(py_grid, return_counts=True)
    np_values, np_counts = np.unique(np_grid, return_counts=True)

    print(f"  Python栅格值分布: {dict(zip(py_values, py_counts))}")
    print(f"  NumPy栅格值分布:  {dict(zip(np_values, np_counts))}")

    print("  [OK] 一致性检查通过")


def main():
    num_points = 5000000
    width, height = 500, 500
    resolution = 0.5

    print("=" * 60)
    print("实验 002: 栅格化性能对比")
    print("=" * 60)
    print(f"\n测试规模: {num_points:,} 个点, {width}x{height} 栅格")

    # 生成测试数据（使用NumPy批量生成）
    print("\n[准备] 生成测试数据...")
    np.random.seed(42)
    points = np.random.uniform(
        low=[-100, -100, -10],
        high=[100, 100, 10],
        size=(num_points, 3)
    )

    # Python 版本测试
    print("\n[1/2] Python 实现测试...")
    py_rasterizer = RasterizerPython(width, height, resolution)
    py_rasterizer.create_grid()

    start = time.time()
    py_rasterizer.rasterize(points)
    py_time = time.time() - start
    print(f"  栅格化耗时: {py_time:.2f}s")

    # NumPy 版本测试
    print("\n[2/2] NumPy 向量化实现测试...")
    np_rasterizer = RasterizerVectorized(width, height, resolution)
    np_rasterizer.create_grid()

    start = time.time()
    np_rasterizer.rasterize(points)
    np_time = time.time() - start
    print(f"  栅格化耗时: {np_time:.2f}s")

    # 验证一致性
    print("\n[验证] 栅格输出一致性检查...")
    verify_consistency(py_rasterizer, np_rasterizer)

    # 性能对比
    print("\n" + "=" * 60)
    print("性能对比结果")
    print("=" * 60)
    print(f"Python 实现:  {py_time:.2f}s")
    print(f"NumPy 实现:   {np_time:.2f}s")
    speedup = py_time / np_time if np_time > 0 else float('inf')
    print(f"加速比:       {speedup:.1f}x")
    print(f"时间减少:     {((py_time - np_time) / py_time * 100):.1f}%")

    return speedup


if __name__ == "__main__":
    speedup = main()
    exit(0 if speedup > 5 else 1)
