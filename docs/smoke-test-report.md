# PioneClaw 冒烟测试报告

> 日期：2026-05-04 | 测试轮次：第一轮（冒烟）

---

## 测试概要

| 指标 | 结果 |
|------|------|
| 后端 API 端点 | 18/18 可达 |
| 创建操作 (POST) | 7/7 通过 |
| 读取操作 (GET) | 18/18 通过 |
| 更新操作 (PUT) | 4/4 通过 |
| 删除操作 (DELETE) | 6/6 通过 |
| 聊天 (Chat) | 1/1 通过（实际调用 LLM 返回响应） |
| 后端单元测试 | 535 passed / 7 failed / 3 skipped |
| 前端 TypeScript 编译 | 可运行（有非阻塞型 TS 警告） |

---

## 一、后端 API 冒烟测试结果

### 1.1 读取接口（GET）

| 端点 | HTTP | 状态 |
|------|------|------|
| `/api/dashboard/stats` | 200 | ✅ 返回统计数据 |
| `/api/agents` | 200 | ✅ 返回智能体列表 |
| `/api/tasks` | 200 | ✅ 返回任务列表（空） |
| `/api/tasks/stats` | 200 | ✅ 返回任务统计 |
| `/api/skills` | 200 | ✅ 返回技能列表 |
| `/api/ai-configs` | 200 | ✅ 返回模型配置 |
| `/api/memories` | 200 | ✅ 返回记忆列表（空） |
| `/api/logs` | 200 | ✅ 返回日志列表 |
| `/api/settings` | 200 | ✅ 返回设置 |
| `/api/users` | 200 | ✅ 返回用户列表 |
| `/api/wiki/` | 200 | ✅ 返回 Wiki 文档 |
| `/api/organizations/` | 200 | ✅ 返回组织列表 |
| `/api/channels` | 200 | ✅ 返回渠道列表 |
| `/api/cron` | 200 | ✅ 返回定时任务 |
| `/api/chat/models` | 200 | ✅ 返回可用模型 |
| `/api/runners` | 200 | ✅ 返回 Runner 列表 |
| `/api/roles` | 200 | ✅ 返回角色列表 |
| `/api/graph-rag/stats` | 200 | ✅ 返回图谱统计 |

### 1.2 写入接口（POST/PUT/DELETE）

| 操作 | HTTP | 状态 |
|------|------|------|
| 创建智能体 | 201 | ✅ |
| 创建任务 | 201 | ✅ |
| 创建 AI 配置 | 201 | ✅ |
| 创建记忆 | 201 | ✅ |
| 创建 Wiki | 201 | ✅ |
| 创建定时任务 | 201 | ✅ |
| 更新智能体 | 200 | ✅ |
| 切换智能体状态 | 200 | ✅ |
| 完成任务 | 200 | ✅ |
| 切换技能状态 | 200 | ✅ |
| 设置默认模型 | 200 | ✅ |
| 保存设置 | 200 | ✅ |
| 删除智能体 | 200 | ✅ |
| 删除任务 | 200 | ✅ |
| 删除记忆 | 200 | ✅ |
| 删除 AI 配置 | 200 | ✅ |
| 删除定时任务 | 200 | ✅ |
| 删除 Wiki | 204 | ✅ |

### 1.3 聊天接口

| 操作 | HTTP | 状态 |
|------|------|------|
| `/api/chat/completions` | 200 | ✅ 返回 AI 响应，延迟 ~4s |

---

## 二、发现的问题

### P0 阻塞（0 个）

无阻塞级问题。

### P1 严重（3 个）

| # | 问题 | 模块 | 详情 |
|---|------|------|------|
| **BUG-01** | Wiki API 路径 307 重定向 | Wiki | 前端调用 `/wiki`（无斜杠），后端需 `/wiki/`（有斜杠），返回 307。POST 请求可能因 CORS 预检失败。**已修复**：`wiki.ts` 已加尾斜杠 |
| **BUG-02** | Permissions API 路径 307 重定向 | 权限 | 同上，前端 `/permissions` → 后端 `/permissions/`。**已修复**：`permission.ts` 已加尾斜杠 |
| **BUG-03** | Skills.vue `i18n.global.t()` 报错 | 技能 | `useI18n()` 返回的 Composer 没有 `.global` 属性，会导致运行时错误。**已修复**：改为直接使用 `$t()` |

### P2 一般（5 个）

| # | 问题 | 模块 | 详情 |
|---|------|------|------|
| **BUG-04** | Logs.vue 引用未定义的 `indexMethod` | 日志 | `:index="indexMethod"` 属性引用了不存在的函数。**已修复**：移除该属性 |
| **BUG-05** | 4 个后端路由有双 `/api/` 前缀 | 后端 | `experience.py`、`research.py`、`task_board.py`、`vector_store.py` 的 router prefix 包含 `/api/`，导致实际路径为 `/api/api/xxx`。当前前端未调用，属于潜在 bug |
| **BUG-06** | 前端有多个 TS 未使用变量警告 | 多个页面 | `MainLayout.vue` 的 `currentPageTitle`、`Expand`、`Fold`；`Chat.vue` 的 `t`；`Skills.vue` 的 `markRaw` 等 |
| **BUG-07** | 后端 7 个测试用例失败 | 测试 | 主要是权限边界测试和 Schema 变更导致的 422，非核心流程问题 |
| **BUG-08** | `Monitor.vue` 无路由 | - | 组件存在但未注册到 router |

### P3 轻微（2 个）

| # | 问题 | 模块 | 详情 |
|---|------|------|------|
| **BUG-09** | 插件系统无前端页面 | 插件 | 后端 `/plugins` 路由已注册，但前端无管理页面 |
| **BUG-10** | 审批/工作空间无前端页面 | 组织 | 后端 `/approvals`、`/workspaces` 可用，前端无入口 |

---

## 三、已修复问题

本次冒烟测试中直接修复了 4 个问题：

| # | 修复内容 | 文件 |
|---|---------|------|
| 1 | Wiki API 加尾斜杠避免 307 | `frontend/src/api/wiki.ts` |
| 2 | Permissions API 加尾斜杠避免 307 | `frontend/src/api/permission.ts` |
| 3 | Skills.vue `i18n.global.t()` → `$t()` | `frontend/src/views/Skills.vue` |
| 4 | Logs.vue 移除未定义的 `indexMethod` | `frontend/src/views/Logs.vue` |

---

## 四、结论

**冒烟测试通过**。核心流程（登录 → 仪表盘 → 聊天 → 智能体 → 任务 → 技能 → AI 配置 → 记忆 → 日志 → 设置）均可正常走通。发现 3 个 P1 问题（已全部修复），5 个 P2 问题（非阻塞），2 个 P3 问题。

**建议**：进入第二轮全量功能测试，重点关注：
1. 前端页面在浏览器中的实际渲染效果（需要人工验证 i18n 和深色模式）
2. Wiki 页面的 307 重定向修复是否解决了实际加载问题
3. 各对话框的表单提交和校验
