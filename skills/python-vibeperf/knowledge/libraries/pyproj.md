# PyProj

本文件记录依赖 PyProj API 的性能优化模式。跨库空间计算策略见 [`../domains/spatial-computing.md`](../domains/spatial-computing.md)。

## 缓存 `Transformer` 等昂贵可复用对象

- **通用场景**: 高频坐标转换中反复调用 `pyproj.Transformer.from_crs()`。
- **适用条件**: CRS 组合和构造参数稳定，转换对象可安全复用。
- **不适用/风险**: 缓存键只包含源/目标 CRS 可能不够；`always_xy`、`area_of_interest`、`authority` 等构造参数也可能影响结果。
- **原始模式**:
  ```python
  def transform_point(x, y, from_crs, to_crs):
      transformer = pyproj.Transformer.from_crs(from_crs, to_crs, always_xy=True)
      return transformer.transform(x, y)
  ```
- **推荐模式**:
  ```python
  import threading
  import pyproj

  _transformers = {}
  _lock = threading.Lock()

  def get_transformer(from_crs, to_crs, *, always_xy=True):
      key = (str(from_crs), str(to_crs), always_xy)
      if key not in _transformers:
          with _lock:
              if key not in _transformers:
                  _transformers[key] = pyproj.Transformer.from_crs(
                      from_crs, to_crs, always_xy=always_xy
                  )
      return _transformers[key]
  ```
- **验证方式**: 区分首次初始化和缓存命中耗时；用已知坐标对验证结果一致；长进程需监控缓存数量。

## 批量坐标转换替代逐点转换

- **通用场景**: 循环中逐个调用 `Transformer.transform()`。
- **适用条件**: 坐标可以组织为数组或序列，且转换语义允许批量执行。
- **不适用/风险**: 批量数组过大可能带来内存峰值；需要保留输入顺序和异常处理语义。
- **原始模式**:
  ```python
  xs_out, ys_out = [], []
  for x, y in points:
      x2, y2 = transformer.transform(x, y)
      xs_out.append(x2)
      ys_out.append(y2)
  ```
- **推荐模式**:
  ```python
  points_arr = np.asarray(points)
  xs_out, ys_out = transformer.transform(points_arr[:, 0], points_arr[:, 1])
  ```
- **验证方式**: 对比输出顺序、NaN/无效坐标处理、内存峰值和端到端耗时。

## 对象级转换结果缓存

- **通用场景**: 同一对象的坐标转换结果被多个函数重复读取。
- **适用条件**: 对象坐标在缓存生命周期内不变，或可以在变更时显式失效。
- **不适用/风险**: 对象可变但缓存未失效会返回陈旧坐标；缓存大量对象会增加内存占用。
- **原始模式**:
  ```python
  class Record:
      def projected(self, transformer):
          return transformer.transform(self.x, self.y)
  ```
- **推荐模式**:
  ```python
  class Record:
      def __init__(self, x, y):
          self.x = x
          self.y = y
          self._projected_cache = {}

      def projected(self, crs_key, transformer):
          if crs_key not in self._projected_cache:
              self._projected_cache[crs_key] = transformer.transform(self.x, self.y)
          return self._projected_cache[crs_key]
  ```
- **验证方式**: 测试坐标变更、CRS 变更和缓存失效；记录重复读取次数是否足以抵消缓存复杂度。

## CRS、`always_xy` 与缓存 key 设计

- **通用场景**: 同一系统中存在多个 CRS 组合或不同坐标轴顺序配置。
- **适用条件**: 需要跨模块复用 Transformer，且结果必须稳定可追溯。
- **不适用/风险**: 忽略轴顺序、区域参数或 PROJ 数据版本可能产生看似性能正确但数值错误的结果。
- **推荐模式**: 缓存 key 应覆盖所有影响转换结果的构造参数，并在文档中说明坐标轴约定。
- **验证方式**: 使用固定基准点做单元测试，避免只用性能测试验证坐标转换。

## 缓存失效与线程安全

- **通用场景**: 长进程或并发服务中全局复用 Transformer。
- **适用条件**: Transformer 构造参数有限，缓存可以设置清理策略或随进程生命周期释放。
- **不适用/风险**: 无界缓存可能随用户输入 CRS 增长；并发首次构造可能重复穿透。
- **推荐模式**: 使用锁保护首次写入，并限制可接受 CRS 集合或缓存大小。
- **验证方式**: 并发压测首次访问同一 CRS 组合，确认不会重复构造或产生竞态。
