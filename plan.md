# PioneClaw 重构计划

> 基于 CircleBot Clone 重构 SurperBot，技术栈：Python 3.11+ / FastAPI / SQLAlchemy 2.0 / Pydantic v2 / Vue 3 + TypeScript

**项目名称**: PioneClaw
**项目目录**: `D:/pioneclaw/`

---

## 一、项目概述

### 1.1 重构目标

将 SurperBot 从 Node.js (Express + Sequelize) 重构为 Python (FastAPI + SQLAlchemy)，同时整合 CircleBot Clone 的成熟模块。

### 1.2 技术栈对比

| 层级   | SurperBot (原)                | 重构目标                          | 来源          |
| ---- | ---------------------------- | ----------------------------- | ----------- |
| 后端框架 | Express.js                   | FastAPI                       | CircleBot ✅ |
| ORM  | Sequelize                    | SQLAlchemy 2.0                | CircleBot ✅ |
| 数据验证 | express-validator            | Pydantic v2                   | CircleBot ✅ |
| AI调用 | 自定义                          | LiteLLM                       | CircleBot ✅ |
| 认证   | JWT + bcryptjs               | JWT + passlib                 | CircleBot ✅ |
| 前端框架 | Vue 3 + JS                   | Vue 3 + TypeScript            | CircleBot ✅ |
| 状态管理 | Pinia (JS)                   | Pinia (TS)                    | CircleBot ✅ |
| UI框架 | Element Plus                 | Element Plus                  | CircleBot ✅ |
| 数据库  | MySQL + MongoDB + Redis + ES | SQLite (开发) / PostgreSQL (生产) | CircleBot ✅ |

### 1.3 复用策略

| 类型      | 模块                                                              | 来源        |
| ------- | --------------------------------------------------------------- | --------- |
| ✅ 直接复用  | Agent、Skill、Runner、Memory、Workflow、Provider、Tools、Channels、Cron | CircleBot |
| 🔄 整合扩展 | User、Role、Task、Knowledge、SystemSetting                          | 两者整合      |
| 🆕 新增开发 | Organization、Permission、Wiki                                    | SurperBot |

---

## 二、项目结构

```
D:/pioneclaw/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      # FastAPI 入口
│   │   │
│   │   ├── api/                         # API 路由层
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                  # 依赖注入
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py            # 路由汇总
│   │   │       ├── auth.py              # 认证 API
│   │   │       ├── users.py             # 用户 API
│   │   │       ├── roles.py             # 角色 API
│   │   │       ├── permissions.py       # 权限 API (🆕)
│   │   │       ├── organizations.py     # 组织 API (🆕)
│   │   │       ├── tasks.py             # 任务 API (🔄 扩展)
│   │   │       ├── wiki.py              # Wiki API (🆕)
│   │   │       ├── agents.py            # Agent API (✅ 复用)
│   │   │       ├── agent_execute.py     # Agent 执行 (✅ 复用)
│   │   │       ├── agent_memories.py    # Agent 记忆 (✅ 复用)
│   │   │       ├── skills.py            # Skill API (✅ 复用)
│   │   │       ├── memories.py          # Memory API (✅ 复用)
│   │   │       ├── knowledge.py         # Knowledge API (✅ 复用)
│   │   │       ├── runners.py           # Runner API (✅ 复用)
│   │   │       ├── cron.py              # Cron API (✅ 复用)
│   │   │       ├── channels.py          # Channel API (✅ 复用)
│   │   │       ├── providers.py         # Provider API (✅ 复用)
│   │   │       ├── ai_configs.py        # AI 配置 API (✅ 复用)
│   │   │       ├── chat.py              # Chat API (✅ 复用)
│   │   │       ├── workflow.py          # Workflow API (✅ 复用)
│   │   │       ├── dashboard.py         # Dashboard API (✅ 复用)
│   │   │       ├── logs.py              # Logs API (✅ 复用)
│   │   │       ├── settings.py          # Settings API (✅ 复用)
│   │   │       └── websocket.py         # WebSocket (✅ 复用)
│   │   │
│   │   ├── core/                        # 核心配置
│   │   │   ├── __init__.py
│   │   │   ├── config.py                # Pydantic Settings (✅ 复用)
│   │   │   ├── security.py              # JWT + 密码哈希 (✅ 复用)
│   │   │   ├── permissions.py           # 权限系统 (🔄 扩展)
│   │   │   ├── exceptions.py            # 异常定义 (✅ 复用)
│   │   │   └── database.py              # 数据库连接 (✅ 复用)
│   │   │
│   │   ├── models/                      # SQLAlchemy 模型
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # 基础模型类 (✅ 复用)
│   │   │   ├── user.py                  # 用户模型 (🔄 扩展)
│   │   │   ├── role.py                  # 角色模型 (🔄 扩展)
│   │   │   ├── permission.py            # 权限模型 (🆕)
│   │   │   ├── organization.py          # 组织模型 (🆕)
│   │   │   ├── task.py                  # 任务模型 (🔄 扩展)
│   │   │   ├── wiki.py                  # Wiki 模型 (🆕)
│   │   │   ├── agent.py                 # Agent 模型 (✅ 复用)
│   │   │   ├── skill.py                 # Skill 模型 (✅ 复用)
│   │   │   ├── memory.py                # Memory 模型 (✅ 复用)
│   │   │   ├── runner.py                # Runner 模型 (✅ 复用)
│   │   │   ├── cron_job.py              # Cron 模型 (✅ 复用)
│   │   │   ├── knowledge.py             # Knowledge 模型 (✅ 复用)
│   │   │   ├── ai_config.py             # AI 配置模型 (✅ 复用)
│   │   │   └── system_setting.py        # 系统设置模型 (✅ 复用)
│   │   │
│   │   ├── schemas/                     # Pydantic 模型
│   │   │   ├── __init__.py
│   │   │   ├── common.py                # 通用响应 (✅ 复用)
│   │   │   ├── auth.py                  # 认证 Schema (🔄 扩展)
│   │   │   ├── user.py                  # 用户 Schema (🔄 扩展)
│   │   │   ├── role.py                  # 角色 Schema (🔄 扩展)
│   │   │   ├── permission.py            # 权限 Schema (🆕)
│   │   │   ├── organization.py          # 组织 Schema (🆕)
│   │   │   ├── task.py                  # 任务 Schema (🔄 扩展)
│   │   │   ├── wiki.py                  # Wiki Schema (🆕)
│   │   │   ├── agent.py                 # Agent Schema (✅ 复用)
│   │   │   ├── skill.py                 # Skill Schema (✅ 复用)
│   │   │   ├── memory.py                # Memory Schema (✅ 复用)
│   │   │   └── ...                      # 其他 Schema (✅ 复用)
│   │   │
│   │   ├── modules/                     # 业务模块 (✅ 全部复用)
│   │   │   ├── agent/                   # Agent 核心
│   │   │   │   ├── loop.py              # ReAct 推理循环
│   │   │   │   ├── workflow.py          # 工作流引擎
│   │   │   │   ├── subagent.py          # 子 Agent 管理
│   │   │   │   ├── analyzer.py          # 消息分析
│   │   │   │   ├── compactor.py         # 上下文压缩
│   │   │   │   ├── context.py           # 上下文构建
│   │   │   │   ├── memory.py            # 记忆存储
│   │   │   │   ├── heartbeat.py         # 心跳服务
│   │   │   │   ├── personalities.py     # 性格预设
│   │   │   │   ├── prompts.py           # 提示词模板
│   │   │   │   ├── skills.py            # 技能加载器
│   │   │   │   ├── skills_config.py     # 技能配置
│   │   │   │   ├── skills_schema.py     # 技能 Schema
│   │   │   │   ├── task_manager.py      # 任务管理
│   │   │   │   ├── task_board.py        # 任务看板
│   │   │   │   ├── vector_store.py      # 向量存储
│   │   │   │   ├── experience.py        # 经验学习
│   │   │   │   └── research.py          # 研究会话
│   │   │   │
│   │   │   ├── providers/               # AI Provider
│   │   │   │   ├── base.py
│   │   │   │   ├── factory.py
│   │   │   │   ├── registry.py
│   │   │   │   ├── runtime.py
│   │   │   │   ├── openai_provider.py
│   │   │   │   └── anthropic_provider.py
│   │   │   │
│   │   │   ├── channels/                # 渠道适配器
│   │   │   │   ├── base.py
│   │   │   │   ├── manager.py
│   │   │   │   ├── telegram.py
│   │   │   │   └── feishu.py
│   │   │   │
│   │   │   └── tools/                   # 工具系统
│   │   │       ├── base.py
│   │   │       ├── registry.py
│   │   │       ├── builtin.py
│   │   │       └── web.py
│   │   │
│   │   └── utils/                       # 工具函数
│   │       ├── __init__.py
│   │       ├── logger.py                # 日志工具 (✅ 复用)
│   │       └── helpers.py               # 辅助函数 (✅ 复用)
│   │
│   ├── alembic/                         # 数据库迁移
│   │   ├── versions/
│   │   ├── env.py
│   │   └── alembic.ini
│   │
│   ├── tests/                           # 测试
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_users.py
│   │   └── ...
│   │
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── .env.example
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── main.ts                      # 入口文件
│   │   ├── App.vue                      # 根组件
│   │   │
│   │   ├── api/                         # API 调用
│   │   │   ├── index.ts                 # Axios 实例
│   │   │   ├── auth.ts
│   │   │   ├── user.ts
│   │   │   ├── role.ts
│   │   │   ├── permission.ts            # (🆕)
│   │   │   ├── organization.ts          # (🆕)
│   │   │   ├── task.ts
│   │   │   ├── wiki.ts                  # (🆕)
│   │   │   └── ...
│   │   │
│   │   ├── stores/                      # Pinia 状态
│   │   │   ├── user.ts
│   │   │   ├── app.ts
│   │   │   ├── permission.ts            # (🆕)
│   │   │   └── ...
│   │   │
│   │   ├── router/
│   │   │   └── index.ts
│   │   │
│   │   ├── views/                       # 页面组件
│   │   │   ├── Login.vue
│   │   │   ├── Dashboard.vue
│   │   │   ├── Organizations.vue        # (🆕)
│   │   │   ├── Permissions.vue          # (🆕)
│   │   │   ├── Wiki.vue                 # (🆕)
│   │   │   ├── Tasks.vue                # (🔄 扩展)
│   │   │   ├── Agents.vue
│   │   │   ├── Skills.vue
│   │   │   ├── Memories.vue
│   │   │   ├── Runners.vue
│   │   │   ├── Cron.vue
│   │   │   ├── Channels.vue
│   │   │   ├── AIConfigs.vue
│   │   │   ├── Knowledge.vue
│   │   │   ├── Users.vue
│   │   │   ├── Roles.vue
│   │   │   ├── Logs.vue
│   │   │   ├── Monitor.vue
│   │   │   ├── Settings.vue
│   │   │   ├── Profile.vue
│   │   │   └── Chat.vue
│   │   │
│   │   ├── components/                  # 通用组件
│   │   │   ├── OrgTree.vue              # (🆕) 组织树组件
│   │   │   ├── PermissionTree.vue       # (🆕) 权限树组件
│   │   │   ├── WikiEditor.vue           # (🆕) Wiki 编辑器
│   │   │   └── ...
│   │   │
│   │   ├── layouts/
│   │   │   └── MainLayout.vue
│   │   │
│   │   ├── types/                       # TypeScript 类型
│   │   │   ├── user.d.ts
│   │   │   ├── organization.d.ts        # (🆕)
│   │   │   ├── permission.d.ts          # (🆕)
│   │   │   ├── task.d.ts
│   │   │   ├── wiki.d.ts                # (🆕)
│   │   │   └── ...
│   │   │
│   │   ├── composables/                 # 组合式函数
│   │   │   ├── usePermission.ts
│   │   │   └── ...
│   │   │
│   │   ├── styles/
│   │   │   └── main.scss
│   │   │
│   │   └── utils/
│   │       └── permission.ts            # (🆕) 权限工具函数
│   │
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── docs/
│   ├── API.md
│   ├── DEPLOY.md
│   └── MIGRATION.md
│
├── docker-compose.yml
├── docker-compose.dev.yml
└── README.md
```

