# SciPy

本文件记录依赖 SciPy API 的性能优化模式。空间计算的跨库策略见 [`../domains/spatial-computing.md`](../domains/spatial-computing.md)。

## `cKDTree` / `KDTree` 的版本与选择条件

- **通用场景**: 使用 `scipy.spatial` 做最近邻、半径查询或空间邻域搜索。
- **适用条件**: 数据可以表示为数值坐标数组，查询次数足以摊薄索引构建成本。
- **不适用/风险**: 不同 SciPy 版本中 `KDTree` 与 `cKDTree` 的实现和性能差异可能变化；不能不经验证就承诺固定倍数。
- **原始模式**:
  ```python
  from scipy.spatial import KDTree

  tree = KDTree(points)
  indices = tree.query_ball_point(center, r=radius)
  ```
- **推荐模式**:
  ```python
  from scipy.spatial import cKDTree

  tree = cKDTree(points)
  indices = tree.query_ball_point(center, r=radius)
  ```
- **验证方式**: 在目标 SciPy 版本、坐标维度和数据规模下分别测量构建与查询耗时；确认 API 行为兼容。

## 对不变数据集缓存空间索引

- **通用场景**: 同一批坐标数据被多次查询，但每次调用都重建 `cKDTree`。
- **适用条件**: 数据集在缓存生命周期内不变，且存在稳定缓存键。
- **不适用/风险**: 使用 `id(array)` 作为长期缓存键不够稳健；无界缓存会造成内存泄漏；数据变化后未失效会返回错误结果。
- **原始模式**:
  ```python
  def query_neighbors(points, center, radius):
      tree = cKDTree(points)
      return tree.query_ball_point(center, radius)
  ```
- **推荐模式**:
  ```python
  _tree_cache = {}

  def get_tree(dataset_key, points):
      if dataset_key not in _tree_cache:
          _tree_cache[dataset_key] = cKDTree(points)
      return _tree_cache[dataset_key]
  ```
- **验证方式**: 记录构建成本、查询次数、缓存命中率和内存增长；缓存键应覆盖数据版本、坐标维度、过滤条件等会影响结果的因素。

## 批量邻域查询替代逐点查询

- **通用场景**: 对多个查询点逐个调用 `query_ball_point`。
- **适用条件**: 查询点可以组织为二维数组，且可以接受返回的列表数组结构。
- **不适用/风险**: 返回结果很大时，批量查询可能带来较高内存峰值；仍需根据结果规模分块。
- **原始模式**:
  ```python
  result = []
  for point in query_points:
      result.append(tree.query_ball_point(point, r=radius))
  ```
- **推荐模式**:
  ```python
  result = tree.query_ball_point(query_points, r=radius)
  ```
- **验证方式**: 比较总查询点数、平均邻居数、内存峰值和结果顺序。

## 评估重量级封装与裸数组空间索引的成本

- **通用场景**: 高层库封装的空间算法包含对象构造、格式转换或额外属性维护，profile 显示封装开销明显。
- **适用条件**: 目标操作可以由 NumPy 数组和 SciPy 空间索引表达，且语义差异可被测试覆盖。
- **不适用/风险**: 高层库可能包含边界条件、数值稳定性或领域语义；直接替换可能改变结果。
- **推荐模式**: 先把高层调用拆解为“数据转换、索引构建、查询、后处理”四段测量，再决定是否用 `cKDTree` 等低层 API 替代。
- **验证方式**: 必须用同一输入比较输出一致性、边界行为、耗时和内存；不把某个项目中的库替代经验写成普遍规则。

## 空间索引缓存的失效与内存边界

- **通用场景**: 长进程中缓存多个 `cKDTree` 或其他索引结构。
- **适用条件**: 缓存可以设置容量、TTL、数据版本或显式释放时机。
- **不适用/风险**: 数据集很多或很大时，索引缓存可能成为主要内存来源。
- **推荐模式**: 为缓存键加入数据版本和参数，设置容量上限，并暴露清理接口。
- **验证方式**: 长时间压力测试内存曲线，确认过期数据会释放。
