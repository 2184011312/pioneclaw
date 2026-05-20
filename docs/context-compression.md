# 上下文压缩机制

本文档记录 PioneClaw 和 Claude Code 的上下文压缩机制，对比设计差异并记录演进路线。

## 1. 设计哲学

### Claude Code

Claude Code 采用"渐进式压缩阶梯"：从最轻量的操作（Snip、MicroCompact）开始，只在廉价手段不够时才升级到完整的 LLM 摘要（AutoCompact）。

**核心原则**：日常 context 控制由 Snip + MicroCompact 承担，Compactor（LLM 摘要）是接近模型上下文上限时的最后防线。

### PioneClaw

PioneClaw 借鉴 Claude Code 的模式，实现了三层压缩（Snip -> MicroCompact -> Compactor）。主要差异在于触发策略和功能深度——PioneClaw 追求简洁正确，而非功能广度。

---

## 2. 逐层对比

### 第一层：Snip（零成本消息裁剪）

| 对比项 | Claude Code | PioneClaw |
|--------|-------------|-----------|
| 移除空 system 消息 | 是 | 是 |
| 移除无 tool_calls 的空 assistant 消息 | 是 | 是 |
| 截断超长 reasoning_content | 不适用（不暴露推理过程） | 是，最多 2000 字符 |
| 合并相邻 injection system 消息 | 是 | 未实现 |
| 返回方式 | 返回新列表 | 返回新列表 |
| 执行时机 | 每次 API 调用前 | 每次 LLM 调用前（在 `_prune_context` 中） |

**细节**：Claude Code 的 Snip 会将大型工具结果替换为简短 stub，并追踪 `snipTokensFreed` 传递给下游用于阈值判断。PioneClaw 的 Snip 更简单——只移除真正的空消息和截断推理内容。

### 第二层：MicroCompact（清除旧工具结果）

| 对比项 | Claude Code | PioneClaw |
|--------|-------------|-----------|
| 核心思路 | 将旧工具结果替换为 `'[Old tool result content cleared]'` | 相同 |
| 计数触发 | GrowthBook 配置的 `keepRecent` | 可配置 `keep_recent`，默认 8 |
| 大小触发 | 无显式大小限制，由其他层处理 | 有，单条结果最多 4000 字符 |
| 时间触发 | 有，60 分钟空闲后清理 | 未实现 |
| 缓存感知 MicroCompact | 有，使用 `cache_edits` API 避免前缀失效 | 未实现 |
| API 层 MicroCompact | 有，`input_tokens >= 180K` 时清除工具输入 | 未实现 |
| 可压缩工具白名单 | Read, Shell, Grep, Glob, WebSearch, WebFetch, FileEdit, FileWrite | read_file, write_file, edit_file, grep, glob, file_search, exec, bash, web_search, web_fetch, browser |
| 保留消息结构 | 是（从不删除消息） | 是（原地替换内容） |

**PioneClaw 尚未实现的 Claude Code 功能**：

1. **缓存感知 MicroCompact**：使用 Anthropic 的 `cache_edits` API 删除旧工具结果而不破坏 prompt 缓存前缀。这是 Anthropic API 用户的重要优化。
2. **时间触发**：将超过 60 分钟的旧工具结果替换为占位符，与数量无关。适用于有闲置时段的长时间会话。
3. **API 层 MicroCompact**：在输入 token 达到 180K 时清除搜索/读取/Shell 工具的工具输入（不仅是输出）。无需 LLM 即可减少 token 数。

### 第三层：Compactor（LLM 摘要）

