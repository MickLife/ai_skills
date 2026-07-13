# Markdown 设计图模式

## 混合输出约定

每张图先写 `docs/diagrams/<name>.mmd`。

### SVG 模式

`render-manifest.json` 的 `mode` 为 `svg` 且文件存在时：

```markdown
**设计意图：** 展示系统边界和主要数据交换。

![系统上下文图](diagrams/system-context.svg)

[Mermaid 源码](diagrams/system-context.mmd)

**关键解读：**

- 调用方通过请求进入核心服务。
- 核心服务读取配置并写出结果。
```

### Mermaid 模式

没有 SVG 时，把 `.mmd` 内容复制到围栏中：

````markdown
**设计意图：** 展示系统边界和主要数据交换。

```mermaid
flowchart LR
    Caller["调用方"] -->|"请求"| Core["核心服务"]
    Config["配置"] --> Core
    Core -->|"结果"| Output["输出"]
```

**关键解读：**

- 调用方通过请求进入核心服务。
- 核心服务读取配置并写出结果。
````

不要同时显示 SVG 和 Mermaid 图，避免支持 Mermaid 的阅读器重复渲染。

## 系统上下文

```mermaid
flowchart LR
    User["用户或上游"] -->|"输入"| System["目标系统"]
    Config["配置"] --> System
    System -->|"输出"| Downstream["下游系统"]
```

## 模块关系

```mermaid
flowchart TB
    Interface["接口层"] --> Core["核心处理"]
    Core --> Storage["存储"]
    Core --> NativeLib["C/C++ 核心库"]
```

## 运行时序

```mermaid
sequenceDiagram
    participant Caller as 调用方
    participant Core as 核心模块
    participant Store as 存储
    Caller->>Core: 提交请求
    Core->>Store: 读取数据
    Store-->>Core: 返回数据
    Core-->>Caller: 返回结果
```

## 泳道流程

```mermaid
flowchart TB
    subgraph callerLane [调用方]
        Submit["提交任务"]
        Receive["接收结果"]
    end
    subgraph coreLane [核心模块]
        Validate["校验"]
        Process["处理"]
    end
    Submit --> Validate
    Validate --> Process
    Process --> Receive
```

## 核心类型

```mermaid
classDiagram
    class Pipeline {
        +run()
    }
    class Stage {
        +process()
    }
    Pipeline "1" *-- "many" Stage
```

## 状态变化

```mermaid
stateDiagram-v2
    [*] --> Pending
    Pending --> Running: start
    Running --> Completed: success
    Running --> Failed: error
```

## 数据流

数据流图不表示条件判断和循环，只说明数据来源、加工、存储和去向。

```mermaid
flowchart LR
    Source["外部输入"] -->|"原始数据"| Parse["解析"]
    Parse -->|"结构化数据"| Store[("数据存储")]
    Store -->|"待处理数据"| Transform["转换"]
    Transform -->|"最终结果"| Sink["输出"]
```

## 兼容性检查

- 含空格或标点的显示文字放在双引号中。
- 节点 ID 使用英文、数字和下划线，不使用 `end`。
- 子图写成 `subgraph laneId [显示名称]`。
- 不使用 `<br>`、HTML 实体、`click`、自定义颜色。
- 单个围栏只放一张图。
- 生成 SVG 前先用 `mmdc` 校验；失败则回退 Mermaid 模式并记录原因。
