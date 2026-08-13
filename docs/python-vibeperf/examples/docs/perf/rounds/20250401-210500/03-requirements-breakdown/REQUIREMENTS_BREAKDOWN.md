# 性能优化需求拆解文档

## 项目信息

- **优化目标**: `examples/lidar_rasterization.py`
- **基线性能**: 总耗时 9.38s
- **目标性能**: 总耗时 < 1s（10倍+ 提升）
- **优化策略**: 纯 NumPy 向量化
- **拆解时间**: 2025-04-01

## 优化方向识别

基于阶段2的瓶颈分析，识别出 **2 个核心优化方向**：

| 序号 | 优化方向 | 对应瓶颈 | 当前耗时 | 预估优化后 | 预期收益 |
|------|----------|----------|----------|------------|----------|
| **001** | 点生成 NumPy 化 | `generate_lidar_points` | 5.63s | ~0.1s | **50x** |
| **002** | 栅格化向量化 | `rasterize` | 3.73s | ~0.3s | **12x** |

**总体预期收益**: 9.38s → ~0.4s（**23倍性能提升**）

---

## 优化任务详情

### 任务 001: 点生成 NumPy 化

#### 基本信息

| 属性 | 值 |
|------|-----|
| **任务ID** | PERF-001 |
| **任务名称** | 点生成 NumPy 化 |
| **目标函数** | `generate_lidar_points()` |
| **当前耗时** | 5.63s (60% 总耗时) |
| **目标耗时** | < 0.2s |
| **优先级** | **P0 - 最高** |

#### 问题描述

当前实现使用 Python 层循环调用 `random.uniform()` 逐点生成：

```python
def generate_lidar_points(num_points):
    points = []
    for i in range(num_points):              # 500万次循环
        x = random.uniform(-100, 100)
        y = random.uniform(-100, 100)
        z = random.uniform(-10, 10)
        points.append([x, y, z])
    return points
```

**性能瓶颈**:
1. Python 层 500 万次循环开销
2. 1500 万次 `random.uniform()` 函数调用
3. 列表动态扩容多次内存复制

#### 优化方案

**方案**: 使用 `numpy.random.uniform` 批量生成

```python
import numpy as np

def generate_lidar_points(num_points):
    """NumPy 批量生成 LiDAR 点云"""
    points = np.random.uniform(
        low=[-100, -100, -10],
        high=[100, 100, 10],
        size=(num_points, 3)
    )
    return points  # 返回 numpy.ndarray，shape=(5M, 3)
```

**技术优势**:
- NumPy 底层使用 C 实现，避免 Python 层循环
- 预分配连续内存，无动态扩容开销
- 向量化生成，充分利用 SIMD 指令

#### 预期成果

1. **性能指标**
   - 点生成耗时: 5.63s → < 0.2s（**28倍提升**）
   - 保持生成点的分布特征（均匀分布）

2. **代码指标**
   - 函数行数: 8行 → 5行
   - 依赖增加: `numpy`（已允许）

3. **输出一致性**
   - 点的数量: 5,000,000 不变
   - 坐标范围: x,y ∈ [-100,100], z ∈ [-10,10] 不变
   - 分布类型: 均匀分布不变

#### 验收标准（DoD）

- [ ] 使用 NumPy 实现点生成
- [ ] 点生成耗时 < 0.2s
- [ ] 输出形状为 `(5000000, 3)` 的 numpy.ndarray
- [ ] 坐标范围符合预期
- [ ] 基准测试通过（性能对比数据）

#### 依赖关系

- **前置依赖**: 无（可独立实施）
- **后置影响**: 任务 002 的栅格化需要适配 NumPy 数组输入

---

### 任务 002: 栅格化向量化

#### 基本信息

| 属性 | 值 |
|------|-----|
| **任务ID** | PERF-002 |
| **任务名称** | 栅格化向量化 |
| **目标函数** | `LiDARPointCloudRasterizer.rasterize()` |
| **当前耗时** | 3.73s (40% 总耗时) |
| **目标耗时** | < 0.5s |
| **优先级** | **P0 - 最高** |

