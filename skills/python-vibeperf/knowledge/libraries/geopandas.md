# GeoPandas

本文件记录依赖 GeoPandas API 的性能优化模式。空间计算的跨库策略见 [`../domains/spatial-computing.md`](../domains/spatial-computing.md)。

## 避免逐行访问 GeoDataFrame：预提取列值

- **通用场景**: 循环中通过 `.loc[]`、`.iloc[]` 或 `.at[]` 按索引逐行访问 GeoDataFrame 的列值，用于计算或判断。
- **适用条件**: 循环次数多（通常 >1000），且被访问的列可以在循环前一次性提取为 dict 或数组。
- **不适用/风险**: 列值本身是可变对象（如 list、dict）且需要在循环中写回时，需要额外处理写回逻辑；GeoDataFrame 在循环中被修改时，预提取的副本不会自动同步。
- **原始模式**:
  ```python
  for idx in gdf.index:
      road_id = gdf.loc[idx, 'road_id']
      geom = gdf.loc[idx, 'geometry']
      process(road_id, geom)
  ```
- **推荐模式**:
  ```python
  road_ids = gdf['road_id'].to_dict()
  geometries = gdf['geometry'].to_dict()
  for idx in gdf.index:
      road_id = road_ids[idx]
      geom = geometries[idx]
      process(road_id, geom)
  ```
- **验证方式**: 对比逐行访问与 dict 查找的耗时；确认预提取期间 GeoDataFrame 不会被并发修改。

## 避免循环内 set_index：预构建查找 dict

- **通用场景**: 循环内对 GeoDataFrame 调用 `.set_index(col).loc[key, field]`，用非默认索引列查找值。
- **适用条件**: 查找键集合已知或可枚举，且查找表在循环期间不变。
- **不适用/风险**: 每次循环 `set_index` 创建新 DataFrame，开销巨大；键不存在时 `.loc[]` 会抛 KeyError，需做 `.index` 判断或 try/except。
- **原始模式**:
  ```python
  for road_id in road_ids:
      park_patch_id = gdf.set_index('id').loc[road_id, 'related_patch_id']
  ```
- **推荐模式**:
  ```python
  id_to_patch = dict(zip(gdf['id'], gdf['related_patch_id']))
  for road_id in road_ids:
      park_patch_id = id_to_patch.get(road_id)
  ```
- **验证方式**: 对比 set_index 开销和 dict 构建开销；确认键唯一性和缺失值处理方式。

## 写回 GeoDataFrame 时优先使用 .at[] 而非 .loc[]

- **通用场景**: 循环中逐行更新 GeoDataFrame 的标量列值。
- **适用条件**: 更新目标是单个标量值，索引已知。
- **不适用/风险**: `.at[]` 只能写入标量，不能写入数组或几何对象；对不存在的索引会抛 KeyError。
- **原始模式**:
  ```python
  for idx in gdf.index:
      gdf.loc[idx, 'status'] = new_value
  ```
- **推荐模式**:
  ```python
  for idx in gdf.index:
      gdf.at[idx, 'status'] = new_value
  ```
- **验证方式**: 对比 `.loc[]` 和 `.at[]` 的逐行写入耗时；确认写入后数据类型和索引不变。