| 对比项 | Claude Code | PioneClaw |
|--------|-------------|-----------|
| **触发阈值** | `context_window - 33,000` tokens（动态计算） | `context_window - 33,000` tokens（动态计算，2026-05 对齐） |
| **消息数兜底** | 无（纯 token 判断） | `message_threshold=200` 作为安全网 |
| **Token 估算** | 从上次 API 响应读取实际 token 用量 | 基于字符近似估算（中文 1.5 字符/token，英文 4 字符/token） |
| **摘要提示词** | 9 段结构化 XML 格式（`<analysis>` + `<summary>`） | 9 段结构化 Markdown 格式 |
| **递归摘要** | 无显式递归；使用 session memory 文件做增量更新 | 有，`RECURSIVE_SHORT_CONTEXT_SUMMARY_PROMPT` 将新消息合并到已有摘要 |
| **部分压缩** | 有，支持 `up_to` 和 `from` 方向 | 未实现 |
| **Session Memory Compact** | 有，使用提取的 session memory 文件作为摘要（无 LLM 调用） | 未实现 |
| **图像剥离** | 有，压缩前将图片/文档替换为 `[image]` / `[document]` | 未实现 |
| **压缩后文件恢复** | 有，在 50K token 预算内恢复最近 5 个读取的文件 | 未实现 |
| **压缩后技能恢复** | 有，重新注入已调用技能文本 | 未实现 |
| **熔断器** | 连续 3 次失败后停止重试 | 未实现 |
| **Prompt 过长重试** | 有，逐批丢弃最旧消息组直到请求能发送 | 未实现 |
| **响应式压缩** | 有，`prompt_too_long` 时逐批剥离消息 | 未实现 |
| **记忆提取** | 压缩时提取 user/feedback/project/reference 条目 | 有，`CONVERSATION_TO_MEMORY_PROMPT` 提取记忆条目 |
| **子代理压缩** | 有，使用 `maxTurns: 1` 的子代理实现缓存共享 | 未实现（直接调用 LLM） |

**PioneClaw 摘要重建方式**：

```python
重建后消息 = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": f"[Previous conversation summary]\n{摘要}"},
    *最近消息  # keep_recent=8 条
]
```

**Claude Code 摘要重建方式**：使用带元数据的"Compact summary"消息（消息数量、方向、自定义上下文指令）。对用户更可见。

### 第四层：应急处理（Prompt 过长）

| 对比项 | Claude Code | PioneClaw |
|--------|-------------|-----------|
| `prompt_too_long` 重试 | 有，最多 3 次，每次丢弃更旧的消息组 | 未实现 |
| 阻塞限制 | 达到 `effective_context_window - 3,000` 时阻止新请求，强制手动压缩 | 未实现 |
| 警告 UI | 接近阈值 20K 时显示 token 使用百分比警告 | 未实现 |
| 手动 `/compact` 命令 | 有，支持自定义上下文指令 | 未实现 |

---

## 3. 阈值策略（详细）

### Claude Code

```
AUTOCOMPACT_BUFFER_TOKENS = 13,000    # 安全缓冲
MAX_OUTPUT_TOKENS_FOR_SUMMARY = 20,000  # 预留给摘要输出

effective_context_window = 模型上下文窗口 - 20,000
auto_compact_threshold = effective_context_window - 13,000
```

对于 200K 模型：阈值 = 200K - 20K - 13K = **167,000 tokens**（窗口约 84%）
对于 1M 模型：阈值 = 1M - 20K - 13K = **967,000 tokens**（窗口约 97%）

每次轮次在 Snip + MicroCompact 之后检查，使用 `tokenCountWithEstimation()` 读取上次 API 响应的实际 token 用量。

### PioneClaw（当前）

```python
@dataclass
class CompactionConfig:
    context_window: int = 200_000      # 从 AI 配置读取
    buffer_tokens: int = 33_000        # 与 Claude Code 合并后的缓冲一致

    @property
    def token_threshold(self) -> int:
        return self.context_window - self.buffer_tokens
```

对于 200K 模型：阈值 = 200K - 33K = **167,000 tokens**（与 Claude Code 一致）
对于 256K 模型：阈值 = 256K - 33K = **223,000 tokens**

小上下文窗口保护：当 `context_window <= buffer_tokens` 时，buffer 自动缩放到窗口的 10%，避免阈值变负数。

**与 Claude Code 的差异**：PioneClaw 将输出预留（20K）和缓冲（13K）合并为单个 `buffer_tokens=33,000`。Claude Code 分开管理以便更细粒度控制（例如阻塞限制只在有效窗口上加上 3K 缓冲）。

### 消息数兜底阈值

PioneClaw 保留 `message_threshold=200` 作为额外触发条件。Claude Code 没有这个——纯靠 token 计数。PioneClaw 保留它是因为其 token 估算基于字符近似（不如 Claude Code 的 API 报告值准确）。

---

## 4. Agent Loop 集成

### PioneClaw（`loop.py::_prune_context`）

在 ReAct while 循环中每次 LLM 调用前执行：

```
第一层：Snip（snip_prune）-> 移除空消息，截断推理内容
第二层：MicroCompact（micro_compact）-> 清除旧工具结果内容
第三层：Compactor（should_compact + compact）-> 超过阈值时 LLM 摘要
```

