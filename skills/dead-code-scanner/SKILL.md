---
name: dead-code-scanner
description: Use when scanning Python projects for dead code, unreachable code, unused functions, unused classes, unused imports, unused variables, commented-out code, "dead code", "unused code", "代码瘦身", or "清理没用的代码".
---

# Dead Code Scanner

## Overview

目标是找出 Python 工程里真正可以删除的死代码，并给出可信理由。工具只负责穷举候选；AI 必须逐条复核，排除反射、装饰器注册、框架路由、入口点、公共 API 等动态使用场景。

## Quick Start

1. 确认扫描范围和排除目录。常见目标是 `src`、包目录或单个模块；常见排除是 `tests`、`migrations`、`.venv`、`build`。
2. 安装依赖：`pip install -r <skill-directory>/requirements.txt`。
3. 查看脚本用法：`python <skill-directory>/scripts/scan.py --help`。
4. 生成候选 JSON：

```bash
python <skill-directory>/scripts/scan.py <target> --min-confidence 80 --exclude "*/tests/*,*/migrations/*" --whitelist whitelist.py --out dead_code_candidates.json
```

5. 读取 `dead_code_candidates.json`，逐条复核源码上下文，产出 `dead_code_report.md`。

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

生成 `dead_code_report.md`，按三类分组。每条包含：

- `file:line`
- `kind`
- `symbol`
- 复核结论
- 理由
- 建议动作

报告开头写一句总览：总候选数、确定可删数、疑似可删数、误报数。

## Whitelist

把误报保留项加入 `whitelist.py`，作为本工程已确认非死代码的清单。下次扫描继续传入 `--whitelist whitelist.py`。如果已有白名单，不要覆盖，追加前先避免重复。

## Constraints

- 不要只凭 vulture 或 ruff 结论删除代码。
- 不要自动删除代码；先给 user 确认清单。
- 复核 `unused_function`、`unused_method`、`unused_class` 前必须读取源码和引用上下文。
- 对有副作用的未使用变量，通常改为保留调用、删除赋值，而不是删除整行。
- 静态分析不能证明 Python 动态代码完全不可达；有测试时建议用 `coverage run -m pytest && coverage report -m` 交叉验证。
