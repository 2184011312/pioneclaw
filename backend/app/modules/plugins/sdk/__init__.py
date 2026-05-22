"""
PioneClaw Plugin SDK

第三方插件开发者只需 import pioneclaw.plugins.sdk（或 app.modules.plugins.sdk）

提供：
- PioneClawPlugin 基类
- plugin_metadata 装饰器
- 事件类型定义
- 运行时 API（事件总线、配置、数据库）
"""

from .plugin_entry import PioneClawPlugin, plugin_metadata
from .event_types import PluginEvent, EventType
from .plugin_runtime import (
    get_event_bus,
    get_config,
    get_db_session,
    set_runtime_context,
    clear_runtime_context,
)

__all__ = [
    "PioneClawPlugin",
    "plugin_metadata",
    "PluginEvent",
    "EventType",
    "get_event_bus",
    "get_config",
    "get_db_session",
    "set_runtime_context",
    "clear_runtime_context",
]
