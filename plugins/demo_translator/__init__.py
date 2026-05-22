"""
Demo Translator Plugin - 演示翻译插件
"""
from app.modules.plugins.sdk.plugin_entry import PioneClawPlugin, plugin_metadata
from app.modules.plugins.sdk.event_types import PluginEvent


@plugin_metadata(
    id="demo_translator",
    name="Translator Plugin",
    version="2.0.0",
    description="A demo plugin for real-time text translation (stub)",
)
class TranslatorPlugin(PioneClawPlugin):
    async def on_load(self) -> None:
        print(f"[TranslatorPlugin v{self.version}] Translation engine initialized!")

    async def on_unload(self) -> None:
        print("[TranslatorPlugin] Translation engine stopped.")

    async def on_event(self, event: PluginEvent) -> None:
        if event.type.value == "message_received":
            text = event.data.get("text", "")
            print(f"[TranslatorPlugin] Received message: {text[:50]}...")
