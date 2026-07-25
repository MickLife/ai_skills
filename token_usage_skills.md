先说明口径：真正同时满足“国内用户、公开 Token 数字、第一手分享”的资料并不多。下面前三篇数字较明确；后两篇是重度工作流分享，但统计口径较弱或未披露准确用量。

## 国内 / 华语内容 5 篇

1. [烧了 250 亿 Token 后，我总结的 Claude Code 使用教程](https://simonaking.com/blog/claude-code-guide/)  
   作者：SimonAKing；团队累计 252 亿 Token。  
   用途：开发 Mana——自然语言生成原生 iPhone App 的平台。  
   重点学习：
   - 多终端并行任务
   - `/clear` 与上下文隔离
   - CLAUDE.md、MCP 的成本控制
   - Opus/Sonnet 分工
   - 如何发现缓存、上下文雪球等 Token 黑洞  
   这是国内最值得精读的工程化经验帖。

2. [揭秘 Claude Code 榜一大哥：对话刘小排](https://www.xiaoyuzhoufm.com/episode/68b404c15faf36865944ac4a)  
   形式：播客访谈；单月约 77 亿 Token。  
   用途：开发 Raphael AI、AnyVoice、Fast3D，并自动执行调研、运营、图片生成等任务。  
   重点学习：
   - 把 Claude Code 当通用 Agent，而不只是编码工具
   - 先写 1000～2000 字需求文档，再与 AI 讨论
   - 用 SOP 把虚拟世界中的工作自动化
   - 后台命令、Subagent、7×24 小时任务
   - 从产品洞察到商业变现的完整链路

3. [20 天、20000 次对话、12 亿 Token：重度用户复盘](https://www.cnblogs.com/jackbwublog/p/19626539)  
   作者：思想者杰克；20 天约 12 亿 Token。  
   用途：完成 AI ChatBot、iOS App、GroAsk 等三个产品。  
   重点学习：
   - Skill 固化重复流程
   - Subagent 实现上下文分治
   - 同时管理 5 个以上 Session
   - TDD、Hooks、MCP 的实际定位
   - 在上下文质量下降前主动开新会话

4. [烧掉十亿 Token 后，我总结的 Coding Agent 高阶玩法](https://mp.weixin.qq.com/s/B4ROBwqvPG0ZOwoFqjQMCA)  
   注意：标题称“十亿”，正文只明确提到“上亿”，数字可信度低于前三篇，但内容质量不错。  
   重点学习：
   - 探索→计划→执行→Review 四阶段工作流
   - 写代码与审查代码必须使用不同上下文
   - 每个任务控制在约 400 行改动
   - Git Worktree 并行生成不同方案
   - 选择对 Agent 友好的“无聊技术栈”
   - TDD 和可机器验证的验收标准

5. [Claude Code：从零搭建你的 AI 工作团队](https://www.bilibili.com/video/BV1eADaBME5z/)  
   作者：Axton；未披露准确 Token，但演示了 12 Agent 的真实工作流。  
   用途：内容审查、事实核查、微信发布、社交运营和 Newsletter。  
   重点学习：
   - 先设计流程，再创建 Agent
   - Skill 与 Agent 的职责边界
   - Claude 负责逻辑、Gemini 负责事实核查
   - 一条命令启动完整内容生产流水线
   - 非编程工作的 Agent 化方法

## 国外内容 5 篇

1. [Peter Steinberger：How to code with AI agents](https://www.youtube.com/watch?v=wKy1_KLcxcs)  
   相关用量：团队账户 30 天 6030 亿 Token、约 100 个 Codex Agent。  
   重点学习：
   - 先与 Agent 讨论方案，再说“开始构建”
   - 同时运行 4～10 个 Agent
   - 直接把 Discord 对话和截图作为需求输入
   - 让 Agent 阅读更多代码、自行回答问题
   - 功能完成后立即让它反思和重构

2. [Scaling Myself：46 天处理 268 亿 Token](https://dev.to/alairjt/scaling-myself-processing-268-billion-tokens-in-46-days-with-claude-code-2c28)  
   数据：1272 个 Session、39 个项目、编辑 4585 个文件。  
   重点学习：
   - 把 AI 作为开发操作系统
   - 高频短 Session，而不是无限延长一个会话
   - 模型分级与机械任务委派
   - 用日志量化项目、文件和 Session 产出
   - 建立持续运行而非临时冲刺的工作方式

3. [14 天、38.84 亿 Token、8857 美元：同时构建 6 个项目](https://dev.to/ethan0506/i-spent-8857-using-claude-code-to-build-6-projects-heres-what-i-learned-2hoj)  
   用途：视频 SaaS、AI 新闻流水线、签证自动化、心理测试 App 等。  
   重点学习：
   - 如何同时推进多个生产项目
   - CLAUDE.md、settings.json 和 Hooks 的投资回报
   - 哪些任务值得使用 Opus
   - 安全加固、支付、事务和容灾如何交给 Agent
   - 如何判断 Token 投入是否真正节省了开发时间

4. [Brett Ridenour：30 天 32.8 亿 Token 审计](https://www.brettridenour.com/blog/i-audited-my-claude-code-token-burn)  
   重点学习：
   - 为什么父级 Orchestrator 可能比所有 Worker 更贵
   - 27 个、100 个 Subagent 的实际成本结构
   - 缓存读取不等于免费
   - 限制并发波次、压缩状态汇报
   - Opus 做架构，Sonnet 做实现，Haiku 做机械任务  
   这是分析“Agent 为什么烧 Token”最深入的一篇。

5. [Jason Hoffman：一个月 10 亿 Token 如何运行一家 AI Startup](https://fullhoffman.com/2026/01/19/on-running-a-startup-of-claude-code-agents-what-you-get-for-a-billion-tokens-a-month/)  
   用途：27 天完成 30.9 万行代码、2726 个测试、165 个页面，以及 App、CMS、支付和八语种网站。  
   重点学习：
   - 同时运行 6～15 个 Claude Code 实例
   - 编码、测试、安全、性能、部署 Agent 分权
   - MEMORY.md、CLAUDE.md、危险区域文档和交接文档
   - 小提交、强测试、独立 Review Agent
   - 如何像管理工程团队一样管理 Agent

如果只先看三篇，我建议按这个顺序：

1. Jason Hoffman：学习完整的 Agent 工程组织方式  
2. SimonAKing：学习上下文和 Token 控制  
3. 刘小排访谈：学习如何把 Agent 扩展到产品与商业全流程