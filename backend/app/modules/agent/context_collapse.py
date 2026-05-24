"""
ContextCollapse — 轻量预压缩层

职责：
1. 合并相邻的 system 注入消息（Agent 间消息、上下文恢复消息）
2. 去除冗余 tool_calls 元信息（去重 schema 描述）
3. 压缩超长 tool_result 为结构化占位符（比 MicroCompact 更激进）
4. 零 LLM 成本，纯文本操作

触发条件：TokenBudget status == caution（80%-90%）

对标 Claude Code 的 ContextCollapse 层，介于 MicroCompact 和 Compactor 之间。
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ContextCollapser:
    """上下文折叠器 — 轻量预压缩"""

    INJECTION_MARKERS = [
        "[来自",
        "[Agent 间消息]",
        "[上下文恢复]",
        "[Previous conversation summary]",
        "[Restored files after context compression]",
        "[工具执行结果",
        "[tool_result:",
    ]

    def __init__(
        self,
        max_tool_result_chars: int = 2000,
        max_system_merge_chars: int = 4000,
    ):
        self.max_tool_result_chars = max_tool_result_chars
        self.max_system_merge_chars = max_system_merge_chars

    def collapse(self, messages: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        """
        执行轻量预压缩，返回 (新消息列表, 节省字符数)。

        不修改原列表，返回新列表。
        """
        if not messages:
            return messages, 0

        import copy

        new_messages = copy.deepcopy(messages)
        chars_saved = 0

        # 1. 合并相邻 system 注入消息
        merged, saved = self._merge_adjacent_system(new_messages)
        new_messages = merged
        chars_saved += saved

        # 2. 截断超长 tool_result
        truncated, saved = self._truncate_tool_results(new_messages)
        new_messages = truncated
        chars_saved += saved

        # 3. 去除冗余 tool_calls 元信息
        cleaned, saved = self._dedup_tool_schemas(new_messages)
        new_messages = cleaned
        chars_saved += saved

        if chars_saved > 0:
            logger.debug(
                f"ContextCollapse: saved ~{chars_saved} chars, "
                f"messages {len(messages)} -> {len(new_messages)}"
            )

        return new_messages, chars_saved

    def _merge_adjacent_system(
        self, messages: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], int]:
        """合并相邻的 system 消息（排除第一条 system prompt）。"""
        if len(messages) < 2:
            return messages, 0

        result: list[dict[str, Any]] = []
        chars_saved = 0
        pending_system: list[str] = []

        for i, msg in enumerate(messages):
            role = msg.get("role", "")

            # 第一条 system prompt 单独保留（不合并）
            if role == "system" and i == 0:
                result.append(msg)
                continue

            if role == "system":
                content = str(msg.get("content", ""))
                # 识别为"注入类"system 消息（Agent 间消息、恢复消息等）
                if self._is_injection_system(content):
                    pending_system.append(content)
                    # 节省量由 _flush_system 统一计算，此处不预累加
                else:
                    # 普通 system 消息，先刷新 pending，再添加
                    if pending_system:
                        merged, merged_saved = self._flush_system(pending_system)
                        result.extend(merged)
                        chars_saved += merged_saved
                        pending_system = []
                    result.append(msg)
            else:
                # 非 system 消息，先刷新 pending
                if pending_system:
                    merged, merged_saved = self._flush_system(pending_system)
                    result.extend(merged)
                    chars_saved += merged_saved
                    pending_system = []
                result.append(msg)

        # 末尾刷新
        if pending_system:
            merged, merged_saved = self._flush_system(pending_system)
            result.extend(merged)
            chars_saved += merged_saved

        return result, chars_saved

    def _is_injection_system(self, content: str) -> bool:
        """判断是否为注入类 system 消息（可安全合并的）。"""
        return any(marker in content for marker in self.INJECTION_MARKERS)

    def _flush_system(
        self, contents: list[str]
    ) -> tuple[list[dict[str, Any]], int]:
        """将 pending 的 system 内容合并为一条消息。"""
        if not contents:
            return [], 0

        if len(contents) == 1:
            return [{"role": "system", "content": contents[0]}], 0

        # 多条合并，用分隔符
        merged_content = "\n---\n".join(contents)
        # 如果合并后太长，截断
        if len(merged_content) > self.max_system_merge_chars:
            merged_content = (
                merged_content[: self.max_system_merge_chars]
                + f"\n...[truncated {len(merged_content) - self.max_system_merge_chars} chars]"
            )

        # 节省 = 原内容总长度 - 合并后长度 + (n-1) * 消息开销估算
        original_len = sum(len(c) for c in contents)
        saved = original_len - len(merged_content) + (len(contents) - 1) * 20

        return [{"role": "system", "content": merged_content}], saved

    def _truncate_tool_results(
        self, messages: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], int]:
        """截断超长 tool_result 为更短的占位符（比 MicroCompact 更激进）。"""
        chars_saved = 0
        for msg in messages:
            if msg.get("role") != "tool":
                continue
            content = msg.get("content", "")
            if not isinstance(content, str):
                continue

            if len(content) > self.max_tool_result_chars:
                tool_name = msg.get("tool_name", msg.get("name", ""))
                old_len = len(content)
                msg["content"] = (
                    f"[Collapsed: {tool_name} result truncated]\n"
                    f"{content[-self.max_tool_result_chars:]}"
                )
                chars_saved += old_len - len(msg["content"])

        return messages, chars_saved

    def _dedup_tool_schemas(
        self, messages: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], int]:
        """去除 assistant 消息中 tool_calls 的冗余元信息。"""
        chars_saved = 0

        for msg in messages:
            if msg.get("role") != "assistant":
                continue
            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                continue

            for tc in tool_calls:
                if not isinstance(tc, dict):
                    continue
                func = tc.get("function", {})
                if not isinstance(func, dict):
                    continue
                # 去除 function 中过长的 description（如果有的话）
                desc = func.get("description", "")
                if len(desc) > 500:
                    old_len = len(desc)
                    func["description"] = desc[:500] + "...[truncated]"
                    chars_saved += old_len - len(func["description"])

        return messages, chars_saved
