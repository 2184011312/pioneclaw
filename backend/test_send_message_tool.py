"""
SendMessageTool 功能测试

测试收件箱注册表 + SendMessageTool (list_agents / send 操作)。
"""
import asyncio
import json
import pytest
from datetime import datetime


class TestInboxRegistry:
    """收件箱注册表功能测试"""

    def test_register_agent(self):
        from app.modules.tools.send_message import (
            register_agent, unregister_agent, list_agents, _agent_inboxes, _agent_metadata,
        )
        # Clean slate for test
        aid = "test-register-1"
        # Pre-clean
        _agent_inboxes.pop(aid, None)
        _agent_metadata.pop(aid, None)

        queue = register_agent(aid, label="Test Agent")
        assert isinstance(queue, asyncio.Queue)
        assert aid in _agent_inboxes
        assert _agent_metadata[aid]["status"] == "running"
        assert _agent_metadata[aid]["label"] == "Test Agent"

        # Cleanup
        _agent_inboxes.pop(aid, None)
        _agent_metadata.pop(aid, None)

    def test_unregister_agent(self):
        from app.modules.tools.send_message import (
            register_agent, unregister_agent, _agent_inboxes, _agent_metadata,
        )
        aid = "test-unregister-1"
        _agent_inboxes.pop(aid, None)
        _agent_metadata.pop(aid, None)

        register_agent(aid, label="Test")
        assert aid in _agent_inboxes

        unregister_agent(aid)
        assert aid not in _agent_inboxes
        assert _agent_metadata[aid]["status"] == "completed"

        _agent_inboxes.pop(aid, None)
        _agent_metadata.pop(aid, None)

    def test_send_to_agent_existing(self):
        from app.modules.tools.send_message import (
            register_agent, unregister_agent, send_to_agent, _agent_inboxes, _agent_metadata,
        )
        aid = "test-send-1"
        _agent_inboxes.pop(aid, None)
        _agent_metadata.pop(aid, None)

        register_agent(aid, label="Target")
        ok = send_to_agent(aid, {"from": "test", "message": "hello"})
        assert ok is True

        # Verify message in queue
        queue = _agent_inboxes.get(aid)
        msg = queue.get_nowait()
        assert msg["message"] == "hello"

        _agent_inboxes.pop(aid, None)
        _agent_metadata.pop(aid, None)

    def test_send_to_agent_nonexistent(self):
        from app.modules.tools.send_message import send_to_agent
        ok = send_to_agent("__nonexistent__", {"from": "test", "message": "hi"})
        assert ok is False

    def test_list_agents(self):
        from app.modules.tools.send_message import (
            register_agent, unregister_agent, list_agents, _agent_inboxes, _agent_metadata,
        )
        aid = "test-list-1"
        _agent_inboxes.pop(aid, None)
        _agent_metadata.pop(aid, None)

        register_agent(aid, label="Listable")
        agents = list_agents()
        assert any(a["agent_id"] == aid for a in agents)

        _agent_inboxes.pop(aid, None)
        _agent_metadata.pop(aid, None)


class TestSendMessageTool:
    """SendMessageTool 执行测试"""

    @pytest.mark.asyncio
    async def test_list_agents_action(self):
        from app.modules.tools.send_message import (
            SendMessageTool, register_agent, _agent_inboxes, _agent_metadata,
        )
        aid = "test-tool-list-1"
        _agent_inboxes.pop(aid, None)
        _agent_metadata.pop(aid, None)
        register_agent(aid, label="Agent A")

        tool = SendMessageTool()
        result = await tool.execute(action="list_agents")
        data = json.loads(result)
        assert data["success"] is True
        assert data["total"] >= 1
        assert any(a["agent_id"] == aid for a in data["agents"])

        _agent_inboxes.pop(aid, None)
        _agent_metadata.pop(aid, None)

    @pytest.mark.asyncio
    async def test_send_to_existing_agent(self):
        from app.modules.tools.send_message import (
            SendMessageTool, register_agent, send_to_agent,
            _agent_inboxes, _agent_metadata,
        )
        aid = "test-tool-send-1"
        _agent_inboxes.pop(aid, None)
        _agent_metadata.pop(aid, None)
        register_agent(aid, label="Target")

        tool = SendMessageTool()
        result = await tool.execute(
            action="send", target_agent=aid, message="Hello from test",
            sender_id="test-sender",
        )
        data = json.loads(result)
        assert data["success"] is True
        assert data["target_agent"] == aid

        # Verify the message arrived
        from app.modules.tools.send_message import _agent_inboxes as boxes
        queue = boxes.get(aid)
        msg = queue.get_nowait()
        assert msg["message"] == "Hello from test"
        assert msg["from"] == "test-sender"

        _agent_inboxes.pop(aid, None)
        _agent_metadata.pop(aid, None)

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_agent(self):
        from app.modules.tools.send_message import SendMessageTool
        tool = SendMessageTool()
        result = await tool.execute(
            action="send", target_agent="__nonexistent__", message="Hi",
        )
        data = json.loads(result)
        assert data["success"] is False
        assert "available_agents" in data

    @pytest.mark.asyncio
    async def test_send_missing_target(self):
        from app.modules.tools.send_message import SendMessageTool
        tool = SendMessageTool()
        result = await tool.execute(action="send")
        data = json.loads(result)
        assert data["success"] is False
        assert "target_agent" in data["error"]

    @pytest.mark.asyncio
    async def test_send_missing_message(self):
        from app.modules.tools.send_message import SendMessageTool
        tool = SendMessageTool()
        result = await tool.execute(action="send", target_agent="someone")
        data = json.loads(result)
        assert data["success"] is False
        assert "message" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_invalid_action(self):
        from app.modules.tools.send_message import SendMessageTool
        tool = SendMessageTool()
        result = await tool.execute(action="invalid_action")
        data = json.loads(result)
        assert data["success"] is False
        assert "未知" in data.get("error", "")


class TestAgentLoopInbox:
    """AgentLoop 收件箱集成测试（无 LLM）"""

    @pytest.mark.asyncio
    async def test_inbox_queue_assigned(self):
        """验证 inbox_queue 参数被正确保存"""
        import asyncio
        from app.modules.agent.loop import AgentLoop

        q = asyncio.Queue()
        loop = AgentLoop(
            provider=None,
            inbox_queue=q,
        )
        assert loop._inbox_queue is q

    @pytest.mark.asyncio
    async def test_no_inbox_is_none(self):
        """默认无 inbox_queue 时为 None"""
        from app.modules.agent.loop import AgentLoop
        loop = AgentLoop(provider=None)
        assert loop._inbox_queue is None


class TestToolStructure:
    """SendMessageTool 结构测试"""

    def test_tool_attributes(self):
        from app.modules.tools.send_message import SendMessageTool
        tool = SendMessageTool()
        assert tool.name == "send_message"
        assert tool.required == ["action"]
        assert "action" in tool.parameters
        assert "target_agent" in tool.parameters
        assert "message" in tool.parameters

    def test_action_enum(self):
        from app.modules.tools.send_message import SendMessageTool
        param = SendMessageTool.parameters["action"]
        assert param.enum == ["send", "list_agents"]

    def test_definition_format(self):
        from app.modules.tools.send_message import SendMessageTool
        d = SendMessageTool().get_definition().to_openai_format()
        assert d["type"] == "function"
        assert d["function"]["name"] == "send_message"