**图例说明：**

- ✅ 复用：直接从 CircleBot Clone 复制
- 🔄 扩展：基于 CircleBot 扩展
- 🆕 新增：全新开发

---

## 三、功能模块对比

### 3.1 模块复用矩阵

| 功能模块          | SurperBot  | CircleBot  | 策略    | 优先级 |
| ------------- | ---------- | ---------- | ----- | --- |
| **用户认证**      | JWT + RBAC | JWT + Role | 🔄 整合 | P0  |
| **组织管理**      | ✅ 树形结构     | ❌          | 🆕 新增 | P0  |
| **权限管理**      | ✅ 四级RBAC   | ✅ 基础Role   | 🔄 扩展 | P0  |
| **用户管理**      | ✅          | ✅          | 🔄 整合 | P0  |
| **角色管理**      | ✅          | ✅          | 🔄 整合 | P0  |
| **任务管理**      | ✅ 完整       | ✅ 基础       | 🔄 扩展 | P1  |
| **Wiki 知识库**  | ✅          | ✅ 基础       | 🔄 整合 | P1  |
| **智能记忆**      | ✅          | ✅          | ✅ 复用  | P1  |
| **Agent 管理**  | ✅ 基础       | ✅ 完整       | ✅ 复用  | P1  |
| **Skill 管理**  | ✅ 基础       | ✅ 完整       | ✅ 复用  | P1  |
| **Runner 管理** | ✅          | ✅          | ✅ 复用  | P1  |
| **工作流引擎**     | ❌          | ✅          | ✅ 复用  | P2  |
| **ReAct 推理**  | ❌          | ✅          | ✅ 复用  | P2  |
| **渠道管理**      | ❌          | ✅          | ✅ 复用  | P2  |
| **Provider**  | ❌          | ✅          | ✅ 复用  | P2  |
| **工具系统**      | ❌          | ✅          | ✅ 复用  | P2  |
| **定时任务**      | ❌          | ✅          | ✅ 复用  | P2  |
| **向量存储**      | ❌          | ✅          | ✅ 复用  | P2  |
| **经验学习**      | ❌          | ✅          | ✅ 复用  | P2  |
| **数据监控**      | ✅          | ✅          | 🔄 整合 | P2  |
| **系统设置**      | ✅          | ✅          | 🔄 整合 | P2  |

### 3.2 API 端点清单

#### 认证模块 `/api/auth` (✅ 复用 + 🔄 扩展)

| 方法   | 端点                        | 描述         | 来源    |
| ---- | ------------------------- | ---------- | ----- |
| POST | `/register`               | 用户注册（创建组织） | 🔄 扩展 |
| POST | `/login`                  | 用户登录       | ✅ 复用  |
| POST | `/refresh-token`          | 刷新令牌       | 🆕 新增 |
| POST | `/logout`                 | 登出         | ✅ 复用  |
| GET  | `/me`                     | 当前用户信息     | ✅ 复用  |
| POST | `/change-password`        | 修改密码       | ✅ 复用  |
| POST | `/password-reset/request` | 请求重置密码     | 🆕 新增 |
| POST | `/password-reset/confirm` | 确认重置密码     | 🆕 新增 |

#### 组织管理 `/api/organizations` (🆕 新增)

| 方法     | 端点           | 描述      |
| ------ | ------------ | ------- |
| GET    | `/`          | 组织列表    |
| GET    | `/tree`      | 组织树     |
| POST   | `/`          | 创建组织    |
| GET    | `/:id`       | 组织详情    |
| PUT    | `/:id`       | 更新组织    |
| DELETE | `/:id`       | 删除组织    |
| GET    | `/:id/users` | 组织用户    |
| POST   | `/:id/users` | 添加用户到组织 |

#### 权限管理 `/api/permissions` (🆕 新增)

