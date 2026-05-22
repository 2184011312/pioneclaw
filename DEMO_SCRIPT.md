# PioneClaw 领导演示脚本 — 2026年5月9日

## 环境信息
- **后端**: http://localhost:8000 (API前缀: /api)
- **前端**: http://localhost:5173
- **管理员**: admin / admin123
- **测试用户**: testuser / test123

---

## 一、登录 (1分钟)

打开 http://localhost:5173 → 自动跳转登录页 → 输入 admin / admin123 → 进入 Dashboard

**演示要点**: JWT认证、路由守卫、登录态持久化

---

## 二、Dashboard (1分钟)

登录后自动展示 `/dashboard`:

- **统计卡片**: 总调用4次 | Token 2419 | 平均延迟14.6s | 0失败 (100%成功率)
- **模型分布**: deepseek-v4-pro (3次), glm-5 (1次)
- 左侧导航栏展示完整功能菜单:
  - Dashboard / Chat / Agents / Skills / Tasks / Cron / Memories / Wiki / Profile
  - 系统管理: 用户权限 / AI管理 / 扩展管理 / 系统运维

---

## 三、Chat — ReAct流式对话 + 工具调用 ⭐ (3分钟)

**操作**: 点击 Chat → 输入 "搜索一下今天人工智能领域的最新新闻"

**观察SSE流式响应**:
1. `thinking` — AI推理过程 (前端灰色展开)
2. `content` — 逐字流式输出
3. `tool_call: web_search` — 自动调用搜索引擎
4. `tool_result` — 返回 [Bing] 搜索结果（含摘要）
5. `done` — 对话完成

**演示要点**:
- ReAct (Reasoning + Acting) 闭环
- web_search 三级自动降级: Brave API → Bing → DuckDuckGo
- 中文环境Bing正常工作
- SSE 流式传输，用户体验流畅

---

## 四、Agent 管理 (3分钟)

点击侧边栏 **Agents** → 展示7个Agent:

| Agent | 模型 | 用途 |
|-------|------|------|
| **通用执行** (general-purpose) | glm-5.1 | 通用任务 |
| **编程** (coding) | glm-5.1 | 代码编写，max 100轮 |
| **规划分析** (plan) | glm-5.1 | 方案设计 |
| **智能客服助手** (customer_service) 🆕 | glm-5.1 | 客户咨询、情感分析、升级路由 |
| **数据分析师** (data_analyst) 🆕 | deepseek-v4-pro | SQL查询、统计分析 |
| **代码审查员** (code_reviewer) 🆕 | deepseek-v4-pro | 安全漏洞检测、代码审查 |
| **文档撰写助手** (doc_writer) 🆕 | glm-5.1 | API文档、技术文档 |

**演示操作**:
1. 创建Agent: 填写名称、描述、模型、System Prompt、最大轮次
2. 编辑Agent: 修改模型或max_turns
3. 安全演示: 用testuser登录尝试创建 → 403 (无agent:create权限)

---

## 五、Skill 技能管理 (2分钟)

点击 **Skills** → 展示6个技能:

| 技能 | 类型 | 自动激活 |
|------|------|---------|
| file-operations (系统) | system | - |
| web-search (系统) | system | - |
| Web Search Pro 🆕 | search | ✅ |
| Code Generator 🆕 | development | - |
| File Operations 🆕 | system | ✅ |

**演示操作**:
1. 创建技能: YAML frontmatter自动解析 (always, format, dependencies)
2. 依赖检查: 检测CLI工具、环境变量、Python包是否满足
3. 技能配置: Schema驱动的配置管理
4. 热重载: 修改文件后无需重启

---

## 六、Task 任务管理 (2分钟)

点击 **Tasks** → 展示7个任务，不同状态:

| 任务 | 状态 | 优先级 |
|------|------|--------|
| Q2季度销售数据分析报告 | todo | high |
| 用户管理模块代码审查 | **in_progress** | high |
| API接口文档更新 | **done** | medium |
| 客户反馈分类与自动回复模板 | todo | medium |

**演示操作**:
1. 创建任务: 标题、描述、优先级、截止时间、绑定Agent
2. 状态流转: todo → in_progress → done
3. 分配用户: assignee_id
4. 输出数据: done时附带output_data (如审查结果摘要)

---

## 七、Cron 定时任务 (1分钟)

点击 **Cron Jobs** → 展示1个定时任务:

- **test**: `0 9 * * *` (每天9:00) — 自动生成运营日报，调用数据分析Agent

**演示操作**: 创建/编辑/启用/禁用

---

## 八、Runner 分布式节点 ⭐ (2分钟)

点击 **Extension Management** → 展示4个Runner:

| Runner | 位置 | 状态 | 能力 |
|--------|------|------|------|
| **北京数据中心节点** | 10.20.30.1 | **online** | 16核/32GB/NVIDIA T4 |
| **上海边缘节点** | 10.20.30.2 | **online** | 8核/16GB |
| blocked_runner | 10.0.0.1 | approved | - |
| Testuser Runner | 10.0.0.99 | approved | **绑定用户: testuser** |

