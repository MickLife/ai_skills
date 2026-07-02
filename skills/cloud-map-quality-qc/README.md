# cloud-map-quality-qc

这是一个用于自动驾驶云端地图质量检查的 Cursor Skill 雏形。

当前版本面向没有历史 case 库的 zero-shot 检测：通过输入 manifest、资产类型、检查项注册表、BEV 渲染说明和结构化输出约束，引导多模态大模型发现疑似地图质量问题。

当前只内置并启用 `layering` 检查项，用于检测点云叠层。后续可以通过 `detectors/` 扩展缺图、重影、语义错位、稀疏区域等其他质量问题。

## 当前包含

- `SKILL.md`：Skill 主说明和执行流程。
- `resources/input_manifest_schema.json`：动态输入 manifest schema。
- `resources/inspection_result_schema.json`：通用质检结果 schema。
- `resources/asset_types.md`：可用资产类型说明。
- `resources/coordinate_contract.md`：像素、瓦片和地图坐标转换契约。
- `resources/semantic_color_legend.md`：BEV 语义颜色表模板。
- `resources/rendering_spec.md`：BEV 渲染方式说明模板。
- `resources/review_checklist.md`：人工复核清单。
- `detectors/issue_registry.json`：检查项注册表。
- `detectors/layering.md`：点云叠层检查项定义。
- `scripts/`：数据拉取、资产瓦片化、检查输入构造、坐标投影和结果校验脚本占位。

## 下一步接入项

1. 用项目真实语义颜色替换 `resources/semantic_color_legend.md`。
2. 用项目真实 BEV 渲染参数替换 `resources/rendering_spec.md`。
3. 按项目数据组织方式完善 `resources/input_manifest_schema.json` 的资产约束。
4. 在 `scripts/fetch_region_data.py` 中接入对象存储。
5. 在 `scripts/tile_assets.py` 中实现真实瓦片切分和元数据生成。
6. 在 `scripts/project_observation_to_map.py` 中实现像素坐标到地图坐标的确定性转换。
7. 接入多模态模型调用，并使用 `scripts/validate_result.py` 校验输出。
