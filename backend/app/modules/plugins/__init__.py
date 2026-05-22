"""
插件系统

提供插件发现、加载、卸载、事件订阅/发布功能。
"""

from .event_bus import EventBus, EventHandler
from .manager import PluginManager, PluginInfo, PluginState
from .lifecycle import PluginLifecycle, StateTransition
from .sdk import (
    PioneClawPlugin,
    plugin_metadata,
    PluginEvent,
    EventType,
    get_event_bus,
    get_config,
    get_db_session,
    set_runtime_context,
    clear_runtime_context,
)

__all__ = [
    "EventBus",
    "EventHandler",
    "PluginManager",
    "PluginInfo",
    "PluginState",
    "PluginLifecycle",
    "StateTransition",
    # SDK
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
