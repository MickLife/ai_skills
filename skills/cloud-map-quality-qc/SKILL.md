---
name: cloud-map-quality-qc
description: 使用多模态大模型和可插拔检查项执行自动驾驶云端地图质量检查。适用于检查 BEV 渲染图、3D 重建点云、轨迹、覆盖栅格、语义图等云端构图资产，以及叠层、缺图、重影、语义错位、稀疏区域等地图质量问题；当前内置启用叠层检查。
---

# 云端地图质量检查

## 目标

对自动驾驶云端构图区域执行可扩展的地图质量检查。Skill 负责组织输入资产、加载检查项定义、构造多模态模型输入、约束结构化输出、执行坐标投影和结果校验。

当前版本只内置 `layering` 检查项，用于 zero-shot 检测点云叠层问题。未来可以在 `detectors/` 中增加缺图、重影、语义错位、稀疏区域等检查项，而不需要重写主流程。

## 输入模型

使用 `input_manifest` 描述待检查区域、启用的检查项和可用资产。输入必须符合 `resources/input_manifest_schema.json`。

关键概念：

- `region_id`：待检查区域标识。
- `inspection_scope`：坐标系、空间范围和可选时间范围。
- `enabled_checks`：本次启用的检查项，例如 `["layering"]`。
- `assets`：动态资产列表，每个资产包含 `asset_id`、`asset_type`、`uri`、`role` 和可选元数据。
- `runtime_options`：瓦片大小、重叠像素、置信度阈值等运行参数。

不要在主流程中假设固定资产必然存在。每个检查项应通过 `detectors/issue_registry.json` 声明自己的必需资产和可选资产。

## 核心流程

1. 读取 `input_manifest`，校验其符合 `resources/input_manifest_schema.json`。
2. 读取 `detectors/issue_registry.json`，确认 `enabled_checks` 都已注册。
3. 根据每个检查项的 `required_asset_types` 和 `optional_asset_types` 匹配可用资产。
4. 从对象存储拉取或定位本次检查需要的资产。
5. 按资产类型进行瓦片切分、轨迹叠加或元数据准备。
6. 为每个瓦片和检查项构造多模态模型输入：
   - 当前瓦片或局部区域资产。
   - 语义颜色表和渲染说明。
   - 检查项定义文件，例如 `detectors/layering.md`。
   - 输出约束和置信度规则。
7. 要求多模态模型先输出证据，再输出结论。
8. 模型只允许输出像素区域、瓦片引用和观察结果；地图坐标必须由确定性脚本计算。
9. 使用 `scripts/project_observation_to_map.py` 将观察结果转换为地图坐标。
10. 使用 `resources/inspection_result_schema.json` 和 `detectors/issue_registry.json` 校验最终结果。
11. 对低置信度、证据不足或坐标不完整的结果标记人工复核。

## 检查项机制

检查项定义放在 `detectors/` 下：

- `detectors/issue_registry.json`：注册所有支持的质量问题类型。
- `detectors/layering.md`：当前内置的叠层检测定义、误检规则和模型提示要求。

新增检查项时，优先新增 detector 文件和 registry 配置，不要把专项规则写入 `SKILL.md`。

## 模型提示通用要求

调用多模态模型时，应包含以下要求：

- 说明当前启用的检查项及其定义。
- 解释输入资产的类型、坐标关系和渲染方式。
- 如使用 BEV 语义图，必须先解释语义颜色含义。
- 要求模型只检查当前给定瓦片或区域。
- 要求先输出证据，再给出结论。
- 要求给出疑似像素区域、瓦片引用或局部范围。
- 不允许模型编造对象存储路径、地图坐标或不存在的资产。
- 不确定时降低置信度并设置 `needs_human_review=true`。
- 只返回干净 JSON，不要返回 Markdown 或额外解释。

## 输出约束

最终输出必须符合 `resources/inspection_result_schema.json`。

每个 finding 使用通用字段：

- `issue_type`：质量问题类型，例如 `layering`。
- `subtype`：检查项内部子类型，例如 `horizontal_ghosting`。
- `confidence`：置信度，范围 `0-1`。
- `severity`：影响等级。
- `location`：地图坐标、瓦片引用、像素框、多边形或覆盖栅格。
- `evidence`：结构化证据列表。
- `possible_false_positives`：可能误检原因。
- `needs_human_review`：是否需要人工复核。
- `detector_payload`：检查项专属扩展字段。

## 人工复核策略

以下情况必须要求人工复核：

- 检查项证据不足或只基于单一视觉线索。
- 模型明确表示不确定。
- 坐标转换失败或瓦片元数据不完整。
- 异常区域位于复杂道路结构、施工区域或高噪声区域。
- 异常范围较大，可能影响地图发布。

## 附加资源

- 输入 manifest 结构：`resources/input_manifest_schema.json`
- 输出结果结构：`resources/inspection_result_schema.json`
- 资产类型说明：`resources/asset_types.md`
- 坐标契约：`resources/coordinate_contract.md`
- 语义颜色表：`resources/semantic_color_legend.md`
- 渲染规则：`resources/rendering_spec.md`
- 检查项注册表：`detectors/issue_registry.json`
- 叠层检查项：`detectors/layering.md`
- 复核清单：`resources/review_checklist.md`
