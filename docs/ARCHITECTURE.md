# PioneClaw 架构文档 — 1 Center + N Runner

> 2026-05-19

---

## 一、核心理念

**Center 是大脑，Runner 是手**。

- **Center**：Web 管理平台，运行在服务器上。用户通过浏览器访问 Center，对话、管理、调度任务。
- **Runner**：后台守护进程，安装在员工电脑上。接收 Center 指令，在本地执行文件操作和命令。

```
┌──────────────────────────────────────────────────────┐
│                    浏览器                              │
│              http://center:5173                       │
│                对话 / 管理 / 监控                       │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│                  Center (大脑)                         │
│              服务器 :20005                            │
│  ┌─────────┬──────────┬──────────┬────────────────┐  │
│  │ AI Agent│ 任务系统  │ Wiki 知识库│ 会话管理       │  │
│  ├─────────┼──────────┼──────────┼────────────────┤  │
│  │ 技能系统 │ 权限RBAC │ 多租户组织 │ 监控+日志      │  │
│  └─────────┴──────────┴──────────┴────────────────┘  │
│                                                      │
│  Runner 管理: 注册→审批→绑定→指令下发→诊断            │
└──┬──────────┬──────────┬─────────────────────────────┘
   │          │          │
   ▼          ▼          ▼
┌──────┐ ┌──────┐ ┌──────┐
│Runner│ │Runner│ │Runner│  ← 安装在员工电脑上 (手)
│张三PC │ │李四PC │ │服务器 │
│:20006│ │:20006│ │:20006│
└──────┘ └──────┘ └──────┘
```

---

## 二、Center

### 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python + FastAPI + SQLAlchemy 2.0 |
| 前端 | Vue 3 + TypeScript + Element Plus |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |
| 认证 | JWT Bearer + Refresh Token (HttpOnly) |

### 核心模块

| 模块 | 功能 |
|------|------|
| **AI Agent** | ReAct 推理循环，43+ 内置工具，支持 DeepSeek/OpenAI/Anthropic |
| **Runner 管理** | 注册审批、绑定用户、Token 轮换、在线诊断、版本管理 |
| **任务系统** | 创建/指派/审批/AI执行、模板、依赖、进度、附件 |
| **Wiki 知识库** | 空间体系、文档操作、版本管理、审批流程 |
| **会话管理** | 多会话并行、消息持久化、WebSocket 实时通信 |
| **权限 RBAC** | 三级角色(超管/组织管理员/普通用户)、权限树、角色分配 |
| **多租户** | 组织架构树、Workspace、三级 Skill 范围 |
| **安全系统** | 密码复杂度、登录锁定、RateLimit、SSRF 防护、Bash 沙箱 |

### Runner 管理 API（28+ 端点）

```
Runner CRUD:      注册 / 审批 / 更新 / 删除
用户绑定:         bind-user / unbind-user / my-bindings / my-default  
安全机制:         rotate-token (Fernet加密 + 24h过渡期)
诊断监控:         diagnostics / logs / connection-events
版本管理:         upload / download / versions / set-latest
指令通道:         send-instruction / pending / result
```

---

## 三、Runner

### 定位

一个**无界面的后台守护进程**，安装后静默运行。用户通过 Center 下达指令，Runner 在本地执行。

### 技术栈

| 项 | 选择 |
|----|------|
| 语言 | Python 3.10+ |
| 通信 | HTTP (注册/心跳) + 轮询 (指令) |
| 打包 | PyInstaller → 单文件 exe |
| 安全 | 路径沙箱、危险命令黑名单、系统目录保护 |

### 生命周期

```
安装 → 首次设置(输入Center地址+登录/注册)
  → POST /runners/apply → 状态: pending
    → 管理员审批 → 状态: online
      → 心跳循环(每30s) + 指令轮询(每5s)
        → Ctrl+C → 通知Center离线 → 退出
```

### 执行器

| 操作 | 说明 |
|------|------|
| file_read | 读取本地文件 |
| file_write | 写入本地文件 |
| file_delete | 删除文件/目录 |
| file_browse | 浏览目录结构 |
| exec | 执行终端命令 |

所有操作受安全沙箱限制：禁止访问系统目录(C:\Windows等)、禁止执行危险命令(rm -rf /等)。

### 目录结构

```
D:\pioneclaw-runner\
├── main.py              # 入口
├── runner.py            # 主控逻辑
├── center_client.py     # Center 通信
├── executor.py          # 文件+命令执行
├── config.py            # 配置持久化
└── config.json           # 自动生成(runner_id, token)
```

---

## 四、通信协议

### HTTP

```
Runner → Center:
  POST /auth/login         → 登录获取 JWT
  POST /auth/register      → 注册新用户
  POST /runners/apply      → 注册 Runner
  POST /runners/{id}/heartbeat  → 心跳上报
  GET  /runners/{id}/pending    → 轮询指令
  POST /runners/{id}/result     → 上报结果

Center → Runner (通过指令队列):
  POST /runners/{id}/instruction  → 下发指令
```

### 指令格式

