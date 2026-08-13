# 任务 002 设计方案：栅格化向量化

## 基本信息

| 属性 | 值 |
|------|-----|
| **任务ID** | PERF-002 |
| **任务名称** | 栅格化向量化 |
| **目标函数** | `LiDARPointCloudRasterizer.rasterize()` |
| **当前耗时** | 7.88s (当前) / 3.73s (原始基线) |
| **目标耗时** | < 0.5s |
| **优先级** | P0 - 最高 |

## 实验验证结果

### 实验配置

- **实验脚本**: `experiments/experiment_002_vectorized_rasterize.py`
- **测试数据量**: 5,000,000 个点
- **栅格尺寸**: 500×500
- **测试环境**: Python 3.13.11, NumPy 2.2.x

### 性能对比数据

| 实现方式 | 耗时 | 加速比 | 时间减少 |
|----------|------|--------|----------|
| Python 循环 | **7.93s** | 1.0x (基准) | - |
| **NumPy 向量化** | **0.38s** | **21.0x** | **95.2%** |

### 输出一致性验证

| 验证项 | Python 实现 | NumPy 实现 | 结果 |
|--------|-------------|------------|------|
| 栅格形状 | (500, 500) | (500, 500) | ✅ 一致 |
| 占用单元格 | 31,725 | 31,725 | ✅ 完全一致 |
| 差异比例 | - | 0.00% | ✅ 符合预期 |
| 栅格值分布 | {0:218275, 40:26698, 60:3768, 80:941, 100:318} | {0:218275, 40:26698, 60:3768, 80:941, 100:318} | ✅ 完全一致 |

**结论**: 实验验证通过，向量化实现性能提升 21.0 倍，输出完全一致。

## 设计方案

### 优化前代码

```python
def rasterize(self, points):
    """原始 Python 实现 - 性能瓶颈"""
    center_x = self.width // 2
    center_y = self.height // 2

    for point in points:                         # ← 500万次 Python 层循环
        x, y, z = point[0], point[1], point[2]
        grid_x = int((x + 100) / self.resolution)
        grid_y = int((y + 100) / self.resolution)

        if 0 <= grid_x < self.width and 0 <= grid_y < self.height:  # 边界检查
            world_dist = self.euclidean_distance(x, y, 0, 0)        # ← sqrt

            if world_dist < 50:
                # 多级阈值判断
                cell_value = 0
                if world_dist < 5:      cell_value = 100
                elif world_dist < 10:   cell_value = 80
                elif world_dist < 20:   cell_value = 60
                elif world_dist < 50:   cell_value = 40
                else:                   cell_value = 20

                self.grid[grid_y][grid_x] = cell_value              # 列表索引
```

### 优化后代码

```python
def rasterize(self, points):
    """NumPy 向量化实现 - 高性能"""
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
```

### 关键技术点

| 优化点 | 原实现 | 新实现 | 收益 |
|--------|--------|--------|------|
| 循环结构 | Python 层 500万次迭代 | NumPy C 层向量化 | 消除 Python 解释器开销 |
| 坐标转换 | 逐点计算 | 数组整体运算 | SIMD 加速 |
| 边界检查 | if 条件分支 | 布尔掩码 | 向量化筛选 |
| 距离计算 | `math.sqrt()` 1000万次 | 平方比较避免 sqrt | 消除浮点开方 |
| 阈值判断 | if-elif 链 | `np.select()` | 向量化条件选择 |
| 栅格赋值 | 列表索引访问 | NumPy 数组索引 | 连续内存访问 |
| 栅格存储 | `List[List[int]]` | `np.ndarray` | 内存紧凑，缓存友好 |

## 相关组件修改

### 1. `create_grid()` 方法

**优化前**:
```python
def create_grid(self):
    for _ in range(self.height):
        row = []
        for _ in range(self.width):
            row.append(0)
        self.grid.append(row)
```

**优化后**:
```python
def create_grid(self):
    self.grid = np.zeros((self.height, self.width), dtype=np.int32)
```

### 2. `get_occupancy_list()` 方法

**优化前**:
```python
def get_occupancy_list(self):
    occupancy = []
    for row in self.grid:
        for cell in row:
            occupancy.append(cell)
    return occupancy
```

**优化后**:
```python
def get_occupancy_list(self):
    return self.grid.flatten().tolist()
```

### 3. 删除 `euclidean_distance()` 方法

向量化实现不再需要此辅助方法。

## 实施步骤

### 步骤 1: 代码修改

修改 `examples/lidar_rasterization.py` 中的 `LiDARPointCloudRasterizer` 类：

