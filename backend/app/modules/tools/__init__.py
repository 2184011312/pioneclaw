"""
Tools 模块 - 工具系统

包含：
- BaseTool: 工具基类
- ToolRegistry: 工具注册表
- builtin: 内置工具集
"""

from app.modules.tools.base import (
    BaseTool,
    ToolParameter,
    ToolDefinition,
)
from app.modules.tools.registry import (
    ToolRegistry,
    get_tool_registry,
    register_tool,
    register_tool_class,
)
from typing import Optional

from app.modules.tools.builtin import (
    CurrentTimeTool,
    CalculatorTool,
    ReadFileTool,
    WriteFileTool,
    register_builtin_tools,
)
from app.modules.tools.web import WebSearchTool
from app.modules.tools.task_create import TaskCreateTool
from app.modules.tools.task_get import TaskGetTool
from app.modules.tools.task_list import TaskListTool
from app.modules.tools.task_update import TaskUpdateTool
from app.modules.tools.task_stop import TaskStopTool
from app.modules.tools.task_output import TaskOutputTool
from app.modules.tools.todo_write import TodoWriteTool

__all__ = [
    # Base
    "BaseTool",
    "ToolParameter",
    "ToolDefinition",
    # Registry
    "ToolRegistry",
    "get_tool_registry",
    "register_tool",
    "register_tool_class",
    # Built-in tools
    "CurrentTimeTool",
    "CalculatorTool",
    "WebSearchTool",
    "ReadFileTool",
    "WriteFileTool",
    "register_builtin_tools",
    # Task tools (UU.1)
    "TaskCreateTool",
    "TaskGetTool",
    "TaskListTool",
    "TaskUpdateTool",
    "TaskStopTool",
    "TaskOutputTool",
    "TodoWriteTool",
]