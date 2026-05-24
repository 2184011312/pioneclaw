# 上下文压缩机制

PioneClaw 的上下文压缩系统借鉴 Claude Code 的"渐进式压缩阶梯"设计，在 ReAct 循环中逐层释放 context 空间，避免对话历史无限增长导致模型上下文溢出。

---

## 1. 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                     AgentLoop.process_message                │
│                         (每轮 LLM 调用前)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  ContextCompressionService.auto_prune()                     │
│  ├── Layer 1: Snip (零成本)                                  │
│  │   └── 移除空消息、截断超长 reasoning_content               │
│  ├── Layer 2: MicroCompacter (低成本)                        │
│  │   └── 旧工具结果替换为占位符，保留最近 N 个                │
│  ├── Layer 3: ContextCollapse (轻量预压缩，caution 触发)     │
│  │   └── 合并相邻 system 消息、截断超长 tool_result          │
│  └── Layer 4: Compactor (高成本，critical/block 触发)       │
│      └── LLM 生成摘要，替换旧消息为 summary + 最近消息        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Autocompact 时间触发（距上次 assistant > 5 分钟）            │
│  └── 强化 MicroCompact：保留最近 3 个，截断阈值更低           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  手动压缩 (Web UI / /compact 命令)                           │
│  ├── ContextCompressionService.manual_compact(force=True)   │
│  ├── 返回压缩后的消息列表 (替换前端会话)                      │
│  └── 可选: session_id 持久化到数据库                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  应急处理 (prompt_too_long)                                  │
│  └── ContextCompressionService.emergency_compact()          │
│      └── L1 强化 MicroCompact → L2 剥离内容                │
│          → L3 丢弃旧消息 → L4 激进丢弃 → L5 最终防线       │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 五层压缩详解

### Layer 1: Snip（零成本）

**文件**: `app/modules/agent/context_pruner.py::Snip`

在每次 LLM 调用前执行，不调用 LLM，纯文本操作：

| 操作 | 说明 |
|------|------|
| 移除空 system 消息 | `content` 为空或纯空格 |
| 移除空 assistant 消息 | `content` 为空且无 `tool_calls` |
| 截断超长 reasoning_content | 默认最多保留 2000 字符，尾部加 `...[truncated]` |
| 返回新列表 | 不修改原列表（`copy.deepcopy`） |

**触发**: 所有状态（`normal` 及以上）

**配置参数**:
```python
Snip(max_reasoning_chars=2000)
```

### Layer 2: MicroCompacter（低成本）

**文件**: `app/modules/agent/context_pruner.py::MicroCompacter`

清除旧工具结果内容以释放空间：

| 策略 | 说明 |
|------|------|
| 计数触发 | 保留最近 `keep_recent` 个工具结果，更早的替换为占位符 |
| 大小触发 | 单个工具结果超过 `max_chars` 时截断尾部 |
| 结构化占位符 | `[tool_result: {tool_name}, content cleared]`，保留工具名等元信息 |
| 负收益保护 | 占位符比原内容长时跳过替换 |
| 白名单 | 只压缩 `read_file`, `write_file`, `edit_file`, `grep`, `glob`, `file_search`, `exec`, `bash`, `web_search`, `web_fetch`, `browser` |

**触发**: `warning` 及以上，或 Autocompact 时间触发

**配置参数**:
```python
MicroCompacter(keep_recent=8, max_chars=4000)
```

> **注意**: AgentLoop 追加 tool result 时必须包含 `tool_name` 字段，否则 MicroCompacter 无法识别。见 `loop.py` 中所有 `"role": "tool"` 的消息构造。

### Layer 3: ContextCollapse（轻量预压缩）

**文件**: `app/modules/agent/context_collapse.py::ContextCollapser`

零 LLM 成本的预压缩层，在 `caution` 状态触发：

| 操作 | 说明 |
|------|------|
| 合并相邻 system 注入消息 | Agent 间消息、上下文恢复消息合并为一条 |
| 截断超长 tool_result | 截断阈值降至 2000 字符 |
| 去除冗余 tool_calls 元信息 | 截断过长的 description |

**触发**: `caution` 及以上

**配置参数**:
```python
ContextCollapser(max_tool_result_chars=2000, max_system_merge_chars=4000)
```

### Layer 4: Compactor（高成本，阈值触发）

**文件**: `app/modules/agent/compactor.py::Compactor`

