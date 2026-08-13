import math
import time
import sys
import numpy as np


class LiDARPointCloudRasterizer:
    def __init__(self, width, height, resolution):
        self.width = width
        self.height = height
        self.resolution = resolution
        self.grid = []

    def create_grid(self):
        """使用 NumPy 数组初始化栅格 - 高性能"""
        self.grid = np.zeros((self.height, self.width), dtype=np.int32)

    def rasterize(self, points):
        """NumPy 向量化栅格化 - 高性能实现"""
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
        """使用 NumPy flatten 展平栅格 - 高性能"""
        return self.grid.flatten().tolist()


def generate_lidar_points(num_points):
    """NumPy批量生成LiDAR点云数据 - 高性能实现"""
    points = np.random.uniform(
        low=[-100, -100, -10],
        high=[100, 100, 10],
        size=(num_points, 3)
    )
    return points


if __name__ == "__main__":
    print(f"Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    print("LiDAR Point Cloud Rasterization Performance Test")
    print("=" * 50)

    num_points = 5000000
    print(f"Generating {num_points} LiDAR points...")
    start_time = time.time()
    points = generate_lidar_points(num_points)
    gen_time = time.time() - start_time
    print(f"Point generation time: {gen_time:.2f}s")

    width, height = 500, 500
    resolution = 0.5

    print(f"\nInitializing {width}x{height} grid...")
    start_time = time.time()
    rasterizer = LiDARPointCloudRasterizer(width, height, resolution)
    rasterizer.create_grid()
    init_time = time.time() - start_time
    print(f"Grid initialization time: {init_time:.2f}s")

    print(f"\nRasterizing {num_points} points...")
    start_time = time.time()
    rasterizer.rasterize(points)
    rasterize_time = time.time() - start_time
    print(f"Rasterization time: {rasterize_time:.2f}s")

    print(f"\nExtracting occupancy list...")
    start_time = time.time()
    occupancy = rasterizer.get_occupancy_list()
    extract_time = time.time() - start_time
    print(f"Occupancy extraction time: {extract_time:.2f}s")

    total_time = gen_time + init_time + rasterize_time + extract_time
    print(f"\n{'=' * 50}")
    print(f"Total execution time: {total_time:.2f}s")

    occupied_cells = sum(1 for cell in occupancy if cell > 0)
    print(f"Occupied cells: {occupied_cells}")
    print(f"Total cells: {len(occupancy)}")