#### 问题描述

当前实现使用 Python 层循环逐点栅格化：

```python
def rasterize(self, points):
    for point in points:                     # 500万次循环
        x, y, z = point[0], point[1], point[2]
        grid_x = int((x + 100) / self.resolution)
        grid_y = int((y + 100) / self.resolution)

        if 0 <= grid_x < self.width and 0 <= grid_y < self.height:
            world_dist = self.euclidean_distance(x, y, 0, 0)  # sqrt

            if world_dist < 50:
                grid_dist = self.euclidean_distance(...)    # 又一次sqrt

                # 多级阈值判断
                if world_dist < 5:      cell_value = 100
                elif world_dist < 10:   cell_value = 80
                elif world_dist < 20:   cell_value = 60
                elif world_dist < 50:   cell_value = 40
                else:                   cell_value = 20

                self.grid[grid_y][grid_x] = cell_value
```

**性能瓶颈**:
1. Python 层 500 万次循环
2. 每个点最多 2 次 `math.sqrt()` 调用
3. Python 列表嵌套索引访问 `grid[y][x]`
4. 多级条件分支判断

#### 优化方案

**方案**: 使用 NumPy 向量化运算

```python
def rasterize(self, points):
    """NumPy 向量化栅格化"""
    # 坐标转换（向量化）
    grid_x = ((points[:, 0] + 100) / self.resolution).astype(int)
    grid_y = ((points[:, 1] + 100) / self.resolution).astype(int)

    # 边界掩码（向量化）
    valid = (grid_x >= 0) & (grid_x < self.width) & \
            (grid_y >= 0) & (grid_y < self.height)

    # 只处理有效点
    valid_x = points[valid, 0]
    valid_y = points[valid, 1]
    grid_x = grid_x[valid]
    grid_y = grid_y[valid]

    # 距离计算（向量化，避免 sqrt 用平方比较）
    world_dist_sq = valid_x**2 + valid_y**2
    within_range = world_dist_sq < 50**2

    # 应用范围过滤
    valid_x = valid_x[within_range]
    valid_y = valid_y[within_range]
    grid_x = grid_x[within_range]
    grid_y = grid_y[within_range]
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
    self.grid[grid_y, grid_x] = cell_values
```

**技术优势**:
- 无 Python 层循环，全部在 C 层执行
- 使用平方比较避免 `sqrt()` 计算
- NumPy 数组索引赋值高效
- `np.select()` 向量化多级条件

#### 预期成果

1. **性能指标**
   - 栅格化耗时: 3.73s → < 0.5s（**7倍提升**）
   - 与任务 001 配合后总耗时 < 1s

2. **代码指标**
   - 函数复杂度: 降低 Python 层循环嵌套
   - 内存效率: 使用 NumPy 连续内存

3. **输出一致性**
   - 栅格输出形状: (500, 500) 不变
   - 占用单元格数: ~31,739（允许 ±1% 浮动因浮点精度）
   - 栅格值范围: {0, 20, 40, 60, 80, 100} 不变

#### 验收标准（DoD）

- [ ] 使用 NumPy 向量化实现栅格化
- [ ] 栅格化耗时 < 0.5s
- [ ] 避免使用 Python 层 for 循环
- [ ] 占用单元格数与优化前差异 < 1%
- [ ] 基准测试通过（性能对比数据）

#### 依赖关系

- **前置依赖**: 任务 001（输入从 Python list 改为 numpy.ndarray）
- **后置影响**: `get_occupancy_list()` 可能需要适配 NumPy 数组输出

---

## 任务优先级与执行顺序

### 执行顺序

```
┌─────────────────┐     ┌─────────────────┐
│   任务 001      │ ──► │   任务 002      │
│ 点生成 NumPy 化  │     │ 栅格化向量化    │
│   (P0)          │     │   (P0)          │
└─────────────────┘     └─────────────────┘
       │                        │
       ▼                        ▼
 输出 ndarray ──────────────► 输入 ndarray
```

