"""
Demo Logger Plugin - 演示日志插件
"""
from app.modules.plugins.sdk.plugin_entry import PioneClawPlugin, plugin_metadata
from app.modules.plugins.sdk.event_types import PluginEvent


@plugin_metadata(
    id="demo_logger",
    name="Logger Plugin",
    version="1.0.0",
    description="A demo plugin that logs tool execution events",
    dependencies=[],
)
class LoggerPlugin(PioneClawPlugin):
    async def on_load(self) -> None:
        print(f"[LoggerPlugin v{self.version}] Logger ready!")

    async def on_unload(self) -> None:
        print("[LoggerPlugin] Shutting down logger...")

    async def on_event(self, event: PluginEvent) -> None:
        if event.type.value.startswith("tool_"):
            print(f"[LoggerPlugin] Tool event: {event.type.value} - {event.data}")
