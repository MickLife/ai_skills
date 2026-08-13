# Shapely

本文件记录依赖 Shapely API 的性能优化模式。空间计算的跨库策略见 [`../domains/spatial-computing.md`](../domains/spatial-computing.md)。

## Shapely 2.x 批量几何构造

- **通用场景**: 从数组批量构造大量点、线或面时，在 Python 循环中逐个创建几何对象。
- **适用条件**: 项目使用 Shapely 2.x，输入坐标可以整理成符合批量构造 API 的数组。
- **不适用/风险**: Shapely 1.x 不支持这些顶层向量化接口；不同几何类型要求的输入形状不同，不能直接套用同一数组形状。
- **原始模式**:
  ```python
  from shapely.geometry import Point

  points = [Point(x, y) for x, y in coords]
  ```
- **推荐模式**:
  ```python
  import shapely

  points = shapely.points(coords)
  ```
- **线和面的最小示例**:
  ```python
  lines = shapely.linestrings(line_coords)      # shape: (N, M, 2)
  rings = shapely.linearrings(ring_coords)      # 每个 ring 首尾闭合
  polygons = shapely.polygons(rings)
  ```
- **验证方式**: 确认 Shapely 版本、输入形状、空几何和非法几何处理方式；对比构造耗时和内存峰值。

## `prepare()` 加速重复空间谓词判断

- **通用场景**: 一个固定复杂几何对象与大量其他几何反复做 `intersects`、`contains`、`covers` 等谓词判断。
- **适用条件**: 复杂几何会被重复使用，且操作属于空间谓词。
- **不适用/风险**: `prepare()` 本身有成本；对只用一次的几何、非谓词操作或频繁变化的几何可能没有收益。
- **原始模式**:
  ```python
  from shapely import intersects

  for geom in geometries:
      if intersects(complex_polygon, geom):
          count += 1
  ```
- **推荐模式**:
  ```python
  from shapely import intersects, prepare

  prepare(complex_polygon)
  for geom in geometries:
      if intersects(complex_polygon, geom):
          count += 1
  ```
- **验证方式**: 分别测量 prepare 成本和重复谓词判断耗时；确认几何对象不会在 prepare 后被替换。

## 区分谓词操作与构造/分析操作

- **通用场景**: 准备使用 `prepare()` 或空间索引加速几何操作。
- **适用条件**: 操作是布尔谓词，如 `intersects`、`contains`、`within`、`covers`、`touches`。
- **不适用/风险**: `intersection`、`union`、`difference`、`buffer`、`simplify`、`centroid` 等构造或分析操作通常不能从 `prepare()` 获得同类收益。
- **推荐模式**: 先判断操作类型，再选择 prepare、STRtree、向量化构造或算法改写。
- **验证方式**: 用目标 Shapely 版本确认 API 行为，不把某个谓词加速结论迁移到所有几何操作。

## STRtree.dwithin 批量距离查询

- **通用场景**: 对大量点或其他几何查询固定距离内的候选，需要同时完成空间过滤和距离判断。
- **适用条件**: Shapely >= 2.0；`STRtree` 支持 `query(geom, distance=...)` 做距离查询；查询几何和距离可以参数化。
- **不适用/风险**: Shapely 1.x 的 STRtree 不支持 `dwithin`；大距离查询会返回大量候选，可能不如精确算法高效；`dwithin` 与 `buffer + intersects` 在极边界处可能有浮点级差异。
- **原始模式**:
  ```python
  from shapely import STRtree
  
  tree = STRtree(geometries)
  for point in points:
      candidates = tree.query(point.buffer(distance))
      for idx in candidates:
          if point.distance(geoms[idx]) < distance:
              handle(idx)
  ```
- **推荐模式**:
  ```python
  for point in points:
      nearby = tree.query(point, distance=15.0)
      for idx in nearby:
          handle(idx)
  ```
- **验证方式**: 对比 buffer+distance 与 STRtree.dwithin 的构建和查询耗时；确认边界精度在业务容差内。
- **案例证据**: [`../cases/20260529-traj-bind-algo.md`](../cases/20260529-traj-bind-algo.md)

## 几何对象批处理的版本条件

- **通用场景**: 在空间计算流水线中混合使用 Shapely、NumPy 和其他几何库。
- **适用条件**: Shapely 版本、GEOS 版本和输入几何有效性都已确认。
- **不适用/风险**: 几何有效性、坐标维度、空值、NaN 和 CRS 语义不属于 Shapely 性能优化能自动解决的问题。
- **推荐模式**: 在性能优化前先建立几何有效性和输出一致性测试，再做批量化或 prepare。
- **验证方式**: 覆盖空几何、非法几何、自交、多部件几何和三维坐标等边界。