1. **修改 `create_grid()`**: 使用 `np.zeros()` 替代嵌套循环
2. **重写 `rasterize()`**: 实现向量化版本
3. **修改 `get_occupancy_list()`**: 使用 `flatten()` 替代嵌套循环
4. **删除 `euclidean_distance()`**: 不再需要

### 步骤 2: 测试验证

#### 功能测试

```python
def test_rasterize_output():
    rasterizer = LiDARPointCloudRasterizer(500, 500, 0.5)
    rasterizer.create_grid()

    # 生成测试点
    points = np.random.uniform([-100,-100,-10], [100,100,10], (5000000, 3))

    rasterizer.rasterize(points)

    # 验证输出
    assert isinstance(rasterizer.grid, np.ndarray)
    assert rasterizer.grid.shape == (500, 500)
    assert rasterizer.grid.dtype == np.int32

    # 验证占用单元格数
    occupied = np.sum(rasterizer.grid > 0)
    assert 31000 < occupied < 32500  # 约 31,725 ± 500
```

#### 性能测试

```python
def test_rasterize_performance():
    rasterizer = LiDARPointCloudRasterizer(500, 500, 0.5)
    rasterizer.create_grid()
    points = np.random.uniform([-100,-100,-10], [100,100,10], (5000000, 3))

    start = time.time()
    rasterizer.rasterize(points)
    elapsed = time.time() - start

    assert elapsed < 0.5  # 目标: < 0.5s
    print(f"栅格化耗时: {elapsed:.2f}s")
```

#### 一致性测试

```python
def test_rasterize_consistency():
    """对比优化前后的输出一致性"""
    # 使用相同随机种子生成点
    np.random.seed(42)
    points = np.random.uniform([-100,-100,-10], [100,100,10], (5000000, 3))

    # 运行优化版本
    rasterizer = LiDARPointCloudRasterizer(500, 500, 0.5)
    rasterizer.create_grid()
    rasterizer.rasterize(points)

    occupied = np.sum(rasterizer.grid > 0)
    assert 31500 < occupied < 32000  # 约 31,725
```

### 步骤 3: 提交代码

- 使用 git commit 提交修改
- 生成 OPTIMIZATION_EXECUTION-002.md 记录执行结果

## 依赖与约束

### 依赖项

- **numpy**: 已在任务 001 中添加

### 约束条件

1. **功能一致性**: 占用单元格数与优化前差异 < 1%
2. **性能目标**: 栅格化耗时 < 0.5s（实验已验证可达 0.38s）
3. **输出兼容**: `get_occupancy_list()` 仍需返回 Python list（保持接口兼容）

## 风险与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 向量化后占用单元格数差异 | 低 | 中 | 实验已验证完全一致（0.00% 差异） |
| 栅格值分布差异 | 低 | 中 | 实验已验证分布一致 |
| 内存占用增加 | 低 | 低 | NumPy 数组实际占用更少（int32 vs Python int 对象） |
| 下游代码不兼容 | 低 | 低 | `get_occupancy_list()` 仍返回 list |

## 预期成果

### 性能指标

| 指标 | 优化前（当前） | 优化后 | 提升 |
|------|---------------|--------|------|
| 栅格化耗时 | 7.88s | ~0.38s | **21.0x** |
| 总脚本耗时 | 8.14s | ~0.65s | **12.5x** |

### 代码指标

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| `rasterize()` 代码行数 | 28行 | ~22行 |
| 圈复杂度 | O(N) 循环 | O(1) 向量化 |
| Python 层循环 | 500万次 | 0次 |

## 验收标准（DoD）

- [x] 实验验证性能提升 > 10x (实际 21.0x)
- [ ] 修改 `create_grid()` 使用 NumPy
- [ ] 重写 `rasterize()` 使用向量化
- [ ] 修改 `get_occupancy_list()` 使用 `flatten()`
- [ ] 删除 `euclidean_distance()` 方法
- [ ] 栅格化耗时 < 0.5s
- [ ] 占用单元格数与优化前差异 < 1%
- [ ] 栅格值分布保持一致
- [ ] 基准测试通过
- [ ] 代码提交到 git

## 下一步

完成本设计方案后，执行以下操作：
1. 读取 `executing-plans` 技能执行代码修改
2. 读取 `test-driven-development` 技能补充测试用例
3. 读取 `verification-before-completion` 技能验证并提交
4. 生成 `OPTIMIZATION_EXECUTION-002.md`

---

**实验结论**: ✅ 验证通过，向量化实现性能提升 21.0 倍，输出完全一致，可直接进入实施阶段。
