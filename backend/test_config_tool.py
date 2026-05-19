"""
ConfigTool 功能测试

测试 list / get / set 操作及安全护栏。
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch


def _mock_setting(key, value, category, description=""):
    s = MagicMock()
    s.key = key
    s.value = value
    s.category = category
    s.description = description
    return s


def _mock_session_execute(return_value):
    """构建模拟 DB 调用的 mock session"""
    mock_result = MagicMock()
    if isinstance(return_value, list):
        mock_result.scalars.return_value.all.return_value = return_value
    else:
        mock_result.scalar_one_or_none.return_value = return_value

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session.commit = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    return mock_session


# patch target: the lazy import inside methods uses app.core.database.async_session_maker
DB_PATCH = "app.core.database.async_session_maker"


class TestConfigToolStructure:
    def test_tool_attributes(self):
        from app.modules.tools.config import ConfigTool
        tool = ConfigTool()
        assert tool.name == "config"
        assert tool.required == ["action"]

    def test_action_enum(self):
        from app.modules.tools.config import ConfigTool
        assert ConfigTool.parameters["action"].enum == ["list", "get", "set"]

    def test_definition_format(self):
        from app.modules.tools.config import ConfigTool
        d = ConfigTool().get_definition().to_openai_format()
        assert d["function"]["name"] == "config"


class TestConfigBlacklist:
    def test_write_blacklist(self):
        from app.modules.tools.config import _WRITE_BLACKLIST
        assert "token_expiry" in _WRITE_BLACKLIST
        assert "smtp_pass" in _WRITE_BLACKLIST

    def test_security_category(self):
        from app.modules.tools.config import _SECURITY_CATEGORY
        assert _SECURITY_CATEGORY == "security"


class TestConfigList:
    @pytest.mark.asyncio
    async def test_list_returns_json(self):
        from app.modules.tools.config import ConfigTool
        ms = _mock_session_execute([_mock_setting("system_name", "PioneClaw", "general", "系统名称")])
        with patch(DB_PATCH, return_value=ms):
            tool = ConfigTool()
            result = await tool.execute(action="list")
            data = json.loads(result)
            assert data["success"] is True
            assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_with_category_filter(self):
        from app.modules.tools.config import ConfigTool
        ms = _mock_session_execute([])
        with patch(DB_PATCH, return_value=ms):
            tool = ConfigTool()
            result = await tool.execute(action="list", category="general")
            data = json.loads(result)
            assert data["success"] is True
            assert data["category_filter"] == "general"


class TestConfigGet:
    @pytest.mark.asyncio
    async def test_get_missing_key(self):
        from app.modules.tools.config import ConfigTool
        tool = ConfigTool()
        result = await tool.execute(action="get")
        data = json.loads(result)
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self):
        from app.modules.tools.config import ConfigTool
        ms = _mock_session_execute(None)
        with patch(DB_PATCH, return_value=ms):
            tool = ConfigTool()
            result = await tool.execute(action="get", key="__nonexistent__")
            data = json.loads(result)
            assert data["success"] is False
            assert "不存在" in data["error"]

    @pytest.mark.asyncio
    async def test_get_existing_key(self):
        from app.modules.tools.config import ConfigTool
        ms = _mock_session_execute(_mock_setting("system_name", "PioneClaw", "general", "系统名称"))
        with patch(DB_PATCH, return_value=ms):
            tool = ConfigTool()
            result = await tool.execute(action="get", key="system_name")
            data = json.loads(result)
            assert data["success"] is True
            assert data["value"] == "PioneClaw"


class TestConfigSet:
    @pytest.mark.asyncio
    async def test_set_missing_key(self):
        from app.modules.tools.config import ConfigTool
        tool = ConfigTool()
        result = await tool.execute(action="set", value="test")
        data = json.loads(result)
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_set_blacklisted_key(self):
        from app.modules.tools.config import ConfigTool
        tool = ConfigTool()
        result = await tool.execute(action="set", key="token_expiry", value="9999")
        data = json.loads(result)
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_set_same_value(self):
        from app.modules.tools.config import ConfigTool
        ms = _mock_session_execute(_mock_setting("system_name", "PioneClaw", "general", "系统名称"))
        with patch(DB_PATCH, return_value=ms):
            tool = ConfigTool()
            result = await tool.execute(action="set", key="system_name", value="PioneClaw")
            data = json.loads(result)
            assert data["success"] is True
            assert "无需修改" in data["message"]

    @pytest.mark.asyncio
    async def test_set_general_direct_write(self):
        """general 类配置直接写入"""
        from app.modules.tools.config import ConfigTool
        ms = _mock_session_execute(_mock_setting("system_name", "PioneClaw", "general", "系统名称"))
        with patch(DB_PATCH, return_value=ms):
            tool = ConfigTool()
            result = await tool.execute(action="set", key="system_name", value="NewName")
            data = json.loads(result)
            assert data["success"] is True
            assert data["new_value"] == "NewName"

    @pytest.mark.asyncio
    async def test_set_security_needs_confirm_rejected(self):
        """security 类需确认，模拟拒绝"""
        from app.modules.tools.config import ConfigTool
        ms = _mock_session_execute(_mock_setting("debug_mode", "false", "security", "调试模式"))
        with patch(DB_PATCH, return_value=ms), \
             patch.object(ConfigTool, "_confirm_change", return_value=False):
            tool = ConfigTool()
            result = await tool.execute(action="set", key="debug_mode", value="true")
            data = json.loads(result)
            assert data["success"] is False
            assert "拒绝" in data["error"]

    @pytest.mark.asyncio
    async def test_set_security_needs_confirm_approved(self):
        """security 类需确认，模拟批准"""
        from app.modules.tools.config import ConfigTool
        ms = _mock_session_execute(_mock_setting("debug_mode", "false", "security", "调试模式"))
        with patch(DB_PATCH, return_value=ms), \
             patch.object(ConfigTool, "_confirm_change", return_value=True):
            tool = ConfigTool()
            result = await tool.execute(action="set", key="debug_mode", value="true")
            data = json.loads(result)
            assert data["success"] is True
            assert data["new_value"] == "true"


class TestInvalidAction:
    @pytest.mark.asyncio
    async def test_invalid_action(self):
        from app.modules.tools.config import ConfigTool
        tool = ConfigTool()
        result = await tool.execute(action="delete")
        data = json.loads(result)
        assert data["success"] is False
        assert "未知" in data["error"]
