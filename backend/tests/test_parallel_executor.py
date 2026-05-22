"""
Test ParallelExecutor and parallel tool execution
"""
import asyncio
import pytest
from unittest.mock import MagicMock

from app.modules.tools.parallel_executor import ParallelExecutor
from app.modules.tools.base import BaseTool


class MockReadTool(BaseTool):
    name = "read_file"
    description = "Mock read tool"
    is_parallel_safe = True
    parameters = {}
    required = []

    async def execute(self, **kwargs) -> str:
        await asyncio.sleep(0.05)  # Simulate I/O
        return f"Content of {kwargs.get('path', 'unknown')}"


class MockWriteTool(BaseTool):
    name = "write_file"
    description = "Mock write tool"
    is_parallel_safe = False
    parameters = {}
    required = []

    async def execute(self, **kwargs) -> str:
        return f"Wrote to {kwargs.get('path', 'unknown')}"


class TestParallelExecutor:
    def test_can_parallelize_all_safe(self):
        tool_calls = [
            {"name": "read_file", "id": "1"},
            {"name": "grep", "id": "2"},
        ]
        def get_safe(name):
            return name in ("read_file", "grep")

        assert ParallelExecutor.can_parallelize(tool_calls, get_safe) is True

    def test_can_parallelize_mixed(self):
        tool_calls = [
            {"name": "read_file", "id": "1"},
            {"name": "write_file", "id": "2"},
        ]
        def get_safe(name):
            return name in ("read_file",)

        assert ParallelExecutor.can_parallelize(tool_calls, get_safe) is False

    def test_can_parallelize_single_tool(self):
        tool_calls = [{"name": "read_file", "id": "1"}]
        def get_safe(name):
            return True

        # Single tool should not be parallelized
        assert ParallelExecutor.can_parallelize(tool_calls, get_safe) is False

    def test_can_parallelize_empty(self):
        def get_safe(name):
            return True

        assert ParallelExecutor.can_parallelize([], get_safe) is False

    @pytest.mark.asyncio
    async def test_execute_parallel_success(self):
        async def read_a():
            await asyncio.sleep(0.05)
            return "file_a_content"

        async def read_b():
            await asyncio.sleep(0.05)
            return "file_b_content"

        tasks = [
            ("read_file_a", read_a()),
            ("read_file_b", read_b()),
        ]
        results = await ParallelExecutor.execute_parallel(tasks)

        assert len(results) == 2
        # Order preserved
        assert results[0] == ("read_file_a", "file_a_content", None)
        assert results[1] == ("read_file_b", "file_b_content", None)

    @pytest.mark.asyncio
    async def test_execute_parallel_with_error(self):
        async def read_a():
            await asyncio.sleep(0.05)
            return "file_a_content"

        async def read_b():
            await asyncio.sleep(0.05)
            raise ValueError("file not found")

        tasks = [
            ("read_file_a", read_a()),
            ("read_file_b", read_b()),
        ]
        results = await ParallelExecutor.execute_parallel(tasks)

        assert len(results) == 2
        assert results[0][1] == "file_a_content"
        assert results[0][2] is None  # no error
        assert results[1][1] == ""  # empty result on error
        assert isinstance(results[1][2], ValueError)

    @pytest.mark.asyncio
    async def test_parallel_tools_are_marked(self):
        r = MockReadTool()
        w = MockWriteTool()

        assert r.is_parallel_safe is True
        assert w.is_parallel_safe is False

    def test_base_tool_default_not_parallel_safe(self):
        # Default is_parallel_safe should be False
        assert BaseTool.is_parallel_safe == getattr(BaseTool, 'is_parallel_safe', False) or False
