# 坐标契约

本文件定义模型观察结果、瓦片像素坐标和地图坐标之间的职责边界。

## 基本原则

- 多模态模型只输出可见观察：瓦片 ID、像素框、多边形、线段、局部描述和证据。
- 地图坐标必须由确定性脚本根据可信元数据计算，不能由模型自由生成。
- 如果缺少坐标转换元数据，结果必须保留像素位置并设置 `needs_human_review=true`。

## 支持的位置表达

`location` 可以包含以下一种或多种表达：

- `center_xyz`：地图坐标中心点。
- `extent_xyz`：地图坐标范围。
- `tile_refs`：瓦片引用和像素级位置。
- `polygon`：地图坐标多边形。
- `polyline`：地图坐标线段。
- `coverage_cells`：覆盖栅格单元。

## 瓦片引用

瓦片引用必须包含：

- `tile_id`
- `asset_id`
- `pixel_bbox` 或 `pixel_polygon`

像素坐标默认以图像左上角为原点，x 向右，y 向下。若项目渲染不同，必须在 `rendering_spec.md` 和 tile metadata 中说明。

## 投影脚本职责

`scripts/project_observation_to_map.py` 应负责：

1. 读取模型输出的 tile-local observation。
2. 读取瓦片元数据和图像到地图坐标转换。
3. 计算 `center_xyz`、`extent_xyz`、`polygon` 或 `polyline`。
4. 保留原始 `tile_refs` 作为可追溯证据。
5. 对无法投影的 finding 标记人工复核，不丢弃原始观察。