| 方法     | 端点      | 描述   |
| ------ | ------- | ---- |
| GET    | `/`     | 权限列表 |
| GET    | `/tree` | 权限树  |
| POST   | `/`     | 创建权限 |
| PUT    | `/:id`  | 更新权限 |
| DELETE | `/:id`  | 删除权限 |

#### 任务管理 `/api/tasks` (✅ 复用 + 🔄 扩展)

| 方法     | 端点                      | 描述    | 来源    |
| ------ | ----------------------- | ----- | ----- |
| GET    | `/`                     | 任务列表  | ✅ 复用  |
| GET    | `/stats`                | 任务统计  | 🆕 新增 |
| GET    | `/analytics`            | 任务分析  | 🆕 新增 |
| POST   | `/`                     | 创建任务  | ✅ 复用  |
| GET    | `/:id`                  | 任务详情  | ✅ 复用  |
| PUT    | `/:id`                  | 更新任务  | ✅ 复用  |
| DELETE | `/:id`                  | 删除任务  | ✅ 复用  |
| POST   | `/:id/subtasks`         | 创建子任务 | 🆕 新增 |
| GET    | `/:id/comments`         | 获取评论  | 🆕 新增 |
| POST   | `/:id/comments`         | 添加评论  | 🆕 新增 |
| GET    | `/:id/attachments`      | 获取附件  | 🆕 新增 |
| POST   | `/:id/attachments`      | 上传附件  | 🆕 新增 |
| DELETE | `/:id/attachments/:aid` | 删除附件  | 🆕 新增 |
| POST   | `/batch/assign`         | 批量分配  | 🆕 新增 |
| POST   | `/batch/update`         | 批量更新  | 🆕 新增 |

#### Wiki 管理 `/api/wiki` (🆕 新增)

| 方法     | 端点                      | 描述          |
| ------ | ----------------------- | ----------- |
| GET    | `/`                     | Wiki 列表     |
| GET    | `/search`               | 搜索 Wiki     |
| POST   | `/`                     | 创建 Wiki     |
| POST   | `/import`               | 导入 Markdown |
| GET    | `/:id`                  | Wiki 详情     |
| PUT    | `/:id`                  | 更新 Wiki     |
| DELETE | `/:id`                  | 删除 Wiki     |
| GET    | `/:id/history`          | 版本历史        |
| POST   | `/:id/restore/:version` | 恢复版本        |

#### 其他模块 (✅ 全部复用)

| 模块                                 | 端点前缀                  | API 数量 |
| ---------------------------------- | --------------------- | ------ |
| 用户管理                               | `/api/users`          | 6      |
| 角色管理                               | `/api/roles`          | 6      |
| Agent 管理                           | `/api/agents`         | 8      |
| Agent 执行                           | `/api/agent-execute`  | 3      |
| Chat                               | `/api/chat`           | 2      |
| Skill                              | `/api/skills`         | 8      |
| Memory | `/api/memories`       | 6      |
| Agent Memory                       | `/api/agent-memories` | 6      |
| Knowledge                          | `/api/knowledge`      | 6      |
| Runner                             | `/api/runners`        | 6      |
| Cron                               | `/api/cron`           | 5      |
| Channel                            | `/api/channels`       | 5      |
| Provider                           | `/api/providers`      | 4      |
| AI Config                          | `/api/ai-configs`     | 5      |
| Workflow                           | `/api/workflow`       | 2      |
| Dashboard                          | `/api/dashboard`      | 3      |
| Logs                               | `/api/logs`           | 2      |
| Settings                           | `/api/settings`       | 4      |
| WebSocket                          | `/api/ws`             | 1      |

---

## 四、数据模型设计

### 4.1 新增模型

#### Organization (组织)

```python
class Organization(Base):
    """组织模型 - 树形结构"""
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)

    # 树形结构
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id"))
    level: Mapped[int] = mapped_column(Integer, default=1)
    path: Mapped[str] = mapped_column(String(500))  # 例: "1/2/3"

    # 管理信息
    manager_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(20), default="department")  # company/department/team
    status: Mapped[str] = mapped_column(String(20), default="active")

    # 元数据
    metadata: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    parent: Mapped["Organization | None"] = relationship(back_populates="children", remote_side=[id])
    children: Mapped[list["Organization"]] = relationship(back_populates="parent", cascade="all, delete-orphan")
    users: Mapped[list["User"]] = relationship(back_populates="organization")
    manager: Mapped["User | None"] = relationship(foreign_keys=[manager_id])
```

#### Permission (权限)

```python
class Permission(Base):
    """权限模型 - 树形结构"""
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # 例: task:create
    description: Mapped[str | None] = mapped_column(Text)

    # 权限分类
    type: Mapped[str] = mapped_column(String(20))  # menu/system/app/api
    resource: Mapped[str] = mapped_column(String(50))  # task/user/role
    action: Mapped[str] = mapped_column(String(20))  # create/read/update/delete

    # 树形结构
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("permissions.id"))
    menu_id: Mapped[str | None] = mapped_column(String(36))  # 关联菜单

    # 状态
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # 关系
    parent: Mapped["Permission | None"] = relationship(back_populates="children", remote_side=[id])
    children: Mapped[list["Permission"]] = relationship(back_populates="parent")
```

#### Wiki (知识库)

```python
class Wiki(Base):
    """Wiki 文档"""
    __tablename__ = "wikis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    path: Mapped[str] = mapped_column(String(500), unique=True, index=True)  # 唯一路径，如 /docs/api/auth

    # 分类
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("wikis.id"))
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    # 所有权
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))

    # 版本控制
    version: Mapped[int] = mapped_column(Integer, default=1)

    # 状态
    status: Mapped[str] = mapped_column(String(20), default="published")  # draft/published/archived

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    parent: Mapped["Wiki | None"] = relationship(back_populates="children", remote_side=[id])
    children: Mapped[list["Wiki"]] = relationship(back_populates="parent")
    history: Mapped[list["WikiVersion"]] = relationship(back_populates="wiki", cascade="all, delete-orphan")
    author: Mapped["User"] = relationship(foreign_keys=[created_by])
    organization: Mapped["Organization"] = relationship()


class WikiVersion(Base):
    """Wiki 版本历史"""
    __tablename__ = "wiki_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wiki_id: Mapped[str] = mapped_column(ForeignKey("wikis.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    change_summary: Mapped[str | None] = mapped_column(String(500))  # 变更摘要
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # 关系
    wiki: Mapped["Wiki"] = relationship(back_populates="history")
    author: Mapped["User"] = relationship()
```

### 4.2 扩展模型

#### User (用户 - 扩展)

```python
class User(Base):
    """用户模型 - 扩展自 CircleBot"""
    __tablename__ = "users"

    # CircleBot 原有字段
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(100))
    avatar: Mapped[str | None] = mapped_column(String(500))
    role: Mapped[str] = mapped_column(String(20), default="user")  # user/org_admin/super_admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 🆕 新增字段
    organization_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id"), index=True)
    department: Mapped[str | None] = mapped_column(String(100))
    position: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(20))

    # 权限扩展
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_org_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # 登录安全
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_login_ip: Mapped[str | None] = mapped_column(String(45))
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    organization: Mapped["Organization | None"] = relationship(back_populates="users")
    roles: Mapped[list["Role"]] = relationship(secondary="user_roles", back_populates="users")
```

#### Role (角色 - 扩展)

```python
class Role(Base):
    """角色模型 - 扩展自 CircleBot"""
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)

    # CircleBot 原有
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)

    # 🆕 新增字段
    type: Mapped[str] = mapped_column(String(20), default="custom")  # system/custom
    level: Mapped[int] = mapped_column(Integer, default=0)  # 0-3 权限等级
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    organization_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    users: Mapped[list["User"]] = relationship(secondary="user_roles", back_populates="roles")
    organization: Mapped["Organization | None"] = relationship()
```

#### Task (任务 - 扩展)