### 优先级说明

| 优先级 | 任务 | 理由 |
|--------|------|------|
| **P0** | 001 - 点生成 NumPy 化 | 耗时占比最高(60%)，实施最简单，ROI最高 |
| **P0** | 002 - 栅格化向量化 | 耗时占比次高(40%)，但依赖 001 完成 |

**注意**: 任务 002 依赖任务 001 的输出格式（从 list 改为 ndarray），必须顺序执行。

---

## 约束条件

### 功能正确性约束

1. **算法输出一致性**
   - 占用单元格数与优化前差异 < 1%（~31,739 ± 300）
   - 栅格值的统计分布保持一致

2. **数据类型约束**
   - 栅格值仍为整数类型
   - 坐标计算精度保持 float64

### 代码质量约束

1. **可读性**
   - 向量化代码需添加详细注释说明
   - 复杂逻辑保留原始算法的注释对照

2. **可维护性**
   - NumPy 操作使用常见函数（避免过度技巧性代码）
   - 保留原始实现作为注释（可选）

### 性能约束

1. **基准指标**
   - 优化后总耗时 < 1s
   - 单个任务优化后耗时达到预期目标

2. **内存使用**
   - 峰值内存增加 < 200MB（NumPy 预分配）

---

## 风险与缓解措施

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 向量化后浮点精度差异导致输出不一致 | 中 | 高 | 优化前后对比验证，设置合理的误差容忍范围 |
| NumPy 数组内存占用过大 | 低 | 中 | 使用 `float32` 替代 `float64` 可选 |
| 栅格化向量化逻辑复杂难以调试 | 中 | 中 | 分步骤实现，每步验证中间结果 |
| 依赖冲突（NumPy 版本） | 低 | 低 | 使用常见 NumPy API，兼容性测试 |

---

## 执行计划

### 阶段 1: 任务 001 - 点生成 NumPy 化

**目标**: 将 `generate_lidar_points` 改为 NumPy 实现

**步骤**:
1. 编写 NumPy 版点生成函数
2. 创建性能对比测试
3. 验证输出一致性（点数、范围、分布）
4. 提交代码

**预期耗时**: ~30分钟

### 阶段 2: 任务 002 - 栅格化向量化

**目标**: 将 `rasterize` 改为 NumPy 向量化实现

**步骤**:
1. 适配 `rasterize` 输入为 NumPy 数组
2. 分步实现向量化逻辑：
   - 坐标转换向量化
   - 边界掩码向量化
   - 距离计算优化（避免 sqrt）
   - 阈值判断向量化
   - 栅格赋值向量化
3. 创建性能对比测试
4. 验证输出一致性（占用单元格数、栅格值分布）
5. 提交代码

**预期耗时**: ~60分钟

---

## 产物清单

- [x] `docs/perf/rounds/20250401-210500/03-requirements-breakdown/REQUIREMENTS_BREAKDOWN.md` - 本文档

**下一阶段产物**（将生成）：
- `04-iterative-optimization/SOLUTION_DESIGN-001.md` - 任务 001 设计方案
- `04-iterative-optimization/OPTIMIZATION_EXECUTION-001.md` - 任务 001 执行记录
- `04-iterative-optimization/SOLUTION_DESIGN-002.md` - 任务 002 设计方案
- `04-iterative-optimization/OPTIMIZATION_EXECUTION-002.md` - 任务 002 执行记录

---

## 总结

本次优化拆解将性能问题分解为 **2 个高优先级任务**：

1. **任务 001** (P0): 点生成 NumPy 化 —— 预期收益 50 倍
2. **任务 002** (P0): 栅格化向量化 —— 预期收益 12 倍

**总体预期**: 总耗时从 9.38s 降至 ~0.4s，实现 **23倍性能提升**。

**下一步行动**: 进入阶段 4，开始任务 001 的迭代优化（实验设计 → 代码修改 → 测试验证 → 提交）。
