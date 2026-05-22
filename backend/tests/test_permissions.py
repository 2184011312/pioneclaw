"""
权限系统单元测试
"""

from __future__ import annotations

import pytest

from app.modules.tools.permissions import match_rule, resolve_permission
from app.modules.tools.types import (
    PermissionBehavior,
    PermissionMode,
    PermissionRequest,
    PermissionResult,
    PermissionRule,
    ToolContext,
)


class FakeTool:
    id = "read_file"
    parameters = {}

    def check_permissions(self, input, ctx):
        return PermissionResult(behavior="ask")


class FakeToolAllow:
    id = "write_file"

    def check_permissions(self, input, ctx):
        return PermissionResult(behavior="allow", reason="tool_allow")


@pytest.fixture
def ctx():
    return ToolContext(
        session_id="s1",
        message_id="m1",
        working_dir="/tmp",
    )


# ------------------------------------------------------------------
# match_rule
# ------------------------------------------------------------------

class TestMatchRule:
    def test_exact_tool_match_no_pattern(self):
        rules = [PermissionRule(tool="read_file", behavior=PermissionBehavior.ALLOW)]
        assert match_rule("read_file", {}, rules) is not None
        assert match_rule("write_file", {}, rules) is None

    def test_wildcard_tool(self):
        rules = [PermissionRule(tool="*", behavior=PermissionBehavior.DENY)]
        assert match_rule("anything", {}, rules) is not None

    def test_pattern_exact_match(self):
        rules = [PermissionRule(tool="read_file", pattern="/etc/passwd", behavior=PermissionBehavior.DENY)]
        assert match_rule("read_file", {"file_path": "/etc/passwd"}, rules) is not None
        assert match_rule("read_file", {"file_path": "/tmp/test"}, rules) is None

    def test_pattern_prefix_match(self):
        rules = [PermissionRule(tool="exec", pattern="rm *", behavior=PermissionBehavior.DENY)]
        assert match_rule("exec", {"command": "rm -rf /"}, rules) is not None
        assert match_rule("exec", {"command": "ls -la"}, rules) is None

    def test_no_match_when_tool_differs(self):
        rules = [PermissionRule(tool="read_file", pattern="/tmp/*", behavior=PermissionBehavior.ALLOW)]
        assert match_rule("write_file", {"file_path": "/tmp/test"}, rules) is None


# ------------------------------------------------------------------
# resolve_permission
# ------------------------------------------------------------------

class TestResolvePermission:
    @pytest.mark.asyncio
    async def test_layer1_deny(self, ctx):
        rules = [PermissionRule(tool="read_file", behavior=PermissionBehavior.DENY)]
        result = await resolve_permission(FakeTool(), {}, ctx, rules, "default")
        assert result.behavior == PermissionBehavior.DENY
        assert "rule" in result.reason

    @pytest.mark.asyncio
    async def test_layer1_allow(self, ctx):
        rules = [PermissionRule(tool="read_file", behavior=PermissionBehavior.ALLOW)]
        result = await resolve_permission(FakeTool(), {}, ctx, rules, "default")
        assert result.behavior == PermissionBehavior.ALLOW
        assert "rule" in result.reason

    @pytest.mark.asyncio
    async def test_layer2_yolo(self, ctx):
        result = await resolve_permission(FakeTool(), {}, ctx, [], "yolo")
        assert result.behavior == PermissionBehavior.ALLOW
        assert result.reason == "yolo_mode"

    @pytest.mark.asyncio
    async def test_layer2_plan(self, ctx):
        result = await resolve_permission(FakeTool(), {}, ctx, [], "plan")
        assert result.behavior == PermissionBehavior.DENY
        assert result.reason == "plan_mode"

    @pytest.mark.asyncio
    async def test_layer3_tool_allow(self, ctx):
        result = await resolve_permission(FakeToolAllow(), {}, ctx, [], "default")
        assert result.behavior == PermissionBehavior.ALLOW
        assert result.reason == "tool_allow"

    @pytest.mark.asyncio
    async def test_layer4_ask_callback(self, ctx):
        async def ask_cb(req: PermissionRequest):
            return PermissionResult(behavior=PermissionBehavior.ALLOW, reason="user_allowed")

        ctx.ask_callback = ask_cb
        result = await resolve_permission(FakeTool(), {}, ctx, [], "default")
        assert result.behavior == PermissionBehavior.ALLOW
        assert result.reason == "user_allowed"

    @pytest.mark.asyncio
    async def test_layer4_no_callback_defaults_deny(self, ctx):
        result = await resolve_permission(FakeTool(), {}, ctx, [], "default")
        assert result.behavior == PermissionBehavior.DENY
        assert result.reason == "default_deny"
