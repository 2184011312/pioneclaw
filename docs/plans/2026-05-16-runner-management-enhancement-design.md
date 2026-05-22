# Runner 管理增强 — 设计文档

> 日期：2026-05-16
> 参考：CircleBot 平台分析报告 / distributed-wandering-mitten.md
> 决策：方案 A（CircleBot 对照增量补齐），5 块 4.5 天

---

## 一、背景

PioneClaw 现有 Runner 模块包含 13 个 API 端点（注册/审批/心跳/上下线），前端 Runners.vue 1116 行。对比 CircleBot 的 Runner 管理体系，缺少：

- **Runner-用户绑定**：多对一（一个用户可有多台 Runner，一台 Runner 只归属一个用户）
- **Token 安全轮换**：API Key 定期轮换 + 过渡期机制
- **诊断与日志**：远程查看 Runner 的 CPU/内存/磁盘/进程和本地日志
- **版本管理**：Runner 安装包上传/下载/版本历史/设为最新

## 二、数据模型

### 新增模型

**RunnerRelease** — Runner 版本发布：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int PK | |
| version | str | "1.2.3" |
| filename | str | "pioneclaw-runner-1.2.3.zip" |
| file_path | str | 服务器存储路径 |
| file_size | int | 字节数 |
| checksum | str | SHA256 |
| platform | str | windows/linux/macos |
| release_notes | text? | 更新日志 |
| is_latest | bool | 是否最新版本 |
| uploaded_by | int FK users.id | 上传者 |
| created_at | datetime | |

**ConnectionEvent** — Runner 连接事件：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int PK | |
| runner_id | int FK runners.id | |
| event_type | str | online/offline/disconnect/heartbeat_fail/token_rotate |
| detail | text? | 事件详情 |
| created_at | datetime | |

### 修改现有模型

**Runner** 增加字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| token_rotated_at | datetime? | 上次 Token 轮换时间 |
| token_expires_at | datetime? | 旧 Token 过期时间（24h 过渡期） |
| diagnostics | JSON? | 最新诊断快照 |

**User** 增加字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| default_runner_id | int? FK runners.id | 用户默认 Runner |

### 绑定关系

不使用单独的绑定表。Runner 现有 `user_id` 字段承载归属关系：

```
Runner.user_id ──────> User.id        (多对一：一个用户可有多台 Runner)
User.default_runner_id ──> Runner.id  (用户默认 Runner)
```

## 三、API 端点

现有 13 个端点保持不变，新增 15 个端点，总计 28 个。

### A1：Runner-用户绑定（4 个）

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/runners/{id}/bind-user` | 组织管理员+ | body: {user_id} → 设置 Runner.user_id |
| DELETE | `/runners/{id}/unbind-user` | 组织管理员+ | 清除 Runner.user_id |
| GET | `/runners/my-bindings` | 用户 | 当前用户绑定的所有 Runner |
| PUT | `/runners/my-default` | 用户 | body: {runner_id} → 设置 User.default_runner_id |

### A2：Token 安全轮换（1 个）

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/runners/{id}/rotate-token` | 组织管理员+ | 生成新 api_key（Fernet 加密），记录 rotated_at，旧 token 24h 过渡期仍可用 |

### A3：Runner 诊断+日志（4 个）

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/runners/{id}/diagnostics` | 组织管理员+ | 返回 CPU/内存/磁盘/进程信息快照 |
| GET | `/runners/{id}/local-logs` | 组织管理员+ | 按分类/时间范围查询 Runner 本地日志 |
| GET | `/runners/{id}/local-logs/categories` | 组织管理员+ | 可用日志分类列表 |
| GET | `/runners/{id}/connection-events` | 组织管理员+ | 连接事件历史 |

### A4：Runner 版本管理（6 个）

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/runner-releases/latest` | 用户 | 各平台最新版本 |
| GET | `/runner-releases/versions` | 用户 | 版本历史列表 |
| GET | `/runner-releases/download/{version}/{filename}` | 用户 | 下载安装包 |
| POST | `/runner-releases/upload` | 超管 | 上传新版本（multipart） |
| DELETE | `/runner-releases/versions/{version}` | 超管 | 删除版本 |
| POST | `/runner-releases/versions/{version}/set-latest` | 超管 | 设为最新 |

## 四、前端设计

在现有 `Runners.vue`（1116 行）内改为 Tab 式布局，4 个 Tab：

### Tab 1：Runner 列表（现有功能增强）
- 保持现有表格和统计卡片
- 每行增加操作按钮：绑定/解绑/轮换 Token/诊断

### Tab 2：诊断面板（新增）
- 上半部分：CPU/内存/磁盘使用率进度条
- 下半部分：进程列表 + 连接事件时间线
- 顶栏：Runner 下拉选择器

### Tab 3：版本管理（新增，仅超管可见）
- 左侧版本列表：版本号/平台/日期/是否 latest
- 右侧上传区：拖拽上传 + 版本号 + 更新日志
- 操作按钮：设为最新 / 删除

### Tab 4：我的 Runner（新增，普通用户可见）
- 已绑定 Runner 列表
- 操作：设默认 / 查看详情

## 五、测试计划

| 模块 | 测试文件 | 估 |
|------|---------|------|
| 用户绑定 | `test_runner_binding.py` — bind/unbind/my-bindings/default（~12） | ~12 |
| Token 轮换 | `test_runner_token.py` — rotate/旧token可用/过渡期后失效（~8） | ~8 |
| 诊断日志 | `test_runner_diagnostics.py` — 诊断快照/日志查询/分类/连接事件（~10） | ~10 |
| 版本管理 | `test_runner_releases.py` — 上传/下载/列表/latest/删除/权限（~10） | ~10 |
| 前端 | `runner.test.ts` — Tab切换/绑定弹窗/版本上传（~8） | ~8 |

**TDD：先写测试→失败→实现→通过**

## 六、实施顺序

```
A1 用户绑定 (1天) → A2 Token轮换 (0.5天) → A3 诊断日志 (1天)
                                            ↘ A4 版本管理 (1天) → A5 前端 (1天)
```

- A1→A2 顺序执行（A2 依赖绑定关系）
- A3 和 A4 可并行
- A5 前端在所有后端 API 完成后统一改造

## 七、涉及文件

### 新建
- `backend/app/models/runner_release.py` — RunnerRelease 模型
- `backend/app/models/connection_event.py` — ConnectionEvent 模型
- `backend/app/schemas/runner_schemas.py` — 新增 Schema
- `backend/app/api/runner_releases.py` — 版本管理 API
- `backend/tests/test_runner_binding.py`
- `backend/tests/test_runner_token.py`
- `backend/tests/test_runner_diagnostics.py`
- `backend/tests/test_runner_releases.py`
- `frontend/src/tests/runner.test.ts`

### 修改
- `backend/app/models/models.py` — Runner/User 增加字段
- `backend/app/models/__init__.py` — 导出新模型
- `backend/app/schemas/__init__.py` — 导出新 Schema
- `backend/app/api/runners.py` — 增加绑定/Token/诊断端点
- `backend/app/api/__init__.py` — 注册 runner_releases router
- `frontend/src/views/Runners.vue` — Tab 式改造
- `frontend/src/api/runners.ts` — 新 API 调用函数