```python
class Task(Base):
    """任务模型 - 扩展自 CircleBot"""
    __tablename__ = "tasks"

    # CircleBot 原有字段
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    assignee_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))

    # 🆕 新增字段
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"))  # 子任务
    template_id: Mapped[str | None] = mapped_column(String(36))  # 任务模板
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)

    # 时间管理
    start_time: Mapped[datetime | None] = mapped_column(DateTime)
    end_time: Mapped[datetime | None] = mapped_column(DateTime)
    estimated_hours: Mapped[float | None] = mapped_column(Float)
    actual_hours: Mapped[float | None] = mapped_column(Float)

    # 进度跟踪
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100

    # 协作
    collaborators: Mapped[list[str]] = mapped_column(JSON, default=list)  # 协作人ID列表
    watchers: Mapped[list[str]] = mapped_column(JSON, default=list)  # 关注人ID列表

    # 附件和标签
    attachments: Mapped[list[dict]] = mapped_column(JSON, default=list)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    # 元数据
    metadata: Mapped[dict | None] = mapped_column(JSON)

    # 完成信息
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    parent: Mapped["Task | None"] = relationship(back_populates="subtasks", remote_side=[id])
    subtasks: Mapped[list["Task"]] = relationship(back_populates="parent", cascade="all, delete-orphan")
    comments: Mapped[list["TaskComment"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    assignee: Mapped["User | None"] = relationship(foreign_keys=[assignee_id])
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])
    organization: Mapped["Organization"] = relationship()


class TaskComment(Base):
    """任务评论"""
    __tablename__ = "task_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("task_comments.id"))  # 回复
    mentions: Mapped[list[str]] = mapped_column(JSON, default=list)  # @用户列表

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    task: Mapped["Task"] = relationship(back_populates="comments")
    user: Mapped["User"] = relationship()
    parent: Mapped["TaskComment | None"] = relationship(back_populates="replies", remote_side=[id])
    replies: Mapped[list["TaskComment"]] = relationship(back_populates="parent")
```

---

## 五、实施阶段

### 阶段一：项目初始化与基础架构 (2天) ✅ 已完成

#### 任务清单

| ID  | 任务                  | 说明                                       | 预计时间 | 状态 |
| --- | ------------------- | ---------------------------------------- | ---- | ---- |
| 1.1 | 创建项目目录结构            | 按 2.1 节结构创建                              | 0.5h | ✅ |
| 1.2 | 复制 CircleBot 后端核心代码 | `core/`、`modules/`、`models/base.py`      | 1h   | ✅ |
| 1.3 | 复制 CircleBot 前端代码   | `frontend/` 整个目录                         | 0.5h | ✅ |
| 1.4 | 配置数据库连接             | SQLite (开发) / PostgreSQL (生产)            | 1h   | ✅ |
| 1.5 | 配置 Alembic 迁移       | 初始化迁移环境                                  | 0.5h | ✅ |
| 1.6 | 创建新模型文件             | Organization、Permission、Wiki、TaskComment | 1h   | ✅ |
| 1.7 | 扩展现有模型              | User、Role、Task 添加新字段                     | 1h   | ✅ |
| 1.8 | 创建 Pydantic Schemas | 新增和扩展的 Schema                            | 2h   | ✅ |
| 1.9 | 测试数据库连接和迁移          | 运行 alembic upgrade head                  | 0.5h | ✅ |

#### 交付物

- [x] 项目目录结构 (`D:/pioneclaw/`)
- [x] 后端核心代码（可运行）
- [x] 前端代码（可运行）
- [x] 数据库迁移文件 (`alembic/versions/001_initial.py`)
- [x] 基础模型和 Schema (Organization, Permission, Wiki, WikiVersion, TaskComment)
- [x] 更新 `main.py`、`init_data.py`、`security.py`、`config.py`、`database.py`
- [x] `.env.example` 和 `requirements.txt` 已更新

---

### 阶段二：认证与权限系统 (2天) ✅ 已完成

#### 任务清单

| ID   | 任务         | 说明                                                    | 预计时间 | 状态 |
| ---- | ---------- | ----------------------------------------------------- | ---- | ---- |
| 2.1  | 扩展 auth.py | 添加 refresh token、账户锁定、密码重置                            | 2h   | ✅ |
| 2.2  | 创建权限检查器    | `core/permissions.py` - PermissionChecker 类           | 2h   | ✅ |
| 2.3  | 实现四级权限等级   | super_admin / org_admin / system_admin / user         | 1h   | ✅ |
| 2.4  | 实现通配符权限匹配  | `task:*` 匹配 `task:create` 等                           | 1h   | ✅ |
| 2.5  | 创建权限缓存     | Redis 或内存缓存权限信息                                       | 1h   | ✅ (内存) |
| 2.6  | 创建权限 API   | `api/v1/permissions.py`                               | 2h   | ✅ |
| 2.7  | 扩展角色 API   | 添加权限分配接口                                              | 1h   | ✅ |
| 2.8  | 更新前端权限逻辑   | `stores/permission.ts`、`composables/usePermission.ts` | 2h   | ✅ |
| 2.9  | 创建权限树组件    | `components/PermissionTree.vue`                       | 2h   | ✅ (集成到Permissions.vue) |
| 2.10 | 单元测试       | 认证和权限测试用例                                             | 2h   | ✅ |

#### 交付物

- [x] 扩展的认证系统 (refresh token + 账户锁定 + 密码重置)
- [x] 四级 RBAC 权限系统 (PermissionChecker + 通配符匹配)
- [x] 权限 API (`api/permissions.py`) 和前端组件 (`views/Permissions.vue`)
- [x] 前端权限组合式函数 (`composables/usePermission.ts`)
- [x] 单元测试 (76 tests 全通过)

#### 单元测试详情 ✅

**测试框架**: pytest + pytest-asyncio, 每测试独立 SQLite 文件数据库

| 测试文件 | 测试数 | 覆盖模块 |
|----------|--------|----------|
| `tests/test_auth.py` | 36 | 密码哈希、JWT 令牌、注册、登录、账户锁定、令牌刷新、获取当前用户、修改密码、密码重置、更新资料、登出 |
| `tests/test_permissions.py` | 25 | check_permission 通配符匹配、has_any/has_all_permissions、get_user_permission_codes、PermissionChecker/PermissionCheckerAll 依赖行为 |
| `tests/test_roles_api.py` | 15 | 角色 CRUD、系统角色保护(不可删除)、权限更新 |
| `tests/test_organizations.py` | 16 | 组织列表/树/创建/更新/删除/组织用户, 子组织创建 |
| `tests/test_users_api.py` | 16 | 用户列表/创建/更新/删除/密码重置, 组织分配 |

**Bug 修复**: `auth.py` 中 `locked_until` 与 `datetime.now(timezone.utc)` 的时区敏感/不敏感比较错误，已修复；`organization.py` schema 中 `metadata` 别名导致 Pydantic 读取 SQLAlchemy MetaData 对象而非列值，已移除别名

---

### 阶段三：组织与用户管理 (2天) ✅ 已完成

#### 任务清单

| ID  | 任务       | 说明                        | 预计时间 | 状态 |
| --- | -------- | ------------------------- | ---- | ---- |
| 3.1 | 创建组织 API | `api/v1/organizations.py` | 2h   | ✅ |
| 3.2 | 实现组织树查询  | 递归查询、路径更新                 | 2h   | ✅ |
| 3.3 | 创建组织服务层  | 组织 CRUD、用户分配逻辑            | 2h   | ✅ |
| 3.4 | 扩展用户 API | 添加组织关联、权限管理               | 1h   | ✅ |
| 3.5 | 创建组织管理页面 | `views/Organizations.vue` | 3h   | ✅ |
| 3.6 | 创建组织树组件  | `components/OrgTree.vue`  | 2h   | ✅ (集成到Organizations.vue) |
| 3.7 | 更新用户管理页面 | 添加组织分配                    | 1h   | ✅ |
| 3.8 | 更新注册流程   | 注册时创建组织                   | 1h   | ✅ |
| 3.9 | 单元测试     | 组织和用户管理测试                 | 2h   | ✅ |

#### 交付物

