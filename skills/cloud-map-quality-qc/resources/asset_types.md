# 资产类型说明

`input_manifest` 使用动态 `assets` 列表描述本次质检可用数据。每个检查项通过 `detectors/issue_registry.json` 声明需要哪些 `asset_type`。

## 通用字段

- `asset_id`：本次检查内唯一的资产标识，供 evidence 和脚本引用。
- `asset_type`：资产类型，决定如何切片、展示和解释。
- `uri`：对象存储 URI 或本地路径。
- `role`：资产在本次检查中的用途，例如 `primary_visual_evidence`、`geometry_reference`、`trajectory_context`。
- `coordinate_frame`：资产所属坐标系。
- `metadata_uri`：像素到地图坐标转换、分辨率、瓦片索引等元数据路径。
- `properties`：项目自定义元数据。

## 当前内置资产类型

| asset_type | 用途 | 常见检查项 |
| --- | --- | --- |
| `bev_semantic_image` | BEV 语义渲染图 | 叠层、重影、语义错位 |
| `bev_height_image` | BEV 高度图 | 叠层、高度错位、缺图 |
| `bev_density_image` | BEV 点密度图 | 缺图、稀疏区域、重影 |
| `bev_intensity_image` | BEV 强度图 | 结构边界和传感器异常辅助判断 |
| `trajectory_overlay` | 已叠加轨迹的可视化图 | 多趟采集错位、叠层 |
| `trajectory` | 原始或重建轨迹数据 | 坐标投影、采集来源关联 |
| `point_cloud` | 3D 重建点云 | 几何复核、局部剖面分析 |
| `coverage_grid` | 期望覆盖栅格 | 缺图、覆盖率异常 |
| `coverage_mask` | 实际覆盖 mask | 缺图、稀疏区域 |
| `tile_metadata` | 瓦片和坐标转换元数据 | 所有需要坐标定位的检查项 |
| `custom` | 项目自定义资产 | 由 detector 自行解释 |

## 扩展规则

- 新增资产类型时，优先更新本文件和 `resources/input_manifest_schema.json`。
- 如果只是某个项目的临时字段，放在资产的 `properties` 中，不要新增顶层字段。
- detector 不应假设某个资产一定存在，必须通过 registry 声明必需和可选资产。