当 token 数超过阈值时，使用 LLM 生成对话摘要，替换旧消息：

**触发条件**:
```python
TokenBudget(context_window=200_000)
# compact_threshold = 200_000 - 20_000(output) - 13_000(buffer) = 167_000
```

**分级触发**:

| 状态 | 触发层 | Compactor 行为 |
|------|--------|---------------|
| `normal` | L1 Snip | 不触发 |
| `warning` | L1 + L2 | 不触发 |
| `caution` | L1 + L2 + L3 | 不触发 |
| `critical` | L1 + L2 + L3 + L4 | 正常摘要 |
| `block` | L1 + L2 + L3 + L4(激进) | 强制摘要，更短 |

**压缩流程**:
1. `_split_messages()` — 分割为"要总结的"和"要保留的"（保留最近 8 条）
2. `_format_messages()` — 格式化消息为文本，多模态内容替换为 `[image]` / `[document]`
3. `_generate_summary()` — 调用 LLM 生成摘要
4. `_rebuild_after_compact()` — 重建消息列表：`system + summary + recent + restored_files`

**保护机制**:
- **空摘要保护**: 摘要为空时不丢弃历史，返回原消息
- **熔断器**: 连续 3 次失败后停止尝试，避免浪费 API 调用
- **force 参数**: `manual_compact()` 设置 `force=True` 绕过阈值检查

**配置参数**:
```python
CompactionConfig(
    context_window=200_000,      # 从模型配置读取（委托 TokenBudget）
    buffer_tokens=33_000,        # 输出预留 + 安全缓冲（未注入 TokenBudget 时回退）
    message_threshold=200,       # 消息数兜底阈值
    keep_recent_messages=8,      # 压缩后保留最近 N 条
    generate_memory=False,       # 是否提取记忆条目
    token_budget=None,           # 外部 TokenBudget（统一阈值时注入）
)
```

---

## 3. Autocompact 时间触发

**文件**: `app/modules/agent/compression_service.py::ContextCompressionService`

当用户长时间离开（> 5 分钟）后回归对话时，自动执行强化 MicroCompact：

| 参数 | 值 | 说明 |
|------|-----|------|
| 触发间隔 | 300 秒（5 分钟） | 距上次 assistant 响应时间 |
| 保留工具结果 | 3 个 | 比正常模式（8 个）更激进 |
| 截断阈值 | 2000 字符 | 比正常模式（4000）更低 |

**实现**:
- `mark_assistant_response()` 在每次 assistant 响应后记录时间戳
- `auto_prune()` 每轮检查时间戳，超时则触发强化模式

---

## 4. Token 预算与阈值

**文件**: `app/modules/agent/token_budget.py::TokenBudget`

```python
@dataclass
class TokenBudget:
    context_window: int
    max_output_tokens: int = 20_000
    safety_buffer: int = 13_000

    @property
    def effective_window(self) -> int:
        return self.context_window - self.max_output_tokens

    @property
    def compact_threshold(self) -> int:
        return self.effective_window - self.safety_buffer

    @property
    def warning_threshold(self) -> int:
        return self.compact_threshold - 20_000

    @property
    def hard_block_threshold(self) -> int:
        return self.effective_window - 3_000
```

**不同窗口下的阈值**:

| 模型窗口 | compact_threshold | warning_threshold | hard_block_threshold |
|----------|-------------------|-------------------|----------------------|
| 200K | 167,000 | 147,000 | 177,000 |
| 128K | 95,000 | 75,000 | 105,000 |
| 256K | 223,000 | 203,000 | 233,000 |
| 16K | 10,000 (auto-scale) | 6,000 | 11,000 |
| 8K | 4,000 (auto-scale) | 0 | 5,000 |

**小上下文保护**: 当 `context_window <= max_output_tokens + safety_buffer` 时，buffer 自动缩放到窗口的 10%，避免阈值变负数。

**Token 用量估算** (`ContextCompressionService.estimate_or_read_usage`):
- 优先使用 `provider.last_input_tokens`（API 真实值）
- 若不可用或字符估算更大，回退到 `estimate_tokens(messages)`（中文 1.5 char/token，英文 4 char/token）
- 返回 `TokenUsage(source="api"|"estimated")`

---

## 5. Reactive Compact（截断续传 + 应急恢复）

**文件**: `app/modules/agent/loop.py::AgentLoop`

