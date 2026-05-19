"""
工具注册表 - 管理和执行工具

功能：
- 注册工具
- 获取工具定义（OpenAI Function Calling 格式）
- 执行工具调用
"""

import asyncio
import logging
from typing import Any, Optional, Type
from app.modules.tools.base import BaseTool, ToolDefinition
from app.core.recovery_recipes import RecoverableToolError

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    工具注册表
    
    管理所有可用工具，提供：
    - 工具注册
    - 工具定义获取
    - 工具执行
    """
    
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._session_id: Optional[str] = None
        self._channel: Optional[str] = None
        self._cancel_token = None
        
        logger.debug("ToolRegistry initialized")
    
    def register(self, tool: BaseTool) -> None:
        """
        注册工具
        
        Args:
            tool: 工具实例
        """
        self._tools[tool.name] = tool
        logger.debug(f"Tool registered: {tool.name}")
    
    def register_class(self, tool_class: Type[BaseTool]) -> None:
        """
        注册工具类（自动实例化）
        
        Args:
            tool_class: 工具类
        """
        tool = tool_class()
        self.register(tool)
    
    def unregister(self, name: str) -> bool:
        """
        注销工具
        
        Args:
            name: 工具名称
        
        Returns:
            bool: 是否成功
        """
        if name in self._tools:
            del self._tools[name]
            logger.debug(f"Tool unregistered: {name}")
            return True
        return False
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        获取工具
        
        Args:
            name: 工具名称
        
        Returns:
            BaseTool: 工具实例，不存在则返回 None
        """
        return self._tools.get(name)
    
    def get_definitions(self) -> list[dict[str, Any]]:
        """
        获取所有工具定义（OpenAI Function Calling 格式）
        
        Returns:
            list: 工具定义列表
        """
        return [
            tool.get_definition().to_openai_format()
            for tool in self._tools.values()
        ]
    
    def list_tools(self) -> list[str]:
        """
        列出所有工具名称
        
        Returns:
            list: 工具名称列表
        """
        return list(self._tools.keys())
    
    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        auto_record: bool = True,
    ) -> str:
        """
        执行工具
        
        Args:
            name: 工具名称
            arguments: 工具参数
            auto_record: 是否自动记录（暂未实现）
        
        Returns:
            str: 执行结果
        """
        tool = self.get_tool(name)
        if not tool:
            error_msg = f"Tool not found: {name}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        
        # 验证参数
        valid, error = tool.validate_arguments(arguments)
        if not valid:
            logger.error(f"Tool {name} validation failed: {error}")
            return f"Error: {error}"
        
        # 检查取消令牌
        if self._cancel_token and self._cancel_token.is_cancelled:
            return "Error: Execution cancelled"
        
        logger.info(f"Executing tool: {name} with arguments: {arguments}")
        
        try:
            result = await tool.execute(**arguments)
            logger.debug(f"Tool {name} result: {result[:100] if len(result) > 100 else result}")
            return result
        except RecoverableToolError:
            raise  # 透传给 AgentLoop 的恢复系统处理
        except Exception as e:
            error_msg = f"Tool execution failed: {name} - {e}"
            logger.error(error_msg)
            return f"Error: {e}"
    
    def set_session_id(self, session_id: str) -> None:
        """设置会话 ID"""
        self._session_id = session_id
    
    def set_channel(self, channel: Optional[str]) -> None:
        """设置渠道"""
        self._channel = channel
    
    def set_cancel_token(self, cancel_token) -> None:
        """设置取消令牌"""
        self._cancel_token = cancel_token
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        return name in self._tools


# 全局工具注册表实例
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(tool: BaseTool) -> None:
    """注册工具到全局注册表"""
    get_tool_registry().register(tool)


def register_tool_class(tool_class: Type[BaseTool]) -> None:
    """注册工具类到全局注册表"""
    get_tool_registry().register_class(tool_class)
