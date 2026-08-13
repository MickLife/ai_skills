# NumPy

本文件记录依赖 NumPy API 的性能优化模式。跨库向量化原则见 [`../principles/vectorization.md`](../principles/vectorization.md)。

## 避免循环中反复拼接数组

- **通用场景**: 在循环中逐次调用 `np.vstack`、`np.hstack`、`np.concatenate` 或 `np.append` 扩展数组。
- **适用条件**: 每轮生成的数组形状兼容，最终结果可以一次性拼接。
- **不适用/风险**: 如果总结果非常大，列表收集中间数组仍会占用内存；必要时应预分配或分块落盘。
- **原始模式**:
  ```python
  result = np.empty((0, 3))
  for item in items:
      arr = compute(item)
      result = np.vstack([result, arr])
  ```
- **推荐模式**:
  ```python
  arrays = [compute(item) for item in items]
  result = np.concatenate(arrays, axis=0)
  ```
- **验证方式**: 对比拼接次数、总元素量、峰值内存和端到端耗时。

## 用向量化分组聚合替代逐组 Python 循环

- **通用场景**: 需要对不等长分组求和、均值或计数。
- **适用条件**: 数据可以按分组键排序，且聚合函数可以由 NumPy reduce 类 API 表达。
- **不适用/风险**: 分组过少、数据很小或聚合逻辑高度自定义时，排序和边界构造成本可能抵消收益。
- **原始模式**:
  ```python
  result = []
  for group_indices in groups:
      result.append(data[group_indices].mean(axis=0))
  ```
- **推荐模式**:
  ```python
  sorted_data = data[sort_indices]
  boundaries = np.r_[0, np.cumsum(group_sizes)]
  sums = np.add.reduceat(sorted_data, boundaries[:-1], axis=0)
  counts = np.diff(boundaries).reshape(-1, 1)
  result = sums / counts
  ```
- **验证方式**: 覆盖空组、单元素组、dtype 和排序稳定性；比较排序成本与循环成本。

## 预计算数组并复用切片视图

- **通用场景**: 循环中重复调用昂贵转换函数，后续又按位置访问相邻或子集数据。
- **适用条件**: 转换结果在一轮处理内不变，且可以放入连续数组。
- **不适用/风险**: 转换结果依赖外部状态或输入会变化时，预计算会导致陈旧数据。
- **原始模式**:
  ```python
  nearby = [expensive_transform(x) for x in items[i - 10:i + 10]]
  ```
- **推荐模式**:
  ```python
  transformed = np.array([expensive_transform(x) for x in items])
  nearby = transformed[max(0, i - 10):i + 11]
  ```
- **验证方式**: 确认切片是视图还是副本，并衡量预计算成本、内存占用和重复查询次数。

## 用布尔索引或花式索引替代逐个 append

- **通用场景**: 根据条件筛选数组元素或索引后逐个追加到 Python 列表。
- **适用条件**: 条件可以向量化表达，且结果可以一次性取出。
- **不适用/风险**: 花式索引通常会复制数据；对超大结果要关注内存峰值。
- **原始模式**:
  ```python
  result = []
  for i in np.argwhere(condition).ravel():
      result.append(data[i])
  ```
- **推荐模式**:
  ```python
  idx = np.where(condition)[0]
  result = data[idx]
  ```
- **验证方式**: 比较筛选结果顺序、dtype、内存峰值和耗时。

## 避免隐式拷贝与 dtype 膨胀

- **通用场景**: NumPy 代码看似向量化，但热点来自隐式 `copy()`、dtype 自动提升或非连续数组转换。
- **适用条件**: profile 或内存监控显示大量分配，或数组操作频繁跨 dtype/布局边界。
- **不适用/风险**: 为避免拷贝而复用可变视图可能引入别名修改问题。
- **推荐模式**: 明确 dtype、检查 `arr.flags`，在必要时一次性转换布局，避免热路径反复转换。
- **验证方式**: 用内存分析确认分配次数，并补充别名修改相关测试。
