import random
import math
import time
import sys


class LiDARPointCloudRasterizer:
    def __init__(self, width, height, resolution):
        self.width = width
        self.height = height
        self.resolution = resolution
        self.grid = []

    def create_grid(self):
        for _ in range(self.height):
            row = []
            for _ in range(self.width):
                row.append(0)
            self.grid.append(row)

    def euclidean_distance(self, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        return math.sqrt(dx * dx + dy * dy)

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
                    grid_dist = self.euclidean_distance(grid_x, grid_y, center_x, center_y)

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
        occupancy = []
        for row in self.grid:
            for cell in row:
                occupancy.append(cell)
        return occupancy


def generate_lidar_points(num_points):
    points = []
    for i in range(num_points):
        x = random.uniform(-100, 100)
        y = random.uniform(-100, 100)
        z = random.uniform(-10, 10)
        points.append([x, y, z])
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