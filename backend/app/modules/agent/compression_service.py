"""
ContextCompressionService — 唯一压缩入口

职责：
1. auto_prune(): AgentLoop 每轮自动调用（Snip -> MicroCompact -> Compactor）
2. manual_compact(): Web UI / /compact 命令调用（强制 LLM 摘要）
3. emergency_compact(): prompt_too_long 时调用（激进丢弃）
4. estimate_or_read_usage(): 优先真实 token 用量，fallback 字符估算
5. build_compression_report(): 返回压缩统计报告

设计原则：
- 不要让 Web UI、AgentLoop、/compact 各自实现压缩逻辑
- 所有压缩操作走这里，保证行为一致
"""

import logging
from dataclasses import dataclass
from typing import Any

from app.modules.agent.compactor import CompactionResult, Compactor
from app.modules.agent.context_collapse import ContextCollapser
from app.modules.agent.context_pruner import ContextPruner, estimate_tokens
from app.modules.agent.token_budget import TokenBudget, TokenUsage

logger = logging.getLogger(__name__)


@dataclass
class CompressionReport:
    """压缩报告"""

    summary: str = ""
    removed_messages: int = 0
    kept_messages: int = 0
    saved_tokens: int = 0
    before_tokens: int = 0
    after_tokens: int = 0
    strategy: str = ""  # "snip", "microcompact", "compact", "emergency"