*两个核心节点有心跳，显示当前任务和执行能力*

**演示操作**:
1. Runner统计: 在线数/总任务数/成功率
2. 用户绑定: testuser_runner 的 approved_by=4 (testuser)
3. 审批流程: pending → approve/reject
4. 中心节点信息: Runner申请接入的HTTP地址

---

## 九、RBAC 权限系统 ⭐ (3分钟)

点击 **User & Permissions**:

### 用户管理 (Users Tab)
| 用户 | 角色 | 权限数 |
|------|------|--------|
| admin | super_admin | * (全部) |
| test1 | org_admin | 21个权限码 |
| yue | user | 14个权限码 |
| testuser | user | 14个权限码 |

### 角色管理 (Roles Tab)

| 角色 | 权限码示例 |
|------|-----------|
| super_admin | `["*"]` |
| org_admin | `dashboard:view, chat:*, agent:*, skill:*, mission:* ...` |
| user | `dashboard:view, chat:view, chat:create, agent:read, agent:execute ...` |

### 实时权限验证 (关键演示!)
1. 新开无痕窗口 → testuser / test123 登录
2. testuser 尝试创建Agent → **403 Forbidden** (缺少agent:create)
3. Admin给user角色添加 `agent:create` 权限 → 保存
4. testuser刷新 → 可以创建Agent了
5. `/auth/me` 返回用户完整权限列表

**演示要点**: 细粒度RBAC, resource:action格式, 通配符支持, 实时生效

---

## 十、AI 模型配置 (1.5分钟)

点击 **AI Management** → 展示4个模型:

| 模型 | Provider | API地址 | 上下文 |
|------|----------|---------|--------|
| **deepseek-v4-pro** (默认) | OpenAI兼容 | api.deepseek.com | 128K |
| glm-5.1 | OpenAI兼容 | ark.cn-beijing.volces.com | **200K** |
| glm-5 | OpenAI兼容 | aicoding.bwits.cn | 128K |
| azure_gpt4 | Azure | api.openai.azure.com | 128K |

**演示操作**: 添加模型 → 测试连通性 (返回success + 延迟)

---

## 十一、Wiki + 分层记忆 (2分钟)

### Wiki 知识库
点击 **Wiki** → 展示6个文档:

| 文档 | 范围 |
|------|------|
| **PioneClaw 快速入门指南** 🆕 | system |
| **系统架构设计说明** 🆕 | system |

点击文档查看Markdown渲染内容，演示搜索功能

### 分层记忆 (Layered Memory)
点击 **Layered Memory** → 3层架构:

- **L0 (短期)**: 对话上下文, 快速衰减
- **L1 (中期)**: 会话摘要, 中等持久
- **L2 (长期)**: 结构化知识, 永久存储

**已存储5条记忆**:
- project_overview: "PioneClaw企业级AI Agent管理平台..."
- tech_decision: "选择FastAPI的原因..."
- user_preference: "用户偏好中文界面..."
- security_policy: "RBAC三级权限模型..."
- deployment_info: "生产环境计划..."

**演示**: recall "PioneClaw" → 返回3层结果及相似度分数

---

## 十二、系统运维 (1.5分钟)

点击 **System Operations**:

- **日志**: 7条API调用记录 (用户/模型/Token/耗时/成功)
- **设置**: 5项系统参数 (system_name, debug_mode, language, timezone)

---

## 演示总时长: 约25分钟

## 故障预案

| 问题 | 解决 |
|------|------|
| 后端无响应 | `cd D:\pioneclaw\backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` |
| 前端白屏 | `cd D:\pioneclaw\frontend && npm run dev` |
| web_search无结果 | Brave key到期，Bing降级自动接管 |
| 登录失败 | 确认SQLite数据库路径未被移动 |

---

## 关键API速查

```
POST   /api/auth/login              # 登录
GET    /api/auth/me                 # 当前用户+权限
GET    /api/dashboard/stats         # 统计
POST   /api/chat/react/stream       # ReAct流式对话
GET    /api/agents                  # Agent列表
POST   /api/agents                  # 创建Agent
GET    /api/skills                  # 技能列表
POST   /api/skills/reload           # 热重载技能
GET    /api/tasks                   # 任务列表
GET    /api/cron                    # 定时任务
GET    /api/runners                 # Runner列表
POST   /api/runners/{id}/heartbeat  # 心跳
GET    /api/runners/stats           # Runner统计
GET    /api/users                   # 用户列表
GET    /api/roles                   # 角色列表
GET    /api/ai-configs              # AI模型配置
POST   /api/ai-configs/test         # 模型测试
GET    /api/wiki/                   # Wiki列表
POST   /api/layered-memory/store    # 分层记忆存储
POST   /api/layered-memory/recall   # 分层记忆召回
GET    /api/logs                    # 系统日志
GET    /api/settings                # 系统设置
```

---

✅ 所有12个模块已通过API验证，每一步均可正常运行。
