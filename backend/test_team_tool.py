"""
TeamCreateTool + TeamDeleteTool 功能测试

测试团队注册表、创建/删除工具、send_to_team 群发。
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

DB_PATCH = "app.core.database.async_session_maker"


def _cleanup_teams():
    from app.modules.tools.team import _teams
    _teams.clear()


def _cleanup_agents():
    from app.modules.tools.send_message import _agent_inboxes, _agent_metadata
    _agent_inboxes.clear()
    _agent_metadata.clear()


class TestTeamRegistry:
    """团队注册表功能测试"""

    def setup_method(self):
        _cleanup_teams()

    def teardown_method(self):
        _cleanup_teams()

    def test_register_team(self):
        from app.modules.tools.team import register_team, get_team
        register_team("t1", "Team A", ["a1", "a2"], "Desc")
        team = get_team("t1")
        assert team is not None
        assert team["name"] == "Team A"
        assert team["member_agent_ids"] == ["a1", "a2"]

    def test_unregister_team(self):
        from app.modules.tools.team import register_team, unregister_team
        register_team("t2", "Team B")
        assert unregister_team("t2") is True
        assert unregister_team("__nonexistent__") is False

    def test_add_team_member(self):
        from app.modules.tools.team import register_team, add_team_member, get_team
        register_team("t3", "Team C", ["a1"])
        add_team_member("t3", "a2")
        team = get_team("t3")
        assert "a2" in team["member_agent_ids"]
        # Duplicate add is idempotent
        add_team_member("t3", "a2")
        assert team["member_agent_ids"].count("a2") == 1

    def test_remove_team_member(self):
        from app.modules.tools.team import register_team, remove_team_member, get_team
        register_team("t4", "Team D", ["a1", "a2"])
        remove_team_member("t4", "a1")
        team = get_team("t4")
        assert "a1" not in team["member_agent_ids"]
        assert "a2" in team["member_agent_ids"]

    def test_list_teams(self):
        from app.modules.tools.team import register_team, list_teams
        register_team("t5", "Team E")
        register_team("t6", "Team F")
        teams = list_teams()
        assert len(teams) >= 2

    def test_send_to_team(self):
        from app.modules.tools.team import register_team, send_to_team
        from app.modules.tools.send_message import register_agent
        _cleanup_agents()

        # Register agents first
        register_agent("a1", "Agent 1")
        register_agent("a2", "Agent 2")

        register_team("t7", "Team G", ["a1", "a2"])
        result = send_to_team("t7", {"from": "test", "message": "hello team"})
        assert result["success"] is True
        assert result["delivered"] == 2
        assert result["failed"] == 0

        _cleanup_agents()

    def test_send_to_nonexistent_team(self):
        from app.modules.tools.team import send_to_team
        result = send_to_team("__nonexistent__", {"from": "test", "message": "hi"})
        assert result["success"] is False


class TestTeamCreateTool:
    """TeamCreateTool 执行测试"""

    @pytest.mark.asyncio
    async def test_create_team_basic(self):
        from app.modules.tools.team import TeamCreateTool
        _cleanup_teams()

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch(DB_PATCH, return_value=mock_session):
            tool = TeamCreateTool()
            result = await tool.execute(name="Test Team")
            data = json.loads(result)
            assert data["success"] is True
            assert data["name"] == "Test Team"
            assert data["member_count"] == 0

        _cleanup_teams()

    @pytest.mark.asyncio
    async def test_create_team_with_members(self):
        from app.modules.tools.team import TeamCreateTool
        _cleanup_teams()

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch(DB_PATCH, return_value=mock_session):
            tool = TeamCreateTool()
            result = await tool.execute(
                name="Team With Members",
                member_agent_ids='["a1", "a2"]',
            )
            data = json.loads(result)
            assert data["success"] is True
            assert data["member_count"] == 2
            assert data["members"] == ["a1", "a2"]

        _cleanup_teams()

    @pytest.mark.asyncio
    async def test_create_team_invalid_members_json(self):
        from app.modules.tools.team import TeamCreateTool
        _cleanup_teams()

        tool = TeamCreateTool()
        result = await tool.execute(name="Bad Team", member_agent_ids="not-json")
        data = json.loads(result)
        assert data["success"] is False
        assert "JSON" in data["error"]

        _cleanup_teams()


class TestTeamDeleteTool:
    """TeamDeleteTool 执行测试"""

    @pytest.mark.asyncio
    async def test_delete_nonexistent_team(self):
        from app.modules.tools.team import TeamDeleteTool
        _cleanup_teams()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch(DB_PATCH, return_value=mock_session):
            tool = TeamDeleteTool()
            result = await tool.execute(team_id="__nonexistent__")
            data = json.loads(result)
            assert data["success"] is False

    @pytest.mark.asyncio
    async def test_delete_team_from_runtime(self):
        from app.modules.tools.team import TeamDeleteTool, register_team
        _cleanup_teams()

        register_team("t-del", "To Delete")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch(DB_PATCH, return_value=mock_session):
            tool = TeamDeleteTool()
            result = await tool.execute(team_id="t-del")
            data = json.loads(result)
            assert data["success"] is True
            assert data["runtime_removed"] is True

        _cleanup_teams()


class TestSendMessageSendToTeam:
    """SendMessageTool 的 send_to_team 操作测试"""

    def setup_method(self):
        _cleanup_teams()
        _cleanup_agents()

    def teardown_method(self):
        _cleanup_teams()
        _cleanup_agents()

    @pytest.mark.asyncio
    async def test_send_to_team_action(self):
        from app.modules.tools.send_message import SendMessageTool, register_agent
        from app.modules.tools.team import register_team

        register_agent("a1", "Agent 1")
        register_agent("a2", "Agent 2")
        register_team("t-msg", "Msg Team", ["a1", "a2"])

        tool = SendMessageTool()
        result = await tool.execute(action="send_to_team", team_id="t-msg", message="hello")
        data = json.loads(result)
        assert data["success"] is True
        assert data["delivered"] == 2

    @pytest.mark.asyncio
    async def test_send_to_team_missing_team_id(self):
        from app.modules.tools.send_message import SendMessageTool
        tool = SendMessageTool()
        result = await tool.execute(action="send_to_team", message="hi")
        data = json.loads(result)
        assert data["success"] is False
        assert "team_id" in data["error"]

    @pytest.mark.asyncio
    async def test_send_to_team_missing_message(self):
        from app.modules.tools.send_message import SendMessageTool
        tool = SendMessageTool()
        result = await tool.execute(action="send_to_team", team_id="t1")
        data = json.loads(result)
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_action_enum_includes_send_to_team(self):
        from app.modules.tools.send_message import SendMessageTool
        param = SendMessageTool.parameters["action"]
        assert "send_to_team" in param.enum


class TestToolStructure:
    """工具结构测试"""

    def test_team_create_structure(self):
        from app.modules.tools.team import TeamCreateTool
        tool = TeamCreateTool()
        assert tool.name == "team_create"
        assert tool.required == ["name"]

    def test_team_delete_structure(self):
        from app.modules.tools.team import TeamDeleteTool
        tool = TeamDeleteTool()
        assert tool.name == "team_delete"
        assert tool.required == ["team_id"]

    def test_definitions(self):
        from app.modules.tools.team import TeamCreateTool, TeamDeleteTool
        d1 = TeamCreateTool().get_definition().to_openai_format()
        assert d1["function"]["name"] == "team_create"
        d2 = TeamDeleteTool().get_definition().to_openai_format()
        assert d2["function"]["name"] == "team_delete"