PioneClaw 通过 `AgentLoop.__init__` 传入 `ContextPruner` 和 `Compactor`，在 `chat.py` 和 `agent_execute.py` API 入口点组装。`context_window` 从 `AIModelConfig` 数据库记录读取。

### Claude Code（`query.ts`）

在每次 API 调用前在 main query loop 中执行：

```
第一层：Snip（内容替换）
第二层 a：时间触发 MicroCompact（60 分钟空闲触发）
第二层 b：缓存感知 MicroCompact（基于数量，不破坏缓存）
第二层 c：API 层 MicroCompact（input_tokens >= 180K）
第三层 a：Session Memory Compact（如果有 session memory 文件，无 LLM 调用）
第三层 b：完整 AutoCompact（LLM 摘要，阈值触发）
第四层：Reactive Compact（紧急，prompt_too_long 时剥离）
```

---

## 5. PioneClaw 演进路线

### 高优先级

1. **Token 估算精度**：用 API 返回的实际 token 用量替代字符估算。Claude Code 的 `tokenCountWithEstimation` 从 API 响应读取，准确度高得多，届时可移除 `message_threshold` 兜底。

2. **熔断器**：连续 3 次压缩失败（如 LLM 返回空或报错）后停止重试，避免浪费 API 调用。Claude Code 使用 `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3`。

3. **压缩前剥离图像**：如果对话包含图片，在发送给摘要器之前替换为 `[image]` 占位符。防止压缩请求本身触发 `prompt_too_long`。

### 中优先级

4. **Session Memory Compact**：在正常运行期间将关键事实提取到文件。压缩时直接使用此文件作为摘要，无需 LLM 调用。Claude Code 的 `sessionMemoryCompact.ts` 保留 `lastSummarizedMessageId` 之后的消息，将更早的消息替换为 memory 文件内容。

5. **压缩后文件恢复**：压缩后在 50K token 预算内恢复最近 5 个读取的文件。对编程任务至关重要——agent 需要精确的文件内容，而不是摘要。

6. **部分压缩**：支持 `up_to` 和 `from` 方向。适用于用户只想压缩对话某个区间的场景。

### 低优先级

7. **缓存感知 MicroCompact**：使用 Anthropic 的 `cache_edits` API 清除旧工具结果而不破坏 prompt 缓存。仅适用于 Anthropic API 用户。

8. **Prompt 过长重试**：API 返回 `prompt_too_long` 时丢弃最旧消息组并重试，最多 3 次后报错。

9. **手动 `/compact` 命令**：允许用户用自定义指令触发压缩（如 `/compact 重点关注 TypeScript 代码变更`）。

10. **警告 UI**：接近阈值时在聊天界面显示 token 使用百分比。

---

## 6. 关键文件

### PioneClaw

| 文件 | 用途 |
|------|------|
| [compactor.py](backend/app/modules/agent/compactor.py) | Compactor 类、CompactionConfig、摘要提示词 |
| [context_pruner.py](backend/app/modules/agent/context_pruner.py) | Snip、MicroCompacter、ContextPruner、estimate_tokens |
| [loop.py](backend/app/modules/agent/loop.py) | `_prune_context()` 和 `_rebuild_after_compact()` |
| [chat.py](backend/app/api/chat.py) | 在聊天端点组装 ContextPruner + Compactor |
| [agent_execute.py](backend/app/api/agent_execute.py) | 在 Agent 执行入口组装 ContextPruner + Compactor |

### Claude Code（参考）

| 文件 | 用途 |
|------|------|
| `src/services/compact/autoCompact.ts` | 阈值计算、`shouldAutoCompact()`、`autoCompactIfNeeded()` |
| `src/services/compact/compact.ts` | 完整 LLM 压缩、`compactConversation()`、部分压缩 |
| `src/services/compact/microCompact.ts` | MicroCompact 编排、时间触发 |
| `src/services/compact/apiMicrocompact.ts` | API 层上下文编辑 |
| `src/services/compact/sessionMemoryCompact.ts` | Session memory 压缩 |
| `src/services/compact/prompt.ts` | 压缩提示词 |
| `src/services/compact/grouping.ts` | 按 API 轮次分组消息 |
| `src/services/compact/postCompactCleanup.ts` | 压缩后状态清理 |
| `src/query.ts` | 主查询循环——所有压缩层的编排 |
