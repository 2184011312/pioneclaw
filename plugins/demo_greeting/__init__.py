"""
Demo Greeting Plugin - 演示问候插件
"""
from app.modules.plugins.sdk.plugin_entry import PioneClawPlugin, plugin_metadata
from app.modules.plugins.sdk.event_types import PluginEvent


@plugin_metadata(
    id="demo_greeting",
    name="Greeting Plugin",
    version="1.0.0",
    description="A demo plugin that greets users on agent start",
)
class GreetingPlugin(PioneClawPlugin):
    async def on_load(self) -> None:
        print(f"[GreetingPlugin v{self.version}] Loaded successfully!")

    async def on_unload(self) -> None:
        print("[GreetingPlugin] Unloaded. Goodbye!")

    async def on_event(self, event: PluginEvent) -> None:
        if event.type.value == "agent_start":
            print(f"[GreetingPlugin] Agent started! Hello!")