### 截断自动续传

当 LLM 输出因 `max_tokens` 限制被截断（`finish_reason="length"`）时，自动追加续传请求：

| 参数 | 值 |
|------|-----|
| 最大续传次数 | 3 次 |
| 续传提示 | `"[系统提示：你的上一条回复因长度限制被截断，请从断点处继续完成输出]"` |
| 体验 | 用户无感知，看到完整输出 |

### prompt_too_long 5 级恢复

```
L1: 强化 MicroCompact（保留最近 3 个工具结果）
L2: 截断所有工具结果到最小元信息
L3: 丢弃旧消息（保留 system + 最近 5 条）
L4: 激进丢弃（保留 system + 最近 user 消息）
L5: 最终防线（只保留 system prompt，提示用户历史已清空）
```

每级尝试后重新调用 LLM，成功则停止，失败则升级到下一级。

---

## 6. AgentLoop 集成

**文件**: `app/modules/agent/loop.py::AgentLoop`

### 统一阈值系统

`TokenBudget` 由 `AgentLoop.__init__` 统一创建，注入到 `CompressionService` 和 `Compactor.config`：

```python
self._token_budget = TokenBudget(
    context_window=resolved_context_window,
    max_output_tokens=self.max_tokens,
)
# 注入统一预算
if self._compression_service:
    self._compression_service.budget = self._token_budget
if self._compactor and self._compactor.config:
    self._compactor.config.token_budget = self._token_budget
```

### 自动压缩（每轮 LLM 调用前）

```python
# 在 process_message 的 while 循环中
messages = await self._prune_context(messages, iteration)
```

`_prune_context()` 优先使用 `ContextCompressionService`，未注入时回退到直接调用组件。

### 工具执行后跟踪文件访问

```python
# 每次 read_file/write_file/edit_file 执行后
self._track_file_access(tc_name, tc_args, result, tc_id)
```

记录到 `FileTracker`，压缩后通过 `_rebuild_after_compact()` 恢复关键文件内容。

### Autocompact 时间戳

```python
# 每次 assistant 响应后标记时间
if self._compression_service:
    self._compression_service.mark_assistant_response()
```

---

## 7. 上下文可视化

**文件**: `frontend/src/views/Chat.vue`

### SSE done 事件

后端在 `done` 事件中返回完整 `context_report`：
```json
{
  "type": "done",
  "context_report": {
    "total_messages": 42,
    "input_tokens": 128000,
    "output_tokens": 2048,
    "usage_percent": 64,
    "status": "normal",
    "role_distribution": {
      "system": {"count": 3, "tokens": 1200},
      "user": {"count": 10, "tokens": 800},
      "assistant": {"count": 10, "tokens": 5000},
      "tool": {"count": 19, "tokens": 121000}
    },
    "tool_results": {"count": 19, "tokens": 121000}
  }
}
```

### 前端状态条（输入区上方）

| 状态 | usage_percent | 展示 |
|------|---------------|------|
| normal | < 70% | 不展示 |
| warning | 70%-80% | 浅色进度条 |
| caution | 80%-90% | 黄色提示"上下文较长，可点击压缩" |
| critical | > 90% | 红色提示"即将自动压缩" |
| block | >= 硬上限 | 红色提示"已自动压缩" |

### 详情面板

点击进度条展开详情：
- **角色分布**：system / user / assistant / tool 的 count 和 tokens 占比
- **工具结果**：数量和 token 占比
- **阈值线**：compact / warning / block 阈值标记

---

## 8. 手动压缩

### Web UI

**按钮位置**: 聊天头部右侧 "压缩" 按钮

**操作**: 点击后调用 `POST /chat/compact`，前端替换当前会话消息列表。

### /compact 命令

在输入框输入：
- `/compact` — 直接压缩
- `/compact 重点保留数据库迁移` — 带自定义指令

### API 端点

```http
POST /api/chat/compact
Content-Type: application/json

{
  "messages": [...],
  "instruction": "可选的自定义压缩指令",
  "model_config_id": 1,
  "session_id": "可选，若提供则持久化到数据库"
}
```

**响应**:
```json
{
  "success": true,
  "summary": "对话摘要...",
  "removed_messages": 42,
  "kept_messages": 8,
  "saved_tokens": 12800,
  "before_tokens": 96000,
  "after_tokens": 42000,
  "messages": [...]  // 压缩后的完整消息列表
}
```

