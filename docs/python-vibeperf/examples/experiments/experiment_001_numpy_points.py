#!/usr/bin/env python
"""
实验 001: 验证 NumPy 批量生成点 vs Python 循环生成点的性能差异
"""
import time
import random
import numpy as np


def generate_lidar_points_python(num_points):
    """原始 Python 实现"""
    points = []
    for i in range(num_points):
        x = random.uniform(-100, 100)
        y = random.uniform(-100, 100)
        z = random.uniform(-10, 10)
        points.append([x, y, z])
    return points


def generate_lidar_points_numpy(num_points):
    """NumPy 向量化实现"""
    points = np.random.uniform(
        low=[-100, -100, -10],
        high=[100, 100, 10],
        size=(num_points, 3)
    )
    return points


def verify_consistency(py_points, np_points, tolerance=1e-6):
    """验证两种实现的输出一致性（统计分布）"""
    # 转换为 numpy 以便比较
    py_array = np.array(py_points)

    # 检查形状
    assert py_array.shape == np_points.shape, f"形状不一致: {py_array.shape} vs {np_points.shape}"

    # 检查范围
    py_x_range = (py_array[:, 0].min(), py_array[:, 0].max())
    np_x_range = (np_points[:, 0].min(), np_points[:, 0].max())

    print(f"  Python X范围: [{py_x_range[0]:.2f}, {py_x_range[1]:.2f}]")
    print(f"  NumPy X范围:  [{np_x_range[0]:.2f}, {np_x_range[1]:.2f}]")

    # 检查均值（应该在0附近）
    py_mean = py_array.mean(axis=0)
    np_mean = np_points.mean(axis=0)

    print(f"  Python均值: [{py_mean[0]:.4f}, {py_mean[1]:.4f}, {py_mean[2]:.4f}]")
    print(f"  NumPy均值:  [{np_mean[0]:.4f}, {np_mean[1]:.4f}, {np_mean[2]:.4f}]")

    # 粗略验证：均值接近0，范围合理
    assert abs(py_mean[0]) < 1.0, "Python X均值偏离0太多"
    assert abs(np_mean[0]) < 1.0, "NumPy X均值偏离0太多"

    print("  [OK] 一致性检查通过")


def main():
    num_points = 5000000  # 与原始脚本一致

    print("=" * 60)
    print("实验 001: 点生成性能对比")
    print("=" * 60)
    print(f"\n测试规模: {num_points:,} 个点")

    # Python 版本测试
    print("\n[1/2] Python 实现测试...")
    random.seed(42)  # 固定随机种子以便复现
    start = time.time()
    py_points = generate_lidar_points_python(num_points)
    py_time = time.time() - start
    print(f"  耗时: {py_time:.2f}s")

    # NumPy 版本测试
    print("\n[2/2] NumPy 实现测试...")
    np.random.seed(42)  # 固定随机种子
    start = time.time()
    np_points = generate_lidar_points_numpy(num_points)
    np_time = time.time() - start
    print(f"  耗时: {np_time:.2f}s")

    # 验证一致性
    print("\n[验证] 输出一致性检查...")
    verify_consistency(py_points, np_points)

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
    exit(0 if speedup > 10 else 1)  # 如果加速比>10x则认为实验成功