class ContextCompressionService:
    """
    上下文压缩服务 — 唯一入口
    """

    def __init__(
        self,
        budget: TokenBudget | None = None,
        compactor: Compactor | None = None,
        context_pruner: ContextPruner | None = None,
        file_tracker=None,
    ):
        self.budget = budget
        self.compactor = compactor
        self.context_pruner = context_pruner
        self.file_tracker = file_tracker
        self._context_collapser = ContextCollapser()
        # Autocompact 时间触发（改进项 4）
        self._last_assistant_at: float | None = None
        self._autocompact_interval_seconds: float = 300  # 5 分钟

    def estimate_or_read_usage(
        self,
        messages: list[dict[str, Any]],
        provider,
    ) -> TokenUsage:
        """
        获取 token 用量。

        策略：
        - API 真实值（provider.last_input_tokens）可能滞后（不包含本轮新追加的工具结果）
        - 字符估算（estimate_tokens）能反映当前 messages 的实时大小，但精度较低
        - 取两者最大值，避免该压缩时不压缩

        source 标注实际采用的来源：
        - "api": 仅用了 API 值（messages 估算 <= API 值）
        - "estimated": 仅用了估算值（API 无值或估算更大）
        - "mixed": 两者都有，取了大值
        """
        # 1. 实时字符估算（反映当前 messages 大小）
        estimated = estimate_tokens(messages)

        # 2. API 真实值（可能滞后）
        real_input = 0
        real_output = 0
        if provider:
            real_input = getattr(provider, "last_input_tokens", 0) or 0
            real_output = getattr(provider, "last_output_tokens", 0) or 0

        # 3. 取最大值，避免遗漏本轮新追加的大工具结果
        if real_input > 0:
            if estimated > real_input:
                return TokenUsage(
                    input_tokens=estimated,
                    output_tokens=real_output,
                    source="estimated",
                )
            return TokenUsage(
                input_tokens=real_input,
                output_tokens=real_output,
                source="api",
            )

        # 无 API 值，完全依赖估算
        return TokenUsage(
            input_tokens=estimated,
            output_tokens=0,
            source="estimated",
        )

    def build_usage_info(
        self,
        messages: list[dict[str, Any]],
        provider,
    ) -> dict[str, Any]:
        """返回前端可用的上下文使用率信息"""
        usage = self.estimate_or_read_usage(messages, provider)
        info = self.budget.to_dict(usage.input_tokens)
        info["output_tokens"] = usage.output_tokens
        info["source"] = usage.source
        return info

    async def auto_prune(
        self,
        messages: list[dict[str, Any]],
        provider,
    ) -> list[dict[str, Any]]:
        """
        AgentLoop 每轮自动调用。

        分层压缩（改进项 2：根据 TokenBudget 状态分级触发）：
        - normal   (< 70%):  Snip（零成本）
        - warning  (70-80%): Snip + MicroCompact
        - caution  (80-90%): Snip + MicroCompact + ContextCollapse（轻量预压缩）
        - critical (90%+):   Snip + MicroCompact + ContextCollapse + Compactor（全链路）
        - block    (>=硬上限): Compactor（激进摘要）或 emergency_compact
        """
        import time

        # 防御性检查：budget 未注入时直接返回
        if self.budget is None:
            logger.warning("auto_prune called without TokenBudget, skipping")
            return messages

        # 读取 token 用量
        usage = self.estimate_or_read_usage(messages, provider)
        input_tokens = usage.input_tokens
        status = self.budget.get_status(input_tokens)

        logger.debug(
            f"Auto prune: status={status}, tokens={input_tokens}, "
            f"threshold={self.budget.compact_threshold}"
        )

        # Autocompact 时间触发检查（改进项 4）
        now = time.time()
        autocompact_triggered = False
        if self._last_assistant_at is not None:
            elapsed = now - self._last_assistant_at
            if elapsed > self._autocompact_interval_seconds:
                logger.info(
                    f"Autocompact triggered: {elapsed:.0f}s since last assistant, "
                    f"running aggressive MicroCompact"
                )
                autocompact_triggered = True

        # Layer 1: Snip — 所有状态都执行（零成本）
        if self.context_pruner:
            snipped, snip_saved = self.context_pruner.snip_prune(messages)
            messages = snipped
            if snip_saved > 0:
                logger.debug(f"Snip: saved ~{snip_saved} chars")

        # warning 及以上：Layer 2 MicroCompact
        # Autocompact 时也会执行强化 MicroCompact（保留更少）
        if status in ("warning", "caution", "critical", "block") or autocompact_triggered:
            if self.context_pruner:
                if autocompact_triggered and status not in ("critical", "block"):
                    # 时间触发：强化模式（保留最近 3 个，截断阈值更低）
                    from app.modules.agent.context_pruner import MicroCompacter

                    aggressive_micro = MicroCompacter(keep_recent=3, max_chars=2000)
                    messages, micro_saved = aggressive_micro.prune(messages)
                else:
                    messages, micro_saved = self.context_pruner.micro_compact(messages)
                if micro_saved > 0:
                    logger.debug(f"MicroCompact: saved ~{micro_saved} chars")

        # caution 及以上：Layer 3 ContextCollapse（轻量预压缩）
        if status in ("caution", "critical", "block"):
            messages, collapse_saved = self._context_collapser.collapse(messages)
            if collapse_saved > 0:
                logger.debug(f"ContextCollapse: saved ~{collapse_saved} chars")

        # critical / block：Layer 4 Compactor（高成本 LLM 摘要）
        if status in ("critical", "block"):
            if self.compactor:
                logger.info(
                    f"Compactor triggered: status={status}, "
                    f"tokens={input_tokens} >= threshold {self.budget.compact_threshold}"
                )
                try:
                    # block 状态使用更激进的摘要（更短的 max_summary_chars）
                    force_compact = status == "block"
                    result = await self.compactor.compact(
                        messages, force=force_compact
                    )
                    if result.summary and result.removed_messages > 0:
                        messages = self._rebuild_after_compact(messages, result)
                        logger.info(
                            f"Compacted: removed {result.removed_messages} messages, "
                            f"kept {result.kept_messages}, saved ~{result.saved_tokens} tokens"
                        )
                    else:
                        logger.info("Compact skipped: no messages to remove")
                except Exception as e:
                    logger.error(f"Auto compact failed: {e}, preserving original messages")

        return messages

    def mark_assistant_response(self) -> None:
        """标记 assistant 响应时间，用于 Autocompact 时间触发。"""
        import time

        self._last_assistant_at = time.time()

    async def manual_compact(
        self,
        messages: list[dict[str, Any]],
        instruction: str | None = None,
    ) -> tuple[CompressionReport, list[dict[str, Any]]]:
        """
        手动压缩 — Web UI 按钮或 /compact 命令调用。

        强制使用 Compactor，忽略阈值。
        如果提供了 instruction，会注入摘要提示词中作为额外约束。

        Returns:
            Tuple[CompressionReport, List[Dict]]: (压缩报告, 压缩后的消息列表)
        """
        if not self.compactor:
            report = CompressionReport(
                strategy="compact", summary="Compactor not configured"
            )
            return report, messages

        before_tokens = self.estimate_or_read_usage(
            messages, provider=None
        ).input_tokens

        # 注入自定义指令（如果有）
        if instruction:
            pass

        try:
            # 先走 MicroCompact 减少 token 压力
            if self.context_pruner:
                messages, _ = self.context_pruner.micro_compact(messages)

            result = await self.compactor.compact(
                messages, instruction=instruction, force=True
            )

            if result.summary and result.removed_messages > 0:
                messages = self._rebuild_after_compact(messages, result)

            after_tokens = self.estimate_or_read_usage(
                messages, provider=None
            ).input_tokens

            report = CompressionReport(
                summary=result.summary or "",
                removed_messages=result.removed_messages,
                kept_messages=result.kept_messages,
                saved_tokens=result.saved_tokens,
                before_tokens=before_tokens,
                after_tokens=after_tokens,
                strategy="compact",
            )
            return report, messages
        except Exception as e:
            logger.error(f"Manual compact failed: {e}")
            report = CompressionReport(
                strategy="compact",
                summary=f"压缩失败: {e}",
                before_tokens=before_tokens,
            )
            return report, messages

    async def emergency_compact(
        self,
        messages: list[dict[str, Any]],
        attempt: int = 1,
    ) -> list[dict[str, Any]]:
        """
        prompt_too_long 时的应急压缩（改进项 5：5 级渐进恢复）。

        策略（从保守到激进）：
        L1: 强化 MicroCompact（保留最近 3 个工具结果）
        L2: 截断所有工具结果到最小元信息
        L3: 丢弃旧消息（保留 system + 最近 5 条）
        L4: 激进丢弃（保留 system + 最近 user 消息）
        L5: 最终防线（只保留 system prompt，提示用户历史已清空）
        """
        logger.warning(f"Emergency compact attempt {attempt}")

        if attempt == 1:
            # L1: 强化 MicroCompact（保留最近 3 个，截断阈值更低）
            if self.context_pruner:
                from app.modules.agent.context_pruner import MicroCompacter

                emergency_micro = MicroCompacter(keep_recent=3, max_chars=1000)
                messages, saved = emergency_micro.prune(messages)
                logger.info(
                    f"Emergency L1: aggressive MicroCompact, saved ~{saved} chars"
                )
            return messages

        elif attempt == 2:
            # L2: 截断所有工具结果内容到最小元信息
            new_messages = [dict(m) for m in messages]
            for msg in new_messages:
                if msg.get("role") == "tool":
                    tool_name = msg.get("tool_name", msg.get("name", ""))
                    msg["content"] = (
                        f"[tool_result: {tool_name}, content stripped for emergency]"
                    )
            logger.info("Emergency L2: stripped all tool result content")
            return new_messages

        elif attempt == 3:
            # L3: 丢弃最旧的非 system 消息，保留 system + 最近 5 条
            system_msgs = [m for m in messages if m.get("role") == "system"]
            other_msgs = [m for m in messages if m.get("role") != "system"]
            keep_recent = min(5, len(other_msgs))
            kept = other_msgs[-keep_recent:] if keep_recent > 0 else []
            dropped = len(other_msgs) - keep_recent
            logger.info(
                f"Emergency L3: dropped {dropped} old messages, kept {keep_recent}"
            )
            return system_msgs + kept

        elif attempt == 4:
            # L4: 激进丢弃，只保留 system + 最近一条 user 消息
            system_msgs = [m for m in messages if m.get("role") == "system"]
            user_msgs = [m for m in messages if m.get("role") == "user"]
            last_user = user_msgs[-1:] if user_msgs else []
            dropped = len(messages) - len(system_msgs) - len(last_user)
            logger.info(
                f"Emergency L4: aggressive drop, kept {len(system_msgs)} system + "
                f"{len(last_user)} user, dropped {dropped}"
            )
            return system_msgs + last_user

        elif attempt == 5:
            # L5: 最终防线，只保留第一条 system prompt
            system_prompts = [m for m in messages if m.get("role") == "system"]
            first_system = system_prompts[:1] if system_prompts else []
            # 追加提示：历史已清空（创建副本，避免污染原始 dict）
            if first_system:
                first_system = [dict(msg) for msg in first_system]
                first_system[0]["content"] += (
                    "\n\n[系统提示：对话历史因长度限制已清空，请根据当前问题继续回答。]"
                )
            logger.info("Emergency L5: final resort, kept only system prompt")
            return first_system

        return messages

    def _rebuild_after_compact(
        self,
        messages: list[dict[str, Any]],
        result: CompactionResult,
    ) -> list[dict[str, Any]]:
        """压缩后重建消息列表"""
        if not result.summary:
            return messages

        # 保留 system prompt
        system_prompts = [m for m in messages if m.get("role") == "system"]

        # 保留最近消息
        keep_recent = getattr(
            getattr(self.compactor, "config", None),
            "keep_recent_messages",
            8,
        )
        recent = messages[-keep_recent:] if len(messages) > keep_recent else messages

        # 重建：system + 摘要 + 最近消息
        rebuilt = []
        if system_prompts:
            rebuilt.extend(system_prompts)

        rebuilt.append(
            {
                "role": "user",
                "content": f"[Previous conversation summary]\n{result.summary}",
            }
        )
        rebuilt.extend(recent)

        # Phase 6: 恢复关键文件内容（如果 FileTracker 已注入）
        if self.file_tracker and self.file_tracker.record_count > 0:
            restored_files = self.file_tracker.get_recent(
                max_tokens=50_000, max_files=5
            )
            if restored_files:
                restored_lines = ["[Restored files after context compression]"]
                for record in restored_files:
                    restored_lines.append(
                        f"- {record.path} "
                        f"(edited={record.was_edited}, "
                        f"tokens={record.estimated_tokens})"
                    )
                rebuilt.append(
                    {
                        "role": "system",
                        "content": "\n".join(restored_lines),
                    }
                )
                logger.info(
                    f"Restored {len(restored_files)} files after compaction via service: "
                    f"{[r.path for r in restored_files]}"
                )

        return rebuilt

    def build_context_report(
        self,
        messages: list[dict[str, Any]],
        provider,
    ) -> dict[str, Any]:
        """
        构建上下文可视化报告（改进项 6）。

        返回结构化数据，供前端展示 token 分布和压缩状态。
        """
        usage = self.estimate_or_read_usage(messages, provider)
        input_tokens = usage.input_tokens

        # 角色分布
        role_counts: dict[str, int] = {}
        role_tokens: dict[str, int] = {}
        tool_call_count = 0
        tool_result_count = 0
        tool_result_tokens = 0
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            content_len = len(content) if isinstance(content, str) else len(str(content))
            # 粗略 token 估算
            est = content_len // 4
            role_counts[role] = role_counts.get(role, 0) + 1
            role_tokens[role] = role_tokens.get(role, 0) + est
            if role == "tool":
                tool_result_count += 1
                tool_result_tokens += est
            if role == "assistant" and msg.get("tool_calls"):
                tool_call_count += len(msg["tool_calls"])

        # 优先展示 tool_calls 次数（更直观），无 tool_calls 时展示 tool 结果消息数
        display_tool_count = tool_call_count if tool_call_count > 0 else tool_result_count

        # 防御性检查：确保 budget 不为 None（避免阈值全部显示为 0）
        if self.budget is None:
            logger.warning("build_context_report: budget is None, using fallback TokenBudget")
            fallback_budget = TokenBudget(context_window=128_000)
            budget_info = fallback_budget.to_dict(input_tokens)
        else:
            budget_info = self.budget.to_dict(input_tokens)

        return {
            "total_messages": len(messages),
            "input_tokens": input_tokens,
            "output_tokens": usage.output_tokens,
            "source": usage.source,
            "context_window": budget_info.get("context_window", 0),
            "usage_percent": budget_info.get("usage_percent", 0),
            "status": budget_info.get("status", "unknown"),
            "compact_threshold": budget_info.get("compact_threshold", 0),
            "warning_threshold": budget_info.get("warning_threshold", 0),
            "hard_block_threshold": budget_info.get("hard_block_threshold", 0),
            "role_distribution": {
                role: {"count": role_counts.get(role, 0), "tokens": role_tokens.get(role, 0)}
                for role in set(list(role_counts.keys()) + ["system", "user", "assistant", "tool"])
            },
            "tool_results": {
                "count": display_tool_count,
                "tokens": tool_result_tokens,
            },
        }
