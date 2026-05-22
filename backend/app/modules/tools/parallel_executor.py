"""
[已废弃] Parallel Tool Executor

功能已合并到 scheduler.py：
- partition_tool_calls() 替代 can_parallelize()
- run_concurrent_batch() 替代 execute_parallel()

保留本文件仅作兼容导入，将在后续版本中移除。
"""

from __future__ import annotations

import logging
import warnings
from typing import Any, Awaitable, Callable, Dict, List, Tuple

from app.modules.tools.scheduler import run_concurrent_batch

logger = logging.getLogger(__name__)

warnings.warn(
    "parallel_executor.py is deprecated. Use app.modules.tools.scheduler instead.",
    DeprecationWarning,
    stacklevel=2,
)


class ParallelExecutor:
    """并行工具执行器（已废弃，功能移入 scheduler.py）"""

    @staticmethod
    def can_parallelize(
        tool_calls: List[Dict[str, Any]],
        get_tool_safe: Callable[[str], bool],
    ) -> bool:
        """判断一批工具调用是否可以全部并行执行"""
        for tc in tool_calls:
            name = tc.get("name", "")
            if not get_tool_safe(name):
                return False
        return len(tool_calls) > 1

    @staticmethod
    async def execute_parallel(
        tasks: List[Tuple[str, Awaitable[str]]],
    ) -> List[Tuple[str, str, Exception]]:
        """
        并行执行工具，返回 (tool_name, result, exception) 列表

        已废弃：请使用 scheduler.run_concurrent_batch()
        """
        logger.warning("ParallelExecutor.execute_parallel is deprecated. Use scheduler.run_concurrent_batch().")

        async def executor(item):
            tool_name, coro = item
            try:
                result = await coro
                return (tool_name, str(result), None)
            except Exception as exc:
                return (tool_name, "", exc)

        return await run_concurrent_batch(tasks, executor)
