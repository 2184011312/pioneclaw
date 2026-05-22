# 阶段 V：审批流程前端 - 测试方案

## 一、测试范围

### 1.1 后端 API 测试（已有）
- `backend/tests/test_phase_r.py` 中已包含部分审批测试
- 需要补充完整的审批流程测试

### 1.2 前端测试
- `frontend/tests/approvals.test.ts` — 审批页面单元测试
- 嵌入到 `Tasks.vue` 的审批 Tab 测试

---

## 二、后端测试用例

### 2.1 Approval API 测试 (`test_approvals.py`)

| # | 测试用例 | 描述 | 预期结果 |
|---|---------|------|---------|
| 1 | `test_create_approval_skill` | 提交 Skill 共享审批 | 201 Created |
| 2 | `test_create_approval_skill_not_owner` | 非创建者提交审批 | 403 Forbidden |
| 3 | `test_create_approval_skill_wrong_scope` | 已是组织级的 Skill 提交为组织级 | 400 Bad Request |
| 4 | `test_create_approval_duplicate` | 重复提交相同审批 | 400 Bad Request |
| 5 | `test_list_approvals_as_user` | 普通用户查看审批列表 | 只看到自己提交的 |
| 6 | `test_list_approvals_as_org_admin` | 组织管理员查看审批列表 | 看到本组织的 + 自己提交的 |
| 7 | `test_list_approvals_as_super_admin` | 超管查看审批列表 | 看到所有 |
| 8 | `test_get_pending_count` | 获取待审批数量 | 返回正确数量 |
| 9 | `test_get_approval_detail` | 获取审批详情 | 返回完整信息 |
| 10 | `test_review_approve` | 批准审批 | status -> approved, skill.scope 变更 |
| 11 | `test_review_reject` | 拒绝审批 | status -> rejected |
| 12 | `test_review_no_permission` | 无权限用户审批 | 403 Forbidden |
| 13 | `test_review_already_processed` | 审批已处理的情况 | 400 Bad Request |
| 14 | `test_cancel_approval` | 取消审批 | status -> cancelled |
| 15 | `test_cancel_not_owner` | 非提交者取消审批 | 403 Forbidden |
| 16 | `test_cancel_not_pending` | 取消非待审批的请求 | 400 Bad Request |

---

## 三、前端测试用例

### 3.1 Approvals API 封装测试 (`approvalsApi.test.ts`)

| # | 测试用例 | 描述 | 预期结果 |
|---|---------|------|---------|
| 1 | `test_list_approvals` | 调用 list API | 返回审批列表 |
| 2 | `test_get_pending_count` | 调用 pending-count API | 返回数量 |
| 3 | `test_create_approval` | 调用 create API | 返回创建的审批 |
| 4 | `test_review_approval` | 调用 review API | 返回更新后的审批 |
| 5 | `test_cancel_approval` | 调用 cancel API | 返回成功消息 |

### 3.2 Tasks.vue 审批 Tab 测试 (`tasks-approval.test.ts`)

| # | 测试用例 | 描述 | 预期结果 |
|---|---------|------|---------|
| 1 | `test_render_approval_tab` | 渲染审批 Tab | Tab 可见 |
| 2 | `test_display_approvals_list` | 显示审批列表 | 列表渲染正确 |
| 3 | `test_display_pending_count` | 显示待审批数量徽章 | 数量正确 |
| 4 | `test_approve_button_visible_for_admin` | 管理员可见批准按钮 | 按钮可见 |
| 5 | `test_approve_action` | 点击批准按钮 | 调用 API，列表更新 |
| 6 | `test_reject_action` | 点击拒绝按钮 | 弹出确认框，调用 API |
| 7 | `test_cancel_action` | 点击取消按钮 | 取消自己的审批 |
| 8 | `test_filter_by_status` | 按状态筛选 | 列表正确过滤 |
| 9 | `test_approval_detail_dialog` | 点击查看详情 | 显示详情对话框 |
| 10 | `test_error_handling` | API 错误处理 | 显示错误提示 |

---

## 四、开发步骤

### 4.1 后端测试补充（0.5天）
1. 创建 `backend/tests/test_approvals.py`
2. 编写 16 个测试用例
3. 运行测试确保全部通过

### 4.2 前端开发（0.5天）
1. 创建 `frontend/src/api/approvals.ts` — API 封装
2. 修改 `frontend/src/views/Tasks.vue` — 添加审批 Tab
3. 添加 i18n 翻译
4. 编写前端单元测试

---

## 五、验收标准

- [ ] 后端审批 API 测试覆盖 > 90%
- [ ] 后端 16 个测试用例全部通过
- [ ] 前端 API 封装测试通过
- [ ] 前端 Tasks.vue 审批 Tab 测试通过
- [ ] 任务页面有"审批"标签页
- [ ] 可查看待审批/已审批列表
- [ ] 管理员可批准/拒绝审批请求
- [ ] 用户可取消自己提交的审批
