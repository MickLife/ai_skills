"""
测试 001: 验证点生成 NumPy 优化前后的功能一致性和性能提升
"""
import os
import time
import numpy as np
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples.lidar_rasterization_optimized import generate_lidar_points


def test_output_shape():
    """验证输出形状正确"""
    points = generate_lidar_points(1000)
    assert isinstance(points, np.ndarray), f"输出应为 np.ndarray, 实际为 {type(points)}"
    assert points.shape == (1000, 3), f"形状应为 (1000, 3), 实际为 {points.shape}"
    print("[PASS] test_output_shape")


def test_coordinate_ranges():
    """验证坐标范围符合预期"""
    points = generate_lidar_points(10000)

    # X 坐标范围
    assert -100 <= points[:, 0].min() <= -90, f"X最小值异常: {points[:, 0].min()}"
    assert 90 <= points[:, 0].max() <= 100, f"X最大值异常: {points[:, 0].max()}"

    # Y 坐标范围
    assert -100 <= points[:, 1].min() <= -90, f"Y最小值异常: {points[:, 1].min()}"
    assert 90 <= points[:, 1].max() <= 100, f"Y最大值异常: {points[:, 1].max()}"

    # Z 坐标范围
    assert -10 <= points[:, 2].min() <= -8, f"Z最小值异常: {points[:, 2].min()}"
    assert 8 <= points[:, 2].max() <= 10, f"Z最大值异常: {points[:, 2].max()}"

    print("[PASS] test_coordinate_ranges")


def test_statistical_distribution():
    """验证统计分布（均值应在0附近）"""
    points = generate_lidar_points(50000)

    mean = points.mean(axis=0)
    # 均匀分布在 [-a, a] 的均值应该接近 0
    assert abs(mean[0]) < 1.0, f"X均值偏离0: {mean[0]}"
    assert abs(mean[1]) < 1.0, f"Y均值偏离0: {mean[1]}"
    assert abs(mean[2]) < 0.5, f"Z均值偏离0: {mean[2]}"

    print(f"[PASS] test_statistical_distribution (mean=[{mean[0]:.4f}, {mean[1]:.4f}, {mean[2]:.4f}])")


def test_data_type():
    """验证数据类型"""
    points = generate_lidar_points(100)
    assert points.dtype == np.float64, f"数据类型应为 float64, 实际为 {points.dtype}"
    print("[PASS] test_data_type")


def test_performance():
    """验证性能达标"""
    num_points = 5000000

    start = time.time()
    points = generate_lidar_points(num_points)
    elapsed = time.time() - start

    # 性能目标: < 0.5s
    assert elapsed < 0.5, f"性能不达标: {elapsed:.2f}s >= 0.5s"

    print(f"[PASS] test_performance ({elapsed:.2f}s for {num_points:,} points)")


def test_full_scale_correctness():
    """全量数据正确性验证"""
    points = generate_lidar_points(5000000)

    assert points.shape == (5000000, 3), f"全量形状错误: {points.shape}"
    assert points.dtype == np.float64, f"全量数据类型错误: {points.dtype}"

    # 验证无 NaN 或 Inf
    assert not np.isnan(points).any(), "存在 NaN 值"
    assert not np.isinf(points).any(), "存在 Inf 值"

    print("[PASS] test_full_scale_correctness")


if __name__ == "__main__":
    print("=" * 60)
    print("测试 001: 点生成 NumPy 优化验证")
    print("=" * 60)

    try:
        test_output_shape()
        test_coordinate_ranges()
        test_statistical_distribution()
        test_data_type()
        test_full_scale_correctness()
        test_performance()

        print("\n" + "=" * 60)
        print("所有测试通过!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 测试出错: {e}")
        sys.exit(1)