### 持久化到 Session

若请求包含 `session_id`，后端会：
1. 删除该 session 的所有旧 `SessionMessage`
2. 写入压缩后的新消息
3. 更新 `session.message_count`

刷新页面后从后端加载，压缩结果不会丢失。

---

## 9. 压缩后文件恢复

**文件**: `app/modules/agent/file_tracker.py::FileTracker`

面向编程任务，压缩后在 token 预算内恢复最近访问/编辑过的文件内容：

**记录时机**: 每次 `read_file` / `write_file` / `edit_file` 工具执行后

**恢复优先级**:
1. 编辑过的文件（`was_edited=True`）
2. 最近读取的文件（按时间倒序）
3. 在预算内（默认 `max_tokens=50_000`, `max_files=5`）

**恢复方式**: 在 `_rebuild_after_compact()` 末尾追加 system 消息：
```
[Restored files after context compression]
- /app/main.py (edited=True, tokens=42)
- /app/utils.py (edited=False, tokens=28)
```

**注入位置**: `ContextCompressionService._rebuild_after_compact()` 和 `AgentLoop._rebuild_after_compact()` 都会恢复文件信息。

---

## 10. 关键文件

| 文件 | 用途 |
|------|------|
| `app/modules/agent/compression_service.py` | 统一入口：`auto_prune`, `manual_compact`, `emergency_compact`, `build_context_report` |
| `app/modules/agent/compactor.py` | Compactor 类、摘要生成、熔断器、空摘要保护、TokenBudget 委托 |
| `app/modules/agent/context_pruner.py` | Snip、MicroCompacter、estimate_tokens |
| `app/modules/agent/context_collapse.py` | ContextCollapser：合并 system 消息、截断 tool_result |
| `app/modules/agent/token_budget.py` | TokenBudget、阈值计算、状态判断 |
| `app/modules/agent/file_tracker.py` | FileTracker、文件访问记录、压缩后恢复 |
| `app/modules/agent/loop.py` | AgentLoop、`_prune_context`、截断续传、`_track_file_access` |
| `app/api/chat.py` | `/chat/react/stream`、 `/chat/compact`、session 持久化 |
| `app/api/agent_execute.py` | Agent 执行入口组装压缩组件 |
| `frontend/src/views/Chat.vue` | 压缩按钮、/compact 命令、context_report 可视化面板 |

---

## 11. 测试覆盖

| 测试文件 | 覆盖内容 |
|----------|----------|
| `tests/test_token_budget.py` | 16 个测试：阈值计算、状态判断、auto-scaling |
| `tests/test_context_pruner.py` | 17 个测试：Snip、MicroCompact、estimate_tokens |
| `tests/test_file_tracker.py` | 8 个测试：记录、去重、优先级、预算控制 |
| `tests/test_compression_service.py` | 10 个测试：chat_stream 聚合、force 参数、token 估算、FileTracker 跳过、重建恢复、manual_compact 返回消息 |

**运行**:
```bash
pytest tests/test_token_budget.py tests/test_context_pruner.py \
       tests/test_file_tracker.py tests/test_compression_service.py -v
# 53 passed
```

---

## 12. 与 Claude Code 的差异

### 已实现的对齐

- ✅ 五层压缩架构（Snip → MicroCompact → ContextCollapse → Compactor → Reactive Compact）
- ✅ 阈值计算对齐（200K 模型 167K 阈值）
- ✅ 分层触发（normal/warning/caution/critical/block）
- ✅ Autocompact 时间触发（5 分钟）
- ✅ 截断自动续传（3 次）
- ✅ prompt_too_long 5 级恢复
- ✅ 熔断器（3 次连续失败）
- ✅ 空摘要保护（失败不丢历史）
- ✅ 多模态剥离（image/document 占位符）
- ✅ 压缩后文件恢复
- ✅ 手动压缩命令（/compact + Web UI 按钮）
- ✅ 上下文可视化报告

### 尚未实现

| 功能 | 原因 |
|------|------|
| 缓存感知 MicroCompact | 仅 Anthropic API 有意义 |
| Session Memory Compact | PioneClaw 有自己的记忆系统 |
| 部分压缩（up_to/from） | 复杂度/收益比低 |
| 压缩后技能恢复 | 当前优先级低 |
| 子代理压缩 | 直接调用 LLM 已足够 |
