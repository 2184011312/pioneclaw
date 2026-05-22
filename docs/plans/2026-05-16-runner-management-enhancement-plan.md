# Runner 管理增强 — 实施计划

> **For implementer:** TDD throughout. Write failing test first. Watch it fail. Then implement.

**Goal:** 补齐 PioneClaw Runner 模块的用户绑定、Token轮换、诊断日志、版本管理、前端Tab改造

**Architecture:** 在现有 Runner 模块（13 API + Runners.vue 1116行）基础上增量补齐，不动已有端点。新增 2 个模型 + 15 个 API + 4 个前端 Tab

**Tech Stack:** FastAPI + SQLAlchemy 2.0 + Pydantic + Vue 3 + TypeScript + Element Plus

---

## 任务依赖图

```
T1 模型 → T2 绑定API → T3 绑定测试通过
                    → T4 Token轮换API → T5 Token测试通过
T1 模型 → T6 诊断API → T7 诊断测试通过
T1 模型 → T8 版本模型+API → T9 版本测试通过
                                         → T10 前端改造
```

---

### Task 1: 数据模型层

**Files:**
- Modify: `backend/app/models/models.py` — Runner/User 增加字段
- Create: `backend/app/models/runner_release.py` — RunnerRelease 模型
- Create: `backend/app/models/connection_event.py` — ConnectionEvent 模型
- Modify: `backend/app/models/__init__.py` — 导出新模型
- Create: `backend/app/schemas/runner_schemas.py` — 新 Pydantic Schema
- Modify: `backend/app/schemas/__init__.py` — 导出新 Schema

**Implementation:**

1. Runner 模型增加 3 个字段：
```python
token_rotated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
diagnostics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
```

2. User 模型增加 1 个字段：
```python
default_runner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("runners.id"), nullable=True)
```

3. RunnerRelease 模型（字段见设计文档 Section 2）

4. ConnectionEvent 模型（字段见设计文档 Section 2）

5. Schema：BindUserRequest, UnbindUserRequest, RotateTokenResponse, DiagnosticsResponse, LocalLogQuery, ConnectionEventResponse, RunnerReleaseCreate, RunnerReleaseResponse

**Verify:** `from app.models import Runner, User, RunnerRelease, ConnectionEvent` 无 ImportError

---

### Task 2: 用户绑定 API

**Files:**
- Modify: `backend/app/api/runners.py` — 增加 4 个绑定端点
- Create: `backend/tests/test_runner_binding.py`

**Endpoints:**
1. `POST /runners/{id}/bind-user` — 将 Runner.user_id 设为指定用户，需管理员权限
2. `DELETE /runners/{id}/unbind-user` — 清除 Runner.user_id，需管理员权限
3. `GET /runners/my-bindings` — 查询当前用户的所有 Runner（WHERE user_id = current_user.id）
4. `PUT /runners/my-default` — 设置 User.default_runner_id

**Tests (~12):**
- bind-user 成功绑定
- bind-user 重复绑定到已有用户的 Runner → 400
- bind-user 无权限 → 403
- unbind-user 成功解绑
- my-bindings 返回当前用户的 Runner 列表
- my-bindings 不含其他用户的 Runner
- my-default 设置成功
- my-default 设置不存在的 Runner → 404
- my-default 设置别人的 Runner → 403
- 边界：绑定不存在的 Runner → 404
- 边界：绑定不存在的用户 → 404

---

### Task 3: Token 安全轮换 API

**Files:**
- Modify: `backend/app/api/runners.py` — 增加 rotate-token 端点
- Create: `backend/tests/test_runner_token.py`

**Implementation:**
- `POST /runners/{id}/rotate-token`：
  1. 生成新 api_key（`secrets.token_urlsafe(32)`）
  2. Fernet 加密存储
  3. 记录 `token_rotated_at = now`
  4. 设置 `token_expires_at = now + 24h`（旧 token 过渡期）
  5. 返回新 token（仅此一次，不存明文）

**Tests (~8):**
- rotate-token 成功，返回新 token
- 旧 token 在过渡期内仍可通过认证
- 过渡期后旧 token 失效
- 无权限 → 403
- Runner 不存在 → 404
- 连续两次轮换，第一次的旧 token 按各自过渡期计算

---

### Task 4: Runner 诊断与日志 API

**Files:**
- Modify: `backend/app/api/runners.py` — 增加诊断/日志端点
- Create: `backend/tests/test_runner_diagnostics.py`

**Endpoints:**
1. `GET /runners/{id}/diagnostics` — 返回最新诊断快照（从 Runner.diagnostics JSON 读取）
2. `GET /runners/{id}/local-logs` — 查询参数：category, start_time, end_time, limit。模拟返回日志行列表
3. `GET /runners/{id}/local-logs/categories` — 返回可用分类列表（agent/task/system/error）
4. `GET /runners/{id}/connection-events` — 查询 ConnectionEvent 表，按时间倒序

