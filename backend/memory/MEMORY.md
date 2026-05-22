2026-05-09|manual|## PioneerClaw 项目概览
PioneerClaw 是一个 AI Agent 平台，采用双轨记忆架构 (Track 1 + Track 2)。

2026-05-09|manual|### 技术栈
- **前端**: Vue 3 + TypeScript + Element Plus + Vite
- **后端**: FastAPI + SQLAlchemy + SQLite
- **AI 能力**: LLM 对话 + Skill 系统 + 工具编排 + 语义检索

2026-05-09|manual|### 双轨记忆架构
**Track 1** (本文) — MEMORY.md 纯文本文件，零外部依赖，行式存储，支持关键词搜索。
**Track 2** — 分层向量记忆 (L0/L1/L2)，基于向量相似度的语义检索，自动摘要和逐层衰减。

2026-05-09|manual|### 核心功能模块
- **Skill 系统**: 用户可创建/编辑/配置技能，支持提交评审，支持 YAML inline 两种格式
- **多 Provider 支持**: OpenAI / Anthropic / DeepSeek 等多家 LLM 提供商
- **权限管理**: 用户级 / 组织级 / 系统级三级权限模型
- **WebSocket 实时推送**: Agent 思考过程实时流式输出
- **工具系统**: 内置 30+ 工具，支持搜索、文件读写、代码执行等
