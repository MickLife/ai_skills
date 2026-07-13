# Python 分析要点

## 包与依赖

- 从 `pyproject.toml`、`setup.py`、`src/` 布局和 `__init__.py` 识别包根。
- 解析绝对/相对 import，记录通配导入、条件导入和函数内导入。
- 区分内部模块与第三方依赖；多仓模式下识别另一仓库提供的顶层包。

## 入口

- `if __name__ == "__main__"`、`__main__.py`。
- `pyproject.toml` 的 scripts。
- Click/Typer/argparse 命令。
- ASGI/WSGI 应用、任务处理器、插件注册。

## 设计事实

- `__all__` 和 `__init__.py` 再导出定义的公共接口。
- dataclass、Pydantic、TypedDict、Protocol、ABC 常代表数据或扩展约定。
- asyncio、线程、多进程、锁、队列代表运行方式和共享状态。
- 上下文管理器、生成器清理、`atexit` 代表资源生命周期。
- 自定义异常、重试、超时代表错误处理策略。

## 风险

- 动态 import、反射、猴子补丁不能被静态分析完整确认。
- 循环依赖可能隐藏在函数内 import。
- `async` 未 `await`、线程承担 CPU 密集工作、共享可变状态需要重点说明。

## Python 调用 C/C++

识别 pybind11、nanobind、cffi、ctypes、Cython、SWIG 或手写 CPython 扩展。记录：

- 哪个 Python 接口进入原生代码。
- 输入输出如何转换。
- 谁负责内存和对象生命周期。
- 是否以及何处释放 GIL。

无法从绑定代码确认的原生行为不要推测，转到 C/C++ 模块继续追踪。
