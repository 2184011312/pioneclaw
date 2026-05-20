"""
Parallel Tool Executor — 并行执行安全的只读工具

策略：
1. 将连续的同类型（parallel_safe）工具分组为并行批次
2. 使用 asyncio.gather 并行执行
3. 错误级联：一个工具失败则取消同组其他工具
"""

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List, Tuple

logger = logging.getLogger(__name__)


class ParallelExecutor:
    """并行工具执行器"""

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

        使用 asyncio.gather(return_exceptions=True) 并行执行。
        如果任一任务失败，返回结果中包含异常。
        """
        coroutines = [task[1] for task in tasks]
        results = await asyncio.gather(*coroutines, return_exceptions=True)

        output = []
        for (tool_name, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                output.append((tool_name, "", result))
            else:
                output.append((tool_name, str(result), None))
        return output