- [x] 组织管理 API (`api/organizations.py`) - CRUD + 树 + 用户列表
- [x] 组织管理前端页面 (`views/Organizations.vue`)
- [x] 注册流程更新（注册自动创建组织）
- [x] 组织类型定义 (`types/organization.d.ts`) + API (`api/organization.ts`)
- [x] 用户管理页面更新 (组织分配 + 组织筛选 + 搜索)
- [x] 单元测试 (108 tests 全通过)

---

### 阶段四：任务管理扩展 (1.5天) ✅ 已完成

#### 任务清单

| ID  | 任务         | 说明                      | 预计时间 | 状态 |
| --- | ---------- | ----------------------- | ---- | ---- |
| 4.1 | 扩展 Task 模型 | 添加新字段、创建 TaskComment 模型 | 1h   | ✅ |
| 4.2 | 扩展任务 API   | 子任务、评论、附件、批量操作          | 3h   | ✅ (评论API) |
| 4.3 | 创建任务服务层    | 任务业务逻辑                  | 2h   | ✅ (集成到API) |
| 4.4 | 扩展任务前端     | 子任务、附件上传、批量操作           | 3h   | 待完成 |
| 4.5 | 创建任务评论组件   | 评论列表、回复、@提及             | 2h   | 待完成 |
| 4.6 | 单元测试       | 任务管理测试                  | 1h   | 待完成 |

#### 交付物

- [x] TaskComment 模型 (`models/task_comment.py`)
- [x] TaskComment Schema (`schemas/task_comment.py`)
- [x] Task 模型扩展（comments 关系）
- [ ] 任务 API 扩展（子任务、附件）
- [ ] 前端任务扩展

#### 交付物

- [x] 扩展的任务模型
- [x] 任务管理 API
- [x] 任务管理前端
- [x] 单元测试

---

### 阶段五：Wiki 知识库 (1.5天)

#### 任务清单

| ID  | 任务             | 说明                                         | 预计时间 |
| --- | -------------- | ------------------------------------------ | ---- |
| 5.1 | 创建 Wiki 模型     | Wiki、WikiVersion 模型                        | 1h   |
| 5.2 | 创建 Wiki API    | CRUD、版本历史、导入                               | 2h   |
| 5.3 | 创建 Wiki 服务层    | 版本管理、Markdown 解析                           | 2h   |
| 5.4 | 创建 Wiki 页面     | `views/Wiki.vue`                           | 3h   |
| 5.5 | 创建 Wiki 编辑器组件  | `components/WikiEditor.vue` - Markdown 编辑器 | 2h   |
| 5.6 | 实现版本历史功能       | 版本对比、恢复                                    | 2h   |
| 5.7 | 实现 Markdown 导入 | 文件上传、解析                                    | 1h   |
| 5.8 | 单元测试           | Wiki 测试                                    | 1h   |

#### 交付物

- [x] Wiki 模型和 API
- [x] Wiki 前端页面
- [x] Markdown 编辑器
- [x] 版本历史功能
- [x] 单元测试

---

### 阶段六：前端完善与集成 (2天)

#### 任务清单

| ID  | 任务               | 说明                | 预计时间 |
| --- | ---------------- | ----------------- | ---- |
| 6.1 | 更新路由配置           | 添加新页面路由           | 0.5h |
| 6.2 | 更新侧边栏菜单          | 添加组织、权限、Wiki 菜单   | 0.5h |
| 6.3 | 更新 API 层         | 新增 API 调用方法       | 1h   |
| 6.4 | 创建 TypeScript 类型 | 新增类型定义            | 1h   |
| 6.5 | 更新权限指令           | `v-permission` 指令 | 1h   |
| 6.6 | 更新主题样式           | 统一样式              | 1h   |
| 6.7 | 集成测试             | 端到端测试             | 2h   |
| 6.8 | 性能优化             | 懒加载、缓存            | 2h   |
| 6.9 | 文档更新             | README、API 文档     | 2h   |

#### 交付物

- [x] 完整的前端应用
- [x] 集成测试
- [x] 文档

---

### 阶段七：测试与部署 (1天)

#### 任务清单

| ID  | 任务        | 说明                        | 预计时间 |
| --- | --------- | ------------------------- | ---- |
| 7.1 | 单元测试完善    | 覆盖率 > 80%                 | 2h   |
| 7.2 | 集成测试      | API 端点测试                  | 2h   |
| 7.3 | 性能测试      | 压力测试                      | 1h   |
| 7.4 | Docker 配置 | Dockerfile、docker-compose | 1h   |
| 7.5 | CI/CD 配置  | GitHub Actions            | 1h   |
| 7.6 | 部署文档      | DEPLOY.md                 | 1h   |

#### 交付物

- [x] 测试报告
- [x] Docker 配置
- [x] CI/CD 配置
- [x] 部署文档

---

## 六、工时估算

| 阶段       | 预计工时     | 复用比例     | 说明              |
| -------- | -------- | -------- | --------------- |
| 阶段一：基础架构 | 2 天      | 80%      | 大量复用 CircleBot  |
| 阶段二：认证权限 | 2 天      | 50%      | 扩展权限系统          |
| 阶段三：组织用户 | 2 天      | 30%      | 主要新增开发          |
| 阶段四：任务扩展 | 1.5 天    | 70%      | 扩展字段和 API       |
| 阶段五：Wiki | 1.5 天    | 40%      | 主要新增开发          |
| 阶段六：前端完善 | 2 天      | 70%      | 整合和扩展           |
| 阶段七：测试部署 | 1 天      | 80%      | 复用 CircleBot 配置 |
| **总计**   | **12 天** | **~60%** |                 |

---

## 七、风险与应对

### 7.1 技术风险

| 风险       | 影响  | 应对措施                   |
| -------- | --- | ---------------------- |
| 数据库模型不兼容 | 高   | 使用 Alembic 迁移，逐步演进     |
| 权限系统复杂度  | 中   | 参考 SurperBot 原有实现，简化设计 |
| 前端状态管理   | 中   | 使用 Pinia 最佳实践          |

### 7.2 进度风险

| 风险      | 影响  | 应对措施            |
| ------- | --- | --------------- |
| 新功能开发超时 | 中   | 优先核心功能，其他功能后续迭代 |
| 测试不充分   | 中   | 同步编写测试用例        |

---

## 八、后续迭代

### v1.1 计划

- [ ] 工作流模板
- [ ] 高级搜索 (Elasticsearch)
- [ ] 消息通知系统
- [ ] 移动端适配

### v1.2 计划

- [ ] 多语言支持
- [ ] 数据导入导出
- [ ] 审计日志
- [ ] 高级权限 (数据权限、字段权限)

---

