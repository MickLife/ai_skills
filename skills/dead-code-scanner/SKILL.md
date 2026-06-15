---
name: dead-code-scanner
description: Use when scanning Python projects for dead code, unreachable code, unused functions, unused classes, unused imports, unused variables, commented-out code, "dead code", "unused code", "代码瘦身", or "清理没用的代码".
---

# Dead Code Scanner

## Overview

目标是找出 Python 工程里真正可以删除的死代码，并给出可信理由。工具只负责穷举候选；AI 必须逐条复核，排除反射、装饰器注册、框架路由、入口点、公共 API 等动态使用场景。大型仓库必须使用分片和子 agent，主 agent 只做调度、汇总和校验。

## Quick Start

1. 确认扫描范围和排除目录。常见目标是 `src`、包目录或单个模块；常见排除是 `tests`、`migrations`、`.venv`、`build`。
2. 安装依赖：`pip install -r <skill-directory>/requirements.txt`。
3. 查看脚本用法：`python <skill-directory>/scripts/scan.py --help`。
4. 生成 wave 0 候选 JSON：

```bash
python <skill-directory>/scripts/scan.py <target> --min-confidence 80 --exclude "*/tests/*,*/migrations/*" --whitelist whitelist.py --out dead_code_candidates_wave0.json
```

5. 生成复核计划：`python <skill-directory>/scripts/plan_review.py dead_code_candidates_wave0.json --out dead_code_review_plan_wave0.json`。
6. 按 chunk 复核候选，产出 chunk review JSON。
7. 完成前必须运行：`python <skill-directory>/scripts/validate_reviews.py dead_code_candidates_wave0.json <chunk-review-json...> --plan dead_code_review_plan_wave0.json`。
8. 只有校验通过后，才能汇总最终报告并请求 user 确认删除。

## Deletion Waves

死代码删除必须迭代处理，因为存在**连锁删除效应**：第一轮删除的函数、类或模块，可能是另一批旧代码唯一的引用来源。删除前，那些下游代码看起来“仍被使用”；删除后，它们才会在下一轮扫描中变成新的死代码候选。因此，单轮扫描只能发现当前图上的叶子节点，不能一次性证明整条废弃调用链都已经暴露。

每个 wave 表示一次“小批确认删除 + 测试 + 重新扫描”的闭环。删除一批确认可删项后，重新扫描并比较前后结果：

```bash
python <skill-directory>/scripts/scan.py <target> --out dead_code_candidates_wave1.json
python <skill-directory>/scripts/compare_waves.py dead_code_candidates_wave0.json dead_code_candidates_wave1.json --out dead_code_wave0_to_wave1.json
```

- 新出现的候选归为 `new`，必须重新复核，不能自动判定可删。
- 消失的候选归为 `resolved`。
- 仍存在的候选归为 `carried_over`。
- 每个 wave 只删除 user 已确认的低风险项；测试失败时停止本 wave。

## Multi-Agent Review

当候选数超过 30，主 agent 不得独自复核全部候选，必须按 `plan_review.py` 的 chunk 分片。候选数超过 80 时，应并行派发子 agent。

主 agent 职责：

- 运行扫描、分片、校验和 wave 比较脚本。
- 给每个子 agent 分配一个 chunk。
- 汇总 chunk review。
- 校验覆盖率和格式。
- 输出最终报告。

子 agent 职责：

- 只处理指定 `chunk_id` 和候选 ID。
- 必须逐条复核，不能跳过。
- 必须读取必要源码和引用上下文。
- 不得删除代码。
- 不得输出最终报告。
- 不确定时标记 `suspected_deletable`，不能猜。

子 agent prompt 必须包含：

```markdown
You are a dead-code-scanner review subagent.

Scope:
- Chunk ID: <chunk_id>
- Candidate IDs: <ids>
- Allowed paths: <paths>

For every candidate, return:
- candidate_id
- status: confirmed_deletable | suspected_deletable | false_positive
- file
- candidate_line
- symbol
- kind
- removal_range
- removable_lines
- evidence
- risk
- recommended_action

Do not delete code. Do not produce the final report.
```

## Review Checklist

候选命中以下任一情况，通常不是可直接删除的死代码：

- 反射或动态访问：`getattr`、`setattr`、`hasattr`、`globals()`、`locals()`、`__getattr__`、`eval`、`exec`。
- 装饰器注册：FastAPI/Django/Flask 路由、Click/Typer 命令、pytest fixture、信号、事件回调、自定义 registry。
- 字符串引用：配置、模板、路由表、settings、Celery task、ORM、序列化、插件加载按名称引用符号。
- 入口点和协议：`pyproject.toml`/`setup.py` entry points、`__all__`、`__init__.py` 再导出、魔术方法、抽象基类实现、接口方法。
- 公共库 API：仓库内未使用不等于外部用户未使用。
- 测试专用代码：被测试调用仍然是使用；是否删除取决于测试策略，不按死代码处理。

## Classification

每条候选必须归入以下一类，并写明理由：

| 分类 | 含义 | 常见处理 |
| --- | --- | --- |
| 确定可删 | 已读上下文，确认没有动态入口或外部契约风险 | 列入待确认删除清单 |
| 疑似可删 | 静态看无引用，但可能是公共 API、插件点、框架入口或有副作用 | 标注需要人工确认的位置 |
| 误报保留 | 明确命中动态调用、装饰器注册、再导出或外部契约 | 写入/追加到 `whitelist.py` |

确定可删的高置信场景：`return`/`raise` 后不可达语句、无副作用的未使用局部变量、确认不是再导出的未使用导入。

谨慎处理场景：`__init__.py` 中的导入、方法、类、带装饰器的函数、名字出现在配置或字符串中的符号、赋值右侧有函数调用的未使用变量。

## Report Format

最终报告必须固定格式。每条候选必须出现一次，并包含：

- `candidate_id`
- `status`
- `file`
- `candidate_line`
- `kind`
- `symbol`
- `removal_range`
- `removable_lines`
- `evidence`
- `risk`
- `recommended_action`

Summary 必须包含：candidate file、total candidates、reviewed candidates、confirmed deletable、suspected deletable、false positives、total removable lines、review status。

如果 `validate_reviews.py` 失败，报告状态必须是 `INCOMPLETE`，不能向 user 声称复核完成。

## Whitelist

把误报保留项加入 `whitelist.py`，作为本工程已确认非死代码的清单。下次扫描继续传入 `--whitelist whitelist.py`。如果已有白名单，不要覆盖，追加前先避免重复。

## Constraints

- 不要只凭 vulture 或 ruff 结论删除代码。
- 不要自动删除代码；先给 user 确认清单。
- 复核 `unused_function`、`unused_method`、`unused_class` 前必须读取源码和引用上下文。
- 对有副作用的未使用变量，通常改为保留调用、删除赋值，而不是删除整行。
- 候选数超过 30 时必须分片；候选数超过 80 时必须派发子 agent。
- 最终报告前必须运行 `validate_reviews.py`。
- 删除后必须进入下一轮 wave 扫描，并用 `compare_waves.py` 比较变化。
- 静态分析不能证明 Python 动态代码完全不可达；有测试时建议用 `coverage run -m pytest && coverage report -m` 交叉验证。
