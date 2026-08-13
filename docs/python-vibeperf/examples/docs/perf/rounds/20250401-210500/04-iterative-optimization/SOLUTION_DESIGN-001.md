# 任务 001 设计方案：点生成 NumPy 化

## 基本信息

| 属性 | 值 |
|------|-----|
| **任务ID** | PERF-001 |
| **任务名称** | 点生成 NumPy 化 |
| **目标函数** | `generate_lidar_points()` |
| **当前耗时** | 5.63s (基线) / 5.77s (实验) |
| **目标耗时** | < 0.5s |
| **优先级** | P0 - 最高 |

## 实验验证结果

### 实验配置

- **实验脚本**: `experiments/experiment_001_numpy_points.py`
- **测试数据量**: 5,000,000 个点
- **测试环境**: Python 3.13.11, NumPy 2.2.x

### 性能对比数据

| 实现方式 | 耗时 | 加速比 | 时间减少 |
|----------|------|--------|----------|
| Python 循环 + random.uniform() | **5.77s** | 1.0x (基准) | - |
| NumPy 批量生成 | **0.22s** | **26.8x** | **96.3%** |

### 输出一致性验证

| 验证项 | Python 实现 | NumPy 实现 | 结果 |
|--------|-------------|------------|------|
| 输出形状 | (5000000, 3) | (5000000, 3) | ✅ 一致 |
| X坐标范围 | [-100.00, 100.00] | [-100.00, 100.00] | ✅ 一致 |
| Y坐标范围 | [-100.00, 100.00] | [-100.00, 100.00] | ✅ 一致 |
| Z坐标范围 | [-10.00, 10.00] | [-10.00, 10.00] | ✅ 一致 |
| 均值 | [-0.0242, -0.0115, -0.0038] | [-0.0063, 0.0011, 0.0015] | ✅ 接近0（符合均匀分布） |

**结论**: 实验验证通过，NumPy 实现性能提升 26.8 倍，输出一致性符合预期。

## 设计方案

### 优化前代码

```python
def generate_lidar_points(num_points):
    """原始 Python 实现 - 性能瓶颈"""
    points = []
    for i in range(num_points):              # 500万次 Python 层循环
        x = random.uniform(-100, 100)        # Python 函数调用开销
        y = random.uniform(-100, 100)        # 每次循环3次调用
        z = random.uniform(-10, 10)
        points.append([x, y, z])            # 动态列表扩容
    return points                            # 返回 List[List[float]]
```

### 优化后代码

```python
import numpy as np

def generate_lidar_points(num_points):
    """NumPy 向量化实现 - 高性能"""
    points = np.random.uniform(
        low=[-100, -100, -10],
        high=[100, 100, 10],
        size=(num_points, 3)
    )
    return points                              # 返回 np.ndarray, shape=(N, 3)
```

### 关键技术点

| 优化点 | 原实现 | 新实现 | 收益 |
|--------|--------|--------|------|
| 随机数生成 | Python `random.uniform()` 1500万次调用 | NumPy C 层批量生成 | 消除 Python 函数调用开销 |
| 循环结构 | Python 层 500万次迭代 | NumPy 底层 C 循环 | 利用 SIMD 指令加速 |
| 内存分配 | 列表动态扩容 23次 | 预分配连续内存块 | 消除内存复制开销 |
| 数据类型 | Python float 对象列表 | NumPy float64 数组 | 内存紧凑，缓存友好 |

## 实施步骤

### 步骤 1: 代码修改

修改 `examples/lidar_rasterization.py` 中的 `generate_lidar_points` 函数：

1. 添加 `import numpy as np` 到文件顶部
2. 替换函数实现为 NumPy 版本
3. 确保返回值类型为 `numpy.ndarray`

### 步骤 2: 兼容性适配

检查下游依赖：

- `LiDARPointCloudRasterizer.rasterize(points)` 方法需要适配 NumPy 数组输入
- 当前实现使用 `for point in points` 和 `point[0], point[1], point[2]` 访问
- NumPy 数组支持相同的迭代和索引访问，但为任务 002 预留向量化空间

### 步骤 3: 测试验证

#### 功能测试

```python
def test_generate_lidar_points():
    points = generate_lidar_points(1000)
    assert isinstance(points, np.ndarray)
    assert points.shape == (1000, 3)
    assert points.dtype == np.float64
    assert -100 <= points[:, 0].min() and points[:, 0].max() <= 100
    assert -100 <= points[:, 1].min() and points[:, 1].max() <= 100
    assert -10 <= points[:, 2].min() and points[:, 2].max() <= 10
```

#### 性能测试

```python
def test_performance():
    import time
    start = time.time()
    points = generate_lidar_points(5_000_000)
    elapsed = time.time() - start
    assert elapsed < 0.5  # 目标: < 0.5s
    print(f"点生成耗时: {elapsed:.2f}s")
```

### 步骤 4: 提交代码

- 使用 git commit 提交修改
- 生成 OPTIMIZATION_EXECUTION-001.md 记录执行结果

## 依赖与约束

### 依赖项

- **numpy**: 新增依赖，已获用户批准

### 约束条件

1. **功能一致性**: 输出点的坐标范围必须保持不变
2. **性能目标**: 耗时 < 0.5s（实验已验证可达 0.22s）
3. **接口兼容**: 返回类型从 list 改为 ndarray，但形状保持一致性

## 风险与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 下游代码不兼容 NumPy 数组 | 低 | 中 | 验证 `rasterize()` 方法可接受 ndarray |
| 内存占用增加 | 低 | 低 | 5M×3×8B=120MB，可接受 |
| 随机分布差异 | 低 | 低 | 实验已验证均值范围一致 |

## 预期成果

### 性能指标

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 点生成耗时 | 5.63s | ~0.22s | **26.8x** |
| 总脚本耗时 | 9.38s | ~3.97s | **2.4x** |

### 代码指标

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 代码行数 | 8行 | 5行 |
| 圈复杂度 | O(N) 循环 | O(1) 批处理 |
| 依赖项 | 标准库 | 标准库 + NumPy |

## 验收标准（DoD）

- [x] 实验验证性能提升 > 10x
- [ ] 修改 `generate_lidar_points` 使用 NumPy 实现
- [ ] 点生成耗时 < 0.5s
- [ ] 输出形状为 `(5000000, 3)` 的 numpy.ndarray
- [ ] 坐标范围符合预期 [-100,100] / [-10,10]
- [ ] 基准测试通过（性能对比数据记录）
- [ ] 代码提交到 git

## 下一步

完成本设计方案后，执行以下操作：
1. 读取 `executing-plans` 技能执行代码修改
2. 读取 `test-driven-development` 技能补充测试用例
3. 读取 `verification-before-completion` 技能验证并提交
4. 生成 `OPTIMIZATION_EXECUTION-001.md`

---

**实验结论**: ✅ 验证通过，NumPy 实现性能提升 26.8 倍，可直接进入实施阶段。
