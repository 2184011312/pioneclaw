"""
工具基类 - 定义工具的基本接口

所有工具都继承自 BaseTool，实现 execute 方法。
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ToolParameter(BaseModel):
    """工具参数定义"""
    type: str = "string"
    description: str = ""
    enum: Optional[list[str]] = None
    default: Optional[Any] = None


@dataclass
class ToolDefinition:
    """工具定义 - OpenAI Function Calling 格式"""
    name: str
    description: str
    parameters: dict[str, Any]
    required: list[str] = field(default_factory=list)
    
    def to_openai_format(self) -> dict[str, Any]:
        """转换为 OpenAI Function Calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": self.required,
                }
            }
        }


class BaseTool(ABC):
    """
    工具基类
    
    所有工具都需要继承此类并实现：
    - name: 工具名称
    - description: 工具描述
    - parameters: 参数定义
    - execute(): 执行方法
    """
    
    name: str = "base_tool"
    description: str = "Base tool class"
    parameters: dict[str, ToolParameter] = {}
    required: list[str] = []
    
    def get_definition(self) -> ToolDefinition:
        """获取工具定义"""
        params = {
            name: {
                "type": param.type,
                "description": param.description,
                **({"enum": param.enum} if param.enum else {}),
                **({"default": param.default} if param.default is not None else {}),
            }
            for name, param in self.parameters.items()
        }
        
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=params,
            required=self.required,
        )
    
    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """
        执行工具
        
        Args:
            **kwargs: 工具参数
        
        Returns:
            str: 执行结果
        """
        pass
    
    def validate_arguments(self, arguments: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        验证参数

        Args:
            arguments: 参数字典

        Returns:
            tuple: (是否有效, 错误信息)
        """
        # 检查必需参数
        for req in self.required:
            if req not in arguments:
                param_info = self.parameters.get(req)
                desc = f"{req}"
                if param_info:
                    desc = f"{req}({param_info.type}): {param_info.description}"
                return False, (
                    f"缺少必填参数 {desc}。"
                    f"请提供 '{req}' 参数后重试调用 {self.name}。"
                )

        return True, None