## 九、参考资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 文档](https://docs.sqlalchemy.org/en/20/)
- [Pydantic v2 文档](https://docs.pydantic.dev/latest/)
- [Vue 3 文档](https://vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
- [LiteLLM 文档](https://docs.litellm.ai/)

---

## 十、UI 改进记录

### 10.1 仪表盘重构 ✅ 已完成

**目标**: 重新设计仪表盘布局，更直观地展示系统状态

**改动内容**:

- **欢迎区域**: 顶部保留时间问候语，品牌名从 SquareBot 更新为 PioneClaw
- **概览指标卡片**: 4 个指标卡片（替代原来的智能体/技能/记忆/任务）
  - 网关状态（在线/总数 Runner）
  - 在线智能体（活跃/总数 Agent）
  - 今日任务（当日创建的任务数）
  - API 调用次数（当日调用次数，是否达限）
- **左侧区域**: API 用量统计（24h），含模型调用分布
- **右侧区域**:
  - 任务分布（已完成/进行中/待办/已取消的堆叠条形图）
  - 最近活动（最近 5 条任务，含状态标签和相对时间）

**后端改动**:

- `backend/app/api/dashboard.py` - `/dashboard/counts` 端点扩展，返回网关状态、在线智能体、今日任务（按状态分组）、API 调用次数、最近任务列表
- 修复了 `failed_calls` 原来硬编码为 0 的问题，改为实际查询 `is_success == False` 的记录

### 10.2 品牌重命名 ✅ 已完成

**目标**: 将所有 SquareBot 引用统一更改为 PioneClaw

**改动文件**:

- `frontend/index.html` - 页面标题
- `frontend/package.json` - 包名
- `frontend/src/views/Dashboard.vue` - 欢迎文字
- `frontend/src/views/Login.vue` - 登录页标题和 Logo
- `frontend/src/views/Settings.vue` - 关于页面系统名、开发者名、默认设置
- `frontend/src/views/Chat.vue` - localStorage key
- `frontend/src/layouts/MainLayout.vue` - Logo 引用
- `backend/app/api/settings.py` - 默认系统名
- `backend/app/modules/agent/context.py` - Agent 系统提示词
- `backend/app/modules/agent/skills.py` - Skill metadata key
- `backend/app/modules/agent/vector_store.py` - 模块文档
- `backend/app/modules/agent/task_board.py` - 模块文档
- `backend/app/modules/agent/research.py` - 模块文档
- `backend/app/modules/agent/experience.py` - 模块文档
- `backend/app/modules/agent/consolidator.py` - 模块文档
- `frontend/public/squarebot-logo.svg` → `pioneclaw-logo.svg`
- `frontend/public/squarebot.svg` → `pioneclaw.svg`

### 10.3 暗色/亮色主题切换 ✅ 已完成

**目标**: 支持暗色模式和亮色模式切换

**实现方式**:

- 引入 Element Plus 官方暗色模式 CSS (`element-plus/theme-chalk/dark/css-vars.css`)
- 创建 `stores/theme.ts` - 主题状态管理，支持 localStorage 持久化 + 跟随系统偏好
- 在 `MainLayout.vue` 顶栏添加主题切换按钮（太阳/月亮图标）
- 通过 `<html class="dark">` 切换 Element Plus CSS 变量实现暗色模式
- 更新 `main.scss` 使用 CSS 变量替代硬编码颜色
- 更新 `Dashboard.vue` 和 `MainLayout.vue` 样式使用 `var(--el-*)` 变量以适配双主题

**改动文件**:

- `frontend/src/main.ts` - 导入暗色 CSS，初始化主题
- `frontend/src/stores/theme.ts` - 新建主题 store
- `frontend/src/layouts/MainLayout.vue` - 添加切换按钮，CSS 变量化
- `frontend/src/styles/main.scss` - CSS 变量化，添加暗色过渡
- `frontend/src/views/Dashboard.vue` - CSS 变量化

### 10.4 仪表盘 UI 修复 ✅ 已完成

**目标**: 修复对齐问题，"最近活动"改为"最近日志"

**改动**:

- 概览卡片：固定 `height: 88px`，对齐 `card-label`/`card-value` 层级，统一间距
- 主内容区域：从 `el-row/el-col` 改为 CSS Grid (`grid-template-columns: 14fr 10fr`)，避免 flex 撑开不对齐
- 用量统计：每个 item 加 `background: var(--el-fill-color-lighter)` + `border-radius: 6px`，视觉分组
- "最近活动" → "最近日志"：数据源从 Task 改为 ApiUsage，展示模型名、token 数、耗时、失败原因
- 后端 `/dashboard/counts` 新增 `recent_logs` 字段（最近 10 条 ApiUsage 记录）

### 10.5 组织权限闪退 + 侧边栏重构 ✅ 已完成

**闪退修复**:
- `api/index.ts` 缺少 `ListResponse` / `UserResponse` 类型导出，导致 `permission.ts` 和 `organization.ts` import 失败白屏
- 角色权限数据格式不一致：后端用 `{"codes": ["task:create", ...]}`，前端原来用 `{"task": ["create", ...]}`
- OrgPerms.vue 统一使用 `codes` 格式，与 `get_user_permission_codes()` 和 `check_permission()` 对齐

**侧边栏重构** (MainLayout.vue):

| 原结构 | 新结构 |
|--------|--------|
| 智能体管理 | 智能体 |
| Runner 管理 | Runner (独立菜单项) |
| 技能管理 | 技能 (独立菜单项) |
| 记忆系统 | 记忆 (子菜单: 长期记忆 / Agent 记忆 / 定时任务) |
| 知识库 | 知识 (子菜单: 知识库 / Wiki) |
| Wiki 知识库 | ↑ |
| 渠道管理 | → 合入"系统"子菜单 |
| 系统子菜单 (7项) | 系统 (子菜单: 组织与权限 / 用户管理 / 渠道管理 / AI模型配置 / 日志中心 / 系统设置) |
| 组织管理 | → 合入"组织与权限" |
| 权限管理 | → 合入"组织与权限" |
| 角色管理 | → 合入"组织与权限" |

**新增页面**:
- `OrgPerms.vue` — 统一的组织与权限管理页面，3 个 Tab（组织/角色/权限），角色权限配置使用 codes 格式与后端对齐

**新增路由**: `/org-perms` → `OrgPerms.vue`

---

## 十一、CountBot 对比与复用计划

> 基于 D:\countbot 与 PioneClaw 的全面对比，识别可复用/借鉴的模块

### 11.1 对比总结

| 模块 | CountBot | PioneClaw | PioneClaw 缺失 | 复用优先级 |
|------|----------|-----------|---------------|-----------|
| Agent 核心循环 | `AgentLoop` ~800行，Key轮换+trace ID+工具去重+审计+Thinking | `AgentLoop` ~660行，基础ReAct | tool_event_handler回调、trace ID、工具去重、审计日志 | P1 |
| 消息渠道 | 9个适配器(飞书/钉钉/QQ/TG/微信/企微/微博/小智/基类) | 2个(飞书/TG) | 钉钉/QQ/微信/企微/微博/小智 共6个 | P0 |
| 工具系统 | 17个工具(filesystem/shell/web/screenshot/monitoring等) | 5个(echo/time/calc/readfile/writefile+web) | filesystem/shell/file_search/monitoring/screenshot/send_media | P0 |
| 记忆系统 | 文件行式存储+关键词搜索 | 文件行式+**VectorStore向量混合搜索** | 无（PioneClaw领先） | - |
| 定时任务 | CronScheduler精确唤醒+信号量+Heartbeat完整实现 | heartbeat.py未完成 | CronScheduler精确调度、Heartbeat完整实现 | P1 |
| 消息队列 | EnterpriseMessageQueue(四级优先级/去重/死信/持久化/消费确认) | 无 | 整个消息队列模块 | P1 |
| 认证中间件 | RemoteAuthMiddleware(本地直通/远程认证+setup_secret) | JWT+bcrypt(标准认证) | 本地直通/远程认证双模式 | P2 |
| 前端 | 无独立前端 | Vue3+TS+Pinia完整前端 | 无（PioneClaw领先） | - |

### 11.2 复用计划

#### P0: 渠道适配器 + 工具系统

**渠道适配器** (6个，从 CountBot 直接移植):

| 渠道 | 源文件 | 目标路径 | 改动量 |
|------|--------|---------|-------|
| 钉钉 | `countbot/backend/modules/channels/dingtalk.py` | `pioneclaw/backend/app/modules/channels/dingtalk.py` | 中 - 需适配PioneClaw基类 |
| QQ | `countbot/backend/modules/channels/qq.py` | `pioneclaw/backend/app/modules/channels/qq.py` | 中 |
| 微信 | `countbot/backend/modules/channels/wechat.py` | `pioneclaw/backend/app/modules/channels/wechat.py` | 高 - 依赖iLink SDK |
| 企业微信 | `countbot/backend/modules/channels/wecom.py` | `pioneclaw/backend/app/modules/channels/wecom.py` | 高 - 依赖LongConnBot |
| 微博 | `countbot/backend/modules/channels/weibo.py` | `pioneclaw/backend/app/modules/channels/weibo.py` | 中 |
| 小智AI | `countbot/backend/modules/channels/xiaozhi.py` | `pioneclaw/backend/app/modules/channels/xiaozhi.py` | 低 - MCP协议 |

辅助文件:
- `countbot/backend/modules/channels/media_utils.py` → `pioneclaw/backend/app/modules/channels/media_utils.py`
- `countbot/backend/modules/channels/handler.py` → `pioneclaw/backend/app/modules/channels/handler.py`

**工具系统** (7个核心工具):

| 工具 | 源文件 | 功能 | 改动量 |
|------|--------|------|-------|
| filesystem | `countbot/backend/modules/tools/filesystem.py` | 文件读写编辑+路径限制 | 低 - 适配基类 |
| shell | `countbot/backend/modules/tools/shell.py` | 安全Shell执行+危险命令拦截 | 低 |
| file_search | `countbot/backend/modules/tools/file_search.py` | 通配符文件搜索 | 低 |
| monitoring | `countbot/backend/modules/tools/monitoring.py` | 长时间执行进度通知 | 低 |
| screenshot | `countbot/backend/modules/tools/screenshot.py` | 桌面/网页截图 | 中 - 依赖mss/playwright |
| send_media | `countbot/backend/modules/tools/send_media.py` | 渠道媒体发送 | 中 |
| conversation_history | `countbot/backend/modules/tools/conversation_history.py` | 工具调用历史 | 低 |

#### P1: Agent增强 + 定时任务 + 消息队列

**Agent Loop 增强** (从 CountBot `loop.py` 借鉴):

- `tool_event_handler` + `reasoning_event_handler` 回调钩子 → 替换当前内联 WebSocket 通知
- `request_trace_id` 全链路追踪
- `seen_tool_call_ids` 工具调用去重
- `file_audit_logger` 审计日志
- `_try_key_rotation()` 精细 Key 轮换

**定时任务完善**:

- `CronScheduler` 精确按需唤醒(不轮询) + 信号量并发控制 → `pioneclaw/backend/app/modules/agent/cron_scheduler.py`
- `CronExecutor` heartbeat 特殊任务分发 → 扩展现有 cron 模块
- `HeartbeatService` 完整实现(用户空闲检测 + LLM问候 + 两阶段提交) → 更新 `heartbeat.py`
- `ensure_heartbeat_job()` 启动自动注册

**消息队列**:

- `EnterpriseMessageQueue` 整体移植 → `pioneclaw/backend/app/modules/messaging/enterprise_queue.py`
- `RateLimiter` 令牌桶限流 → `pioneclaw/backend/app/modules/messaging/rate_limiter.py`

#### P2: 认证中间件 + 审计

- `RemoteAuthMiddleware` 本地直通/远程认证双模式 → 新增 `pioneclaw/backend/app/core/auth_middleware.py`
- `setup_secret` 远程初始化机制
- scrypt 密码哈希(替代 bcrypt)

### 11.3 PioneClaw 领先部分（不借鉴）

- VectorStore 向量语义搜索 + 混合搜索（CountBot 无此能力）
- 组织/角色/权限体系
- 知识库 / Wiki
- 完整的 Vue 3 前端
- Alembic 数据库迁移

---

## 十二、知识库合并计划

> 将 Knowledge（RAG数据摄入）和 Wiki（协作文档）合并为统一的"知识库"模块

### 12.1 合并策略

以 Wiki 为基础，增加 Knowledge 的分块/RAG 能力。合并后保留 Wiki 的版本控制、树形结构、权限检查，新增分块索引和向量检索。

### 12.2 合并步骤

1. **Wiki 模型增加字段**: `chunk_count`, `total_chunks`, `doc_type`, `source`, `is_indexed`
2. **自动分块**: Wiki 内容保存时自动按段落分块，写入 VectorStore
3. **合并 API**: Wiki API 增加 `/wiki/search/semantic` 语义搜索端点
4. **迁移**: 将 KnowledgeDocument 数据迁移到 Wiki 表
5. **前端合并**: 删除 Knowledge.vue，Wiki.vue 增加文档导入和分块管理
6. **路由清理**: 删除 /knowledge 路由

### 12.3 涉及文件

- `backend/app/models/wiki.py` - 增加分块相关字段
- `backend/app/api/wiki.py` - 增加语义搜索、文档导入
- `backend/app/api/knowledge.py` - 标记废弃
- `backend/app/api/__init__.py` - 移除 knowledge router
- `frontend/src/views/Wiki.vue` - 增加导入/分块管理
- `frontend/src/views/Knowledge.vue` - 删除
- `frontend/src/router/index.ts` - 移除 /knowledge
- `frontend/src/layouts/MainLayout.vue` - 侧边栏移除"知识库"菜单项

---

## 十三、AIE 对比与复用计划

> 基于 D:\aie (AIE/AI Employee) 与 PioneClaw 的全面对比，识别可复用/借鉴的模块

### 13.1 对比总结

| 模块 | AIE | PioneClaw | PioneClaw 缺失 | 复用优先级 |
|------|-----|-----------|---------------|-----------|
| 分层记忆 | L0/L1/L2 三级记忆 + MCP 协议 + 向量语义搜索 + 意图分析 + 重排序 | 行式存储 + 关键词搜索 + VectorStore | 整个 L0/L1/L2 体系、MCP 协议、语义检索、意图分析、多维重排序 | P0 |
| 知识图谱 RAG | LightRAG + NetworkX，5种检索模式(local/global/hybrid/naive/mix) | 无 | 整个 GraphRAG 模块 | P0 |
| 企业消息队列 | 4级优先级 + MD5去重 + 死信队列 + 消费确认 + 持久化 + 令牌桶限流 | 无 | 整个消息队列模块 | P1 |
| 技能系统 | YAML frontmatter + 3层加载优先级 + 热重载 + always自动激活 + 依赖检查 | 基础 Skill 模型 + DB 存储 | 热重载、always自动激活、3层加载、依赖检查 | P1 |
| 子代理系统 | SubagentManager(1328行) + 7种子代理类型 + 并发信号量 + 自动重试 + 心跳监控 + 后台任务 + 任务恢复 | subagent.py(基础) | 完整子代理调度、心跳监控、自动重试、后台进程管理 | P1 |
| Agent Loop | 759行 + 流式输出 + 会话级模型覆盖 + 工具重试 + 插件事件 | ~660行 + 基础ReAct | 会话级模型覆盖、工具重试、插件事件 | P2 |
| 工作流引擎 | Pipeline/Graph/Council 三模式 + WebSocket 可视化 | 基础 workflow.py | Graph DAG 模式、Council 多视角评审 | P2 |
| 渠道系统 | 8个适配器(飞书/钉钉/QQ/TG/微信/企微/微博/小智) | 2个(飞书/TG) | 钉钉/QQ/微信/企微/微博/小智 | P2 |
| 插件系统 | PluginManager + EventBus + 2套内置插件(Superpowers/Superworkers) | 无 | 整个插件体系 | P2 |
| 输出/多模态 | 图片生成 + TTS + 音乐 + 视频 + 视频理解 | 无 | 整个多模态输出模块 | P3 |
| 认证 | 零配置渐进式(本地直通/远程JWT) | JWT + bcrypt 标准认证 | 本地直通/远程双模式 | P3 |

### 13.2 核心模块复用详情

#### P0: 分层记忆 + 知识图谱 RAG

**分层记忆 (从 AIE `memory_mcp_server/` 移植)**:

| 组件 | 源文件 | 功能 | 改动量 |
|------|--------|------|-------|
| TierManager | `aie/backend/modules/memory_mcp_server/service/tier_manager.py` ~300行 | L0/L1/L2 层级管理，LLM自动生成摘要 | 中 - 需适配PioneClaw LLM调用 |
| RetrievalEngine | `aie/backend/modules/memory_mcp_server/service/retrieval_engine.py` ~328行 | 层级检索 + 语义搜索 + BFS扩展 + 分数传播 | 中 |
| RerankModule | `aie/backend/modules/memory_mcp_server/service/rerank_module.py` ~227行 | 5维重排序(语义/热度/时效/层级/类型) | 低 |
| IntentAnalyzer | `aie/backend/modules/memory_mcp_server/service/intent_analyzer.py` ~87行 | LLM驱动的查询意图分析 | 低 |
| MemoryService | `aie/backend/modules/memory_mcp_server/service/memory_service.py` ~362行 | 门面类，组合所有组件 | 中 |
| MCPServer | `aie/backend/modules/memory_mcp_server/protocol/server.py` ~256行 | JSON-RPC 2.0 MCP协议服务 | 低 |
| Embedder | `aie/backend/modules/memory_mcp_server/utils/embedder.py` ~585行 | 多Provider嵌入(统一/BGE/OpenAI/Jina/本地/降级) | 高 - 需适配PioneClaw的LiteLLM |
| MemoryPlugin | `aie/backend/modules/mcp/memory_plugin.py` ~276行 | 生命周期管理(启动/停止MCP子进程) | 中 |
| VectorIndex | `aie/backend/modules/memory_mcp_server/storage/vector_index.py` ~283行 | SQLite BLOB + 余弦相似搜索 | 低 - 与PioneClaw VectorStore合并 |

**知识图谱 RAG (从 AIE `graph_rag/` 移植)**:

| 组件 | 源文件 | 功能 | 改动量 |
|------|--------|------|-------|
| GraphRAGClient | `aie/backend/modules/graph_rag/core.py` ~692行 | LightRAG封装，5种查询模式 | 中 - 需适配嵌入和LLM配置 |
| GraphRAGSettings | `aie/backend/modules/graph_rag/config.py` ~166行 | 配置模型 | 低 |
| KnowledgeHub集成 | `aie/backend/modules/graph_rag/integrations/knowledge_hub.py` | 桥接知识库 | 中 |
| Skill工具 | `aie/backend/modules/graph_rag/skill.py` | Agent可用的索引/查询/统计工具 | 低 |
| REST API | `aie/backend/modules/graph_rag/api.py` | 图操作端点 | 低 |

**新增依赖**: `lightrag-hku>=1.0.0`, `networkx>=3.0`

#### P1: 消息队列 + 技能系统增强 + 子代理系统

**企业消息队列**:

| 组件 | 源文件 | 功能 | 改动量 |
|------|--------|------|-------|
| EnterpriseMessageQueue | `aie/backend/modules/messaging/enterprise_queue.py` ~320行 | 4级优先级 + 去重 + 死信 + 消费确认 + 持久化 | 低 - 直接移植 |
| RateLimiter | `aie/backend/modules/messaging/rate_limiter.py` ~93行 | 令牌桶限流 | 低 - 直接移植 |

**技能系统增强** (在现有 Skill 模型基础上增加):

| 功能 | AIE 实现 | 适配方案 |
|------|----------|---------|
| YAML frontmatter 技能定义 | `aie/backend/modules/agent/skills.py` | 新增 `skills/` 目录支持 SKILL.md 格式 |
| always 自动激活 | frontmatter `always: true` | 技能表增加 `always_activate` 字段 |
| 热重载 | `reload()` 方法 | 增加 SkillWatcher 定时扫描 |
| 3层加载优先级 | workspace > builtin > openclaw | 适配为 workspace > builtin > shared |
| 依赖检查 | `check_requirements()` | 增加运行时依赖校验 |

**子代理系统** (从 AIE `subagent.py` 借鉴核心模式):

| 功能 | AIE 实现 | 适配方案 |
|------|----------|---------|
| 并发信号量 | `Semaphore(max_concurrent=3)` | 增加到 SubagentManager |
| 自动重试 | 指数退避 + 上下文注入 | 增加重试逻辑 |
| 心跳监控 | HeartbeatScheduler + LLM进度分析 | 增加 SubagentHeartbeat |
| 任务恢复 | `recover_tasks()` 从DB恢复 | 增加启动恢复 |
| 7种子代理类型 | GENERAL/EXPLORE/RESEARCH/DEBUG/REVIEW/BUILD/LONG_RUNNING | 先实现3种核心类型 |
| 后台任务 | StartBackgroundTool + sleeping 状态 | 后续迭代 |

#### P2: 工作流增强 + Agent Loop 增强 + 渠道扩展 + 插件系统

- **工作流**: 增加 Graph DAG 模式 + Council 多视角评审模式
- **Agent Loop**: 会话级模型覆盖、工具重试(max_retries=3)、插件事件发射
- **渠道**: 移植 AIE 的钉钉/QQ/微信/企微适配器(同 CountBot)
- **插件**: PluginManager + EventBus + 内置 Superpowers 插件

#### P3: 多模态输出 + 认证增强

- **多模态**: 图片生成、TTS、音乐/视频生成（需要 MiniMax 等 API 密钥）
- **认证**: 本地直通/远程双模式，适应边缘部署场景

### 13.3 PioneClaw 领先部分（不借鉴）

- 组织/角色/权限体系（AIE 无此能力）
- 完整的 Vue 3 前端管理界面（AIE 前端极简）
- Wiki 协作文档 + 版本控制
- Alembic 数据库迁移
- 仪表盘 + 数据分析

---

## 十四、统一开发计划

> 整合所有待开发项（原 Plan + CountBot 对比 + AIE 对比），按优先级排列

### 14.1 开发优先级总表

| 序号 | 任务 | 来源 | 优先级 | 预估工时 | 前置依赖 |
|------|------|------|--------|---------|---------|
| 1 | 分层记忆 L0/L1/L2 + MCP 协议 | AIE | P0 | 5天 | 无 |
| 2 | 知识图谱 RAG (LightRAG) | AIE | P0 | 3天 | #1 |
| 3 | 知识库与 Wiki 合并 | 原Plan 12 | P0 | 2天 | #2 |
| 4 | 企业消息队列 | AIE | P1 | 2天 | 无 |
| 5 | 技能系统增强(热重载/always/依赖检查) | AIE | P1 | 2天 | 无 |
| 6 | 子代理系统(并发/重试/心跳/恢复) | AIE | P1 | 3天 | #5 |
| 7 | 任务管理扩展(子任务+附件+前端完善) | 原Plan 4 | P1 | 2天 | 无 |
| 8 | Agent Loop 增强(模型覆盖/工具重试/插件事件) | AIE+CountBot | P1 | 2天 | #6 |
| 9 | 渠道适配器(钉钉/QQ/微信/企微) | AIE+CountBot | P2 | 3天 | #4 |
| 10 | 工作流增强(Graph DAG + Council) | AIE | P2 | 2天 | #8 |
| 11 | 插件系统(PluginManager + EventBus) | AIE | P2 | 2天 | #8 |
| 12 | 认证增强(本地直通/远程双模式) | AIE | P2 | 1天 | 无 |
| 13 | 多模态输出(图片/TTS/视频) | AIE | P3 | 3天 | #8 |
| 14 | 定时任务完善(CronScheduler精确唤醒) | CountBot | P2 | 1天 | 无 |

### 14.2 阶段划分

**第一阶段: 智能记忆与知识 (P0, ~10天)**
- #1 分层记忆 + #2 知识图谱 RAG + #3 知识库合并

**第二阶段: 调度与执行 (P1, ~11天)**
- #4 消息队列 + #5 技能增强 + #6 子代理 + #7 任务扩展 + #8 Agent Loop增强

**第三阶段: 扩展与集成 (P2, ~9天)**
- #9 渠道 + #10 工作流 + #11 插件 + #12 认证 + #14 定时任务

**第四阶段: 多模态 (P3, ~3天)**
- #13 多模态输出

### 14.3 当前完成状态

| 已完成 | 说明 |
|--------|------|
| Phase 1-3: 基础架构 + 认证权限 + 组织用户 | 项目骨架、JWT/RBAC、组织树 |
| Phase 2 单元测试 | 76 tests 全通过 (auth/permissions/roles) |
| Phase 5: Wiki 知识库 | Wiki模型/API/前端/版本历史 |
| UI: 仪表盘重构、品牌重命名、暗色/亮色主题、侧边栏重构 | |
| 角色与权限合并 | OrgPerms.vue 权限管理合入角色管理 |
| 侧边栏: 运行时拆开、渠道移入系统、定时任务移入记忆 | |

---

**文档版本**: v1.4
**创建日期**: 2026-05-01
**更新日期**: 2026-05-01