```
Center → Runner:
{
  "task_id": "a1b2c3d4",
  "action": "file_read" | "file_write" | "file_browse" | "exec",
  "params": {"path": "C:\\Users\\xxx\\file.txt"}
}

Runner → Center:
{
  "task_id": "a1b2c3d4",
  "success": true,
  "data": "文件内容..."
}
```

---

## 五、Agent × Runner 集成

Agent 对话时自动调用 Runner 执行本地操作：

```
用户对话 "帮我整理桌面文件"
  → Agent 调用 runner_file_browse("~/Desktop")
    → Center 查用户默认 Runner
      → 指令入队 → Runner 轮询拿到 → 本地执行
        → 结果回报 → Agent 继续处理 → 回复用户
```

4 个 Runner 工具：`runner_file_read` / `runner_file_write` / `runner_file_browse` / `runner_exec`

---

## 六、安全体系

### 6.1 认证与授权

| 机制 | 实现 |
|------|------|
| **双 Token** | Access Token (7天) + Refresh Token (30天, HttpOnly Cookie) |
| **JWT 签名** | HS256 + 独立密钥(ACCESS/REFRESH/RESET 三套) |
| **密码策略** | ≥8位 + 大写 + 小写 + 数字 + 特殊字符 |
| **登录保护** | 5次失败锁定30分钟 + RateLimit (10次/分钟) |
| **本地直通** | 127.0.0.1/localhost 免认证（开发模式） |
| **Swagger 保护** | 非 DEBUG 模式下 /docs /openapi.json 需认证 |

### 6.2 权限 RBAC

```
超级管理员 → 所有权限
组织管理员 → 管理本组织用户/资源
普通用户  → 自己的数据 + 对话
```

| 能力 | 实现 |
|------|------|
| **三级角色** | super_admin / org_admin / user |
| **权限树** | 模块级(dashboard, chat, agent...) × 操作级(view, create, edit, delete...) |
| **角色分配** | PUT /roles/user/{id} + 前端 Users 页面 |
| **权限设置** | PUT /roles/{id}/set-permissions + 前端 Roles 页面 |
| **数据隔离** | 用户只能看自己的会话/任务/Runner |

### 6.3 执行安全

| 层级 | 机制 | 说明 |
|------|------|------|
| **Bash 安全分析** | 4级危险分级 (SAFE/CAUTION/DANGEROUS/BLOCKED) | 57+ 正则规则，14 类别 |
| **SSRF 防护** | 预 DNS 阻止 + IP 范围检查 | 阻止 localhost/.local/.internal、RFC1918、云 metadata |
| **路径沙箱** | 读写分层确认 | 读文件需确认，写文件硬拦截敏感路径 |
| **敏感文件检测** | 20 个模式 | .env、.pem、.key、id_rsa、credentials 等 |
| **权限模式** | 5 级 PermissionMode | ReadOnly < WorkspaceWrite < DangerFullAccess < Prompt < Allow |
| **输出验证** | Guardrails | LLM + 函数双重验证，自动重试，失败策略 |

### 6.4 Runner 侧安全

| 机制 | 说明 |
|------|------|
| **路径沙箱** | 默认限制在用户目录，禁止访问 C:\Windows、/etc、/System 等系统路径 |
| **命令黑名单** | rm -rf /、format、shutdown、kill、fork bomb 等硬拦截 |
| **Token 加密** | Runner api_key 用 Fernet AES-128-CBC 加密存储 |
| **Token 轮换** | 支持 rotate-token，24h 过渡期，旧 Token 逐步失效 |
| **审批机制** | Runner 注册后需管理员审批才能上线 |

### 6.5 数据安全

| 机制 | 说明 |
|------|------|
| **API Key 加密** | 所有 LLM API Key 用 Fernet 加密存储，返回脱敏(••••••••) |
| **审计日志** | JSONL 格式，按日期滚动，自动脱敏密钥 |
| **提示词注入防御** | 系统提示词明确禁止执行网页/搜索结果中的指令性文本 |
| **加密存储** | EncryptedString 类型，数据库存密文 |
| **反幻觉规则** | 8 条强制规则：禁止虚构工具调用结果、禁止编造文件内容 |

### 6.6 资源防御

| 机制 | 说明 |
|------|------|
| **RateLimit** | 令牌桶算法，登录/注册/改密等敏感端点限流 |
| **并发控制** | 每用户最大 3 并发，全局最大 20，超配额排队 |
| **WebFetch 安全** | SSRF 防护 + 内容大小上限 50KB + 域名白名单 |
| **安全头** | X-Content-Type-Options、HSTS、CSP 等 |
| **CORS** | 配置允许源白名单 |
| **请求体限制** | 上传文件 200MB 上限 + SHA256 校验 |

---

## 七、部署场景

```
场景1: 开发者单机
  Center + Runner 都在同一台机器
  对话 → Agent → Runner(本机) → 操作本地文件

场景2: 小团队
  Center 在服务器
  每个员工电脑装 Runner
  管理员通过 Center 管理所有 Runner

场景3: 企业部署
  Center 集群化 + PostgreSQL
  Runner 批量部署（域推送/SCCM）
  RBAC + 审批流程完整启用
```
