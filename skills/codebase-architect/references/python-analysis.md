# Python 静态分析指南

产出设计文档时如何阅读与建模 Python 代码库。本文是 `methodology.md` 的 Python 专属配套。

## 模块与包模型

- **包（package）**：含 `__init__.py` 的目录（命名空间包可能省略，按 `sys.path` 风格解析，并标注为命名空间包）。
- **模块（module）**：一个 `.py` 文件，点分名 = 相对包根的路径把 `/` 换成 `.`。
- 可能存在多个包根（如 `src/`、顶层、`libs/`）。从 `pyproject.toml`（`[tool.setuptools.packages.find]`）、`setup.py` 的 `packages=` 或扫描顶层 `__init__.py` 推断。
- **多仓模式**下，每个仓库是独立包根；跨仓 import 表现为对另一仓库顶层包的绝对导入（见 `multi-repo.md`）。

## import 分析（`deps_scan.py` 提取内容）

- `import a.b.c` → 指向模块 `a.b.c` 的边。
- `from a.b import c` → 指向 `a.b` 的边；`c` 可能是名字（类/函数）或子模块——通过检查 `a/b/c.py` 或 `a/b/c/__init__.py` 判定。
- `from . import x`、`from ..y import z` → 按当前模块包与相对深度解析。
- `import a.b as c` → 指向 `a.b` 的边，别名 `c`（记录别名用于调用点追踪）。
- 星号导入 `from x import *` → 记为"通配"边；在坑点中标注，因其隐藏依赖面。
- 条件/动态导入（`try: import cext except: import pure`）→ 两个分支都记录，并在设计文档中注明运行时回退。

依赖表中务必引用 import 行（`file:line`）。

## 需识别的入口

- `if __name__ == "__main__":` 块——常为 CLI 入口。
- `pyproject.toml` `[project.scripts]` / `[project.gui-scripts]`——console_scripts 入口。
- `setuptools` `entry_points={"console_scripts": [...]}`。
- ASGI/WSGI 应用：名为 `app`/`application` 的对象，或文档/脚本中 `uvicorn ...:app` 引用。
- `asyncio.run(main())` 模式。
- `click`/`argparse`/`typer` 命令函数——被装饰的函数才是真正入口。

用户给裸符号入口如 `handle_request` 时，用 `find_entry.py`（grep + def/class 感知）定位定义；若多处定义，列出全部并请用户指定（或按目录收窄）。

## 设计文档需捕获的内容

- **公共 API 面**：经 `__all__` 或 `__init__.py` 再导出的内容。区分公开与内部（前导 `_`）。
- **类型**：Protocol、ABC、dataclass、Pydantic 模型、TypedDict——这些往往就是设计契约。
- **并发**：asyncio 事件循环、线程、多进程、executor、锁/队列。标注共享可变状态。
- **资源生命周期**：上下文管理器、`__enter__`/`__exit__`、用于清理的生成器、`atexit`。
- **配置**：环境变量、配置文件、`pydantic-settings`、`dynaconf`。列入配置表。
- **错误处理策略**：异常层级、自定义异常、重试逻辑、何处抛何处捕。
- **测试形态**：pytest fixture、conftest 层级、测试标记——对"扩展点"小节有用。

## 常见 Python 坑点

- 可变默认参数（`def f(x=[])`）。
- 循环中闭包的晚绑定。
- `async` 函数未 `await` 调用（返回协程但不执行）。
- 线程做 CPU 密集任务时的 GIL 假设。
- `import *` 掩盖依赖方向。
- 用函数内局部 import 掩盖的循环导入。
- 切分支后的 `__pycache__`/`.pyc` 陈旧——非设计问题，除非相关否则不记。
- Poetry / pip-tools / uv 锁文件分叉。

## FFI 边界（Python ↔ C/C++）

当 Python 项目嵌入或绑定 C/C++：

- 识别绑定技术：**pybind11**、**nanobind**、**cffi**、**ctypes**、**Cython**、**SWIG**、手写 CPython 扩展（`PyModule_Create`）。
- 把边界作为一等模块文档化：哪些 Python 调用进入 native、谁持有内存/生命周期、何处释放 GIL（pybind11 `py::call_guard<py::gil_scoped_release>`）。
- native 侧与 `cpp-analysis.md` 交叉引用。
