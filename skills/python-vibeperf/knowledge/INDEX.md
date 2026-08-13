# Python 性能优化知识库

## 概述

本知识库沉淀可迁移的 Python 性能优化模式，用于支持 `python-vibeperf` 在瓶颈分析和方案设计阶段做出更可靠的判断。真实项目中的优化结果可以反写入本知识库，但必须先抽象出通用模式，并写清适用条件、风险和验证方式。

知识库不是项目复盘目录。具体业务上下文、完整性能数据和一次性实验记录只应作为案例证据，不能被写成普遍最佳实践。

## 使用原则

- **先读模板**: 新增或改写条目前，先阅读 [`_TEMPLATE.md`](_TEMPLATE.md)。
- **先抽象后写入**: 从真实优化结果中提炼可迁移模式，再决定写入分类。
- **先验证再沉淀**: 没有 profile、benchmark 或语义一致性验证的经验，不进入通用知识条目。
- **案例不等于规则**: 性能数字、业务对象、数据集形态只能作为证据和边界，不能作为普遍承诺。
- **默认不读案例正文**: 主流程默认只读取 [`cases/README.md`](cases/README.md) 摘要索引；只有需要核验证据或场景高度相似时，才读取单个案例。

## 知识分类

### 通用原则

适用于跨库、跨领域的性能判断原则，核心价值是决策方法而不是某个 API。

- [核心策略](principles/core-strategies.md)
- [数据结构与基础语法](principles/data-structures.md)
- [内存管理](principles/memory-management.md)
- [并发与 I/O](principles/concurrency-and-io.md)
- [向量化与数值计算](principles/vectorization.md)

### 特定库经验

适用于依赖明确库 API、版本行为或库内部实现的优化模式。

- [NumPy](libraries/numpy.md)
- [SciPy](libraries/scipy.md)
- [Shapely](libraries/shapely.md)
- [PyProj](libraries/pyproj.md)
- [GeoPandas](libraries/geopandas.md)
- [Loguru](libraries/loguru.md)

### 跨库领域模式

适用于横跨多个库或工具的问题域。领域条目应引用库级条目，不复制库 API 细节。

- [空间计算](domains/spatial-computing.md)
- [JSON 序列化](domains/json-serialization.md)

### 案例证据

真实案例用于保存证据、环境和边界。案例默认不进入主流程上下文。

- [案例摘要索引](cases/README.md)

## 分类决策规则

- 写入 `principles/`: 经验不依赖特定第三方库，可以通过多种实现方式落地。
- 写入 `libraries/`: 经验依赖特定库 API、版本行为、输入格式或内部实现。
- 写入 `domains/`: 经验横跨多个库或工具，核心问题是领域数据流、建模方式或组合策略。
- 写入 `cases/`: 经验有参考价值但尚未抽象成通用模式，或包含较多项目上下文、环境数据、业务边界。
- 拒绝写入: 缺少真实性能证据、缺少语义一致性验证、无法说明适用条件，或没有迁移价值。

## 写入准入规则

新增经验必须满足以下条件：

1. 明确通用场景，不使用项目私有对象作为核心描述。
2. 明确适用条件和不适用风险。
3. 给出最小原始模式和推荐模式，避免复制完整业务代码。
4. 说明验证方式，包括性能验证和输出一致性验证。
5. 如果引用真实性能数字，必须写入 `cases/` 或条目的“案例证据”，并标注环境、数据规模和统计方法。

## 新文件维护规则

- 新增、移动或删除任何知识文件时，必须同步更新本索引。
- 新增目录分类时，必须说明该目录与其他目录的边界。
- 新增通用条目时，应优先补充到已有文件；只有当主题边界清晰且会持续增长时，才创建新文件。
- 新增案例时，必须同步更新 [`cases/README.md`](cases/README.md) 摘要索引。
