"""
独立工具执行器 - 从 AgentLoop 提取的完整生命周期

执行流程：
1. Schema 验证（可选，上层已通过 LLM 初步验证）
2. Pre-tool hooks
3. Permission resolution（4-layer cascade）
4. Tool execution
5. Post-tool hooks
6. Result transformation hooks
7. Max result size enforcement
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.modules.tools.hooks import HookManager
from app.modules.tools.permissions import resolve_permission
from app.modules.tools.types import (
    PermissionMode,
    PermissionRule,
    ToolContext,
    ToolDef,
    ToolResult,
    ToolUse,
)

logger = logging.getLogger(__name__)


async def execute_tool(
    tool_use: ToolUse,
    tool: ToolDef,
    ctx: ToolContext,
    rules: list[PermissionRule],
    mode: PermissionMode,
    hooks: HookManager,
) -> ToolResult:
    """执行单个工具调用，包含完整生命周期"""
    tool_use_id = tool_use.id

    # ---- 1. Pre-tool hooks ----
    from app.modules.tools.types import HookContext

    pre_hook = await hooks.run(
        "pre_tool_use",
        HookContext(tool=tool, input=tool_use.input, ctx=ctx),
    )
    if pre_hook.block:
        return ToolResult(
            output=f"Blocked: {pre_hook.message or 'pre_tool_use hook'}",
            metadata={"blocked": True, "hook": "pre_tool_use", "tool_use_id": tool_use_id},
        )

    # ---- 2. Permission resolution ----
    permission = await resolve_permission(tool, tool_use.input, ctx, rules, mode)
    if permission.behavior != "allow":
        return ToolResult(
            output=f"Permission {permission.behavior}: {permission.message or permission.reason or tool.id}",
            metadata={
                "permission_denied": True,
                "behavior": permission.behavior,
                "reason": permission.reason,
                "tool_use_id": tool_use_id,
            },
        )

    # Use updated input from permission if provided
    call_input = permission.updated_input if permission.updated_input is not None else tool_use.input

    # ---- 3. Execute ----
    try:
        # 优先调用新接口 execute_new（BaseTool 已实现自动转换）
        if hasattr(tool, "execute_new"):
            result = await tool.execute_new(call_input, ctx)
        else:
            # 兜底：直接调用旧接口
            raw = await tool.execute(**call_input)
            result = ToolResult(output=str(raw) if raw is not None else "")
    except Exception as exc:
        msg = str(exc)
        logger.error(f"Tool {tool.id} execution error: {msg}")
        result = ToolResult(
            output=f"Error: {msg}",
            metadata={"error": True, "tool_use_id": tool_use_id},
        )

    # ---- 4. Max result size enforcement ----
    max_size = getattr(tool, "max_result_size", 0)
    if max_size and max_size > 3 and len(result.output) > max_size:
        result.output = result.output[: max_size - 3] + "..."
        result.metadata = {**result.metadata, "truncated": True}

    # ---- 5. Post-tool hooks ----
    await hooks.run(
        "post_tool_use",
        HookContext(tool=tool, input=call_input, result=result, ctx=ctx),
    )

    # ---- 6. Transform result hooks ----
    transform_hook = await hooks.run(
        "transform_result",
        HookContext(tool=tool, input=call_input, result=result, ctx=ctx),
    )
    if transform_hook.transformed_result is not None:
        result = transform_hook.transformed_result

    return result