**Notes:**
- 诊断数据实际由 Runner 心跳上报填充到 `Runner.diagnostics` JSON 字段
- 本地日志读取在 v1 中返回模拟数据，真实实现依赖 Runner 端支持
- ConnectionEvent 在心跳处理中自动写入（online/offline/heartbeat_fail）

**Tests (~10):**
- diagnostics 返回诊断快照
- diagnostics 无数据时返回空对象
- local-logs 按分类过滤
- local-logs 按时间范围过滤
- local-logs/categories 返回分类列表
- connection-events 返回事件列表
- connection-events 按时间倒序
- 心跳更新时自动写入 online 事件
- 离线时自动写入 offline 事件

---

### Task 5: 版本管理 API

**Files:**
- Create: `backend/app/api/runner_releases.py` — 版本管理 6 个端点
- Modify: `backend/app/api/__init__.py` — 注册 router
- Create: `backend/tests/test_runner_releases.py`

**Endpoints:**
1. `GET /runner-releases/latest` — 按平台分组返回最新版本
2. `GET /runner-releases/versions` — 全部版本列表，按 created_at 倒序
3. `GET /runner-releases/download/{version}/{filename}` — FileResponse 返回安装包
4. `POST /runner-releases/upload` — multipart 上传，计算 SHA256，存储到 workspace/releases/
5. `DELETE /runner-releases/versions/{version}` — 删除版本及文件（仅超管）
6. `POST /runner-releases/versions/{version}/set-latest` — 先清除同平台旧 latest，再设置新 latest（仅超管）

**Tests (~10):**
- upload 成功，自动计算 checksum
- upload 非超管 → 403
- latest 返回各平台最新版本
- versions 列表按时间倒序
- download 成功返回文件
- download 不存在的版本 → 404
- set-latest 成功，旧 latest 被清除
- set-latest 非超管 → 403
- delete 成功删除版本和文件
- delete 非超管 → 403

---

### Task 6: 前端 Tab 改造

**Files:**
- Modify: `frontend/src/views/Runners.vue` — Tab 式布局改造
- Modify: `frontend/src/api/runners.ts` — 新增 API 调用函数
- Create: `frontend/src/tests/runner.test.ts` — 前端测试

**改造内容:**
1. 顶部保留统计卡片
2. 下方改为 `<el-tabs>` 4 个 Tab：
   - **Tab 1 "Runner 列表"**：现有表格 + 每行增加绑定/解绑/轮换Token/诊断按钮
   - **Tab 2 "诊断面板"**（仅管理员）：Runner 选择器 + CPU/内存/磁盘进度条 + 进程列表 + 连接事件时间线
   - **Tab 3 "版本管理"**（仅超管）：版本列表 + 上传区 + set-latest/delete 操作
   - **Tab 4 "我的 Runner"**（普通用户）：绑定列表 + 设默认操作
3. 新增 API 函数：bindUser, unbindUser, getMyBindings, setDefaultRunner, rotateToken, getDiagnostics, getLocalLogs, getConnectionEvents, uploadRelease, getReleases, getLatestRelease, downloadRelease, setLatestRelease, deleteRelease

**Tests (~8):**
- 4 个 Tab 正常渲染
- Tab 权限控制（普通用户看不到 Tab 2/Tab 3）
- 绑定弹窗用户选择器正常
- 版本上传表单验证
- my-bindings 列表渲染
- 设默认按钮触发 API 调用
- Token 轮换确认弹窗
- 空状态显示

---

### Task 7: 集成回归测试

**Files:**
- Modify: 运行全部现有测试确认无回归

**Command:** `cd backend && python -m pytest tests/ -x -q --tb=short`
**Expected:** 所有已有测试通过，新增测试通过，总测试数增加 ~48

---

## 文件变更总览

| 操作 | 文件 |
|------|------|
| 新建 | `backend/app/models/runner_release.py` |
| 新建 | `backend/app/models/connection_event.py` |
| 新建 | `backend/app/schemas/runner_schemas.py` |
| 新建 | `backend/app/api/runner_releases.py` |
| 新建 | `backend/tests/test_runner_binding.py` |
| 新建 | `backend/tests/test_runner_token.py` |
| 新建 | `backend/tests/test_runner_diagnostics.py` |
| 新建 | `backend/tests/test_runner_releases.py` |
| 新建 | `frontend/src/tests/runner.test.ts` |
| 修改 | `backend/app/models/models.py` |
| 修改 | `backend/app/models/__init__.py` |
| 修改 | `backend/app/schemas/__init__.py` |
| 修改 | `backend/app/api/runners.py` |
| 修改 | `backend/app/api/__init__.py` |
| 修改 | `frontend/src/views/Runners.vue` |
| 修改 | `frontend/src/api/runners.ts` |
