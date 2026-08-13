"""
测试 002: 验证栅格化向量化优化前后的功能一致性和性能提升
"""
import os
import time
import numpy as np
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples.lidar_rasterization_optimized import LiDARPointCloudRasterizer, generate_lidar_points


def test_grid_creation():
    """验证栅格创建使用 NumPy 数组"""
    rasterizer = LiDARPointCloudRasterizer(500, 500, 0.5)
    rasterizer.create_grid()

    assert isinstance(rasterizer.grid, np.ndarray), f"栅格应为 np.ndarray, 实际为 {type(rasterizer.grid)}"
    assert rasterizer.grid.shape == (500, 500), f"栅格形状应为 (500, 500), 实际为 {rasterizer.grid.shape}"
    assert rasterizer.grid.dtype == np.int32, f"栅格数据类型应为 int32, 实际为 {rasterizer.grid.dtype}"
    assert np.all(rasterizer.grid == 0), "栅格应初始化为0"
    print("[PASS] test_grid_creation")


def test_rasterize_output():
    """验证栅格化输出正确"""
    rasterizer = LiDARPointCloudRasterizer(500, 500, 0.5)
    rasterizer.create_grid()

    # 生成测试点
    np.random.seed(42)
    points = generate_lidar_points(100000)

    rasterizer.rasterize(points)

    # 验证栅格值范围
    unique_values = np.unique(rasterizer.grid)
    expected_values = {0, 20, 40, 60, 80, 100}
    actual_values = set(unique_values.tolist())
    assert actual_values.issubset(expected_values), f"栅格值 {actual_values} 超出预期 {expected_values}"

    print("[PASS] test_rasterize_output")


def test_rasterize_performance():
    """验证栅格化性能达标"""
    rasterizer = LiDARPointCloudRasterizer(500, 500, 0.5)
    rasterizer.create_grid()

    np.random.seed(42)
    points = generate_lidar_points(5000000)

    start = time.time()
    rasterizer.rasterize(points)
    elapsed = time.time() - start

    # 性能目标: < 0.5s
    assert elapsed < 0.5, f"性能不达标: {elapsed:.2f}s >= 0.5s"

    print(f"[PASS] test_rasterize_performance ({elapsed:.2f}s for 5M points)")


def test_occupancy_list():
    """验证占用列表输出"""
    rasterizer = LiDARPointCloudRasterizer(500, 500, 0.5)
    rasterizer.create_grid()

    np.random.seed(42)
    points = generate_lidar_points(100000)
    rasterizer.rasterize(points)

    occupancy = rasterizer.get_occupancy_list()

    assert isinstance(occupancy, list), f"占用列表应为 list, 实际为 {type(occupancy)}"
    assert len(occupancy) == 500 * 500, f"占用列表长度应为 250000, 实际为 {len(occupancy)}"

    occupied_count = sum(1 for cell in occupancy if cell > 0)
    print(f"[PASS] test_occupancy_list (occupied: {occupied_count})")


def test_rasterize_consistency():
    """全量数据一致性验证"""
    rasterizer = LiDARPointCloudRasterizer(500, 500, 0.5)
    rasterizer.create_grid()

    # 使用固定种子确保可复现
    np.random.seed(42)
    points = generate_lidar_points(5000000)

    rasterizer.rasterize(points)

    # 验证栅格形状和类型
    assert rasterizer.grid.shape == (500, 500)
    assert rasterizer.grid.dtype == np.int32

    # 验证占用单元格数（应与基准接近 31725）
    occupied = np.sum(rasterizer.grid > 0)
    assert 31000 < occupied < 32500, f"占用单元格数 {occupied} 超出预期范围"

    # 验证栅格值分布
    unique, counts = np.unique(rasterizer.grid, return_counts=True)
    distribution = dict(zip(unique.tolist(), counts.tolist()))

    # 预期的分布模式
    assert 0 in distribution, "应包含空单元格(0)"
    assert distribution[0] > 200000, "空单元格应占多数"

    print(f"[PASS] test_rasterize_consistency (occupied: {occupied}, distribution: {distribution})")


def test_full_pipeline():
    """完整流程测试"""
    np.random.seed(42)

    # 1. 生成点
    points = generate_lidar_points(5000000)
    assert isinstance(points, np.ndarray)
    assert points.shape == (5000000, 3)

    # 2. 初始化栅格
    rasterizer = LiDARPointCloudRasterizer(500, 500, 0.5)
    rasterizer.create_grid()
    assert isinstance(rasterizer.grid, np.ndarray)

    # 3. 栅格化
    rasterizer.rasterize(points)
    occupied = np.sum(rasterizer.grid > 0)
    assert 31000 < occupied < 32500

    # 4. 提取占用列表
    occupancy = rasterizer.get_occupancy_list()
    assert isinstance(occupancy, list)
    assert len(occupancy) == 250000
    occupied_in_list = sum(1 for cell in occupancy if cell > 0)
    assert occupied == occupied_in_list, "栅格占用数应与列表一致"

    print(f"[PASS] test_full_pipeline (occupied: {occupied})")


if __name__ == "__main__":
    print("=" * 60)
    print("测试 002: 栅格化向量化优化验证")
    print("=" * 60)

    try:
        test_grid_creation()
        test_rasterize_output()
        test_occupancy_list()
        test_rasterize_consistency()
        test_full_pipeline()
        test_rasterize_performance()

        print("\n" + "=" * 60)
        print("所有测试通过!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
