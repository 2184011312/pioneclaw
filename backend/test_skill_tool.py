"""
SkillTool 功能测试

测试 list/activate 操作及错误处理。
"""
import pytest
import json
import tempfile
import os

# ═══════════════════════════════════════════════════════════
# 测试 1: 工具结构
# ═══════════════════════════════════════════════════════════

class TestSkillToolStructure:
    def test_tool_attributes(self):
        from app.modules.tools.skill import SkillTool
        tool = SkillTool()
        assert tool.name == "skill"
        assert tool.required == ["action"]
        assert "action" in tool.parameters
        assert "skill_name" in tool.parameters

    def test_action_enum(self):
        from app.modules.tools.skill import SkillTool
        param = SkillTool.parameters["action"]
        assert param.enum == ["list", "activate"]

    def test_skill_name_has_default(self):
        from app.modules.tools.skill import SkillTool
        param = SkillTool.parameters["skill_name"]
        assert param.default == ""

    def test_definition_format(self):
        from app.modules.tools.skill import SkillTool
        d = SkillTool().get_definition().to_openai_format()
        assert d["type"] == "function"
        assert d["function"]["name"] == "skill"
        assert "action" in d["function"]["parameters"]["properties"]


# ═══════════════════════════════════════════════════════════
# 测试 2: list 操作
# ═══════════════════════════════════════════════════════════

class TestSkillList:
    @pytest.mark.asyncio
    async def test_list_returns_json(self):
        from app.modules.tools.skill import SkillTool
        tool = SkillTool()
        result = await tool.execute(action="list")
        data = json.loads(result)
        assert data["success"] is True
        assert isinstance(data["skills"], list)
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_no_error(self):
        from app.modules.tools.skill import SkillTool
        tool = SkillTool()
        result = await tool.execute(action="list")
        data = json.loads(result)
        assert "error" not in data


# ═══════════════════════════════════════════════════════════
# 测试 3: activate 操作 — 错误情况
# ═══════════════════════════════════════════════════════════

class TestSkillActivateErrors:
    @pytest.mark.asyncio
    async def test_activate_missing_name(self):
        from app.modules.tools.skill import SkillTool
        tool = SkillTool()
        result = await tool.execute(action="activate")
        data = json.loads(result)
        assert data["success"] is False
        assert "skill_name" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_activate_empty_name(self):
        from app.modules.tools.skill import SkillTool
        tool = SkillTool()
        result = await tool.execute(action="activate", skill_name="")
        data = json.loads(result)
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_activate_nonexistent_skill(self):
        from app.modules.tools.skill import SkillTool
        tool = SkillTool()
        result = await tool.execute(action="activate", skill_name="__nonexistent_xyz__")
        data = json.loads(result)
        assert data["success"] is False
        assert "不存在" in data["error"]
        assert "available_skills" in data


# ═══════════════════════════════════════════════════════════
# 测试 4: 未知 action
# ═══════════════════════════════════════════════════════════

class TestSkillInvalidAction:
    @pytest.mark.asyncio
    async def test_invalid_action(self):
        from app.modules.tools.skill import SkillTool
        tool = SkillTool()
        result = await tool.execute(action="invalid_action_xyz")
        data = json.loads(result)
        assert data["success"] is False
        assert "未知" in data.get("error", "")


# ═══════════════════════════════════════════════════════════
# 测试 5: activate 有效技能（创建临时技能目录）
# ═══════════════════════════════════════════════════════════

class TestSkillActivateValid:
    @pytest.mark.asyncio
    async def test_activate_valid_skill(self, monkeypatch):
        """模拟 SkillsLoader 返回一个假技能来测试 activate"""
        from app.modules.tools.skill import SkillTool
        import app.modules.tools.skill as skill_module

        # 创建一个 mock loader
        class MockMetadata:
            title = "Test Skill"
            description = "A test skill for testing"
            always = False
            tags = ["test"]
            dependencies = []
            requires = None
            install = None

        class MockSkill:
            name = "test-skill"
            path = "/tmp/test-skill"
            content = "---\ntitle: Test\n---\n\n## Instructions\nDo the thing."
            enabled = True
            source = "workspace"
            metadata = MockMetadata()
            def check_requirements(self): return True

        class MockLoader:
            skills = {"test-skill": MockSkill()}
            def get_skill(self, name):
                return self.skills.get(name)
            def _strip_frontmatter(self, content):
                # Simple frontmatter stripper for test
                if content.startswith("---\n"):
                    parts = content.split("---\n", 2)
                    if len(parts) >= 3:
                        return parts[2].strip()
                return content

        # Monkeypatch get_skills_loader
        original = skill_module.get_skills_loader
        skill_module.get_skills_loader = lambda: MockLoader()

        try:
            tool = SkillTool()
            result = await tool.execute(action="activate", skill_name="test-skill")
            data = json.loads(result)
            assert data["success"] is True
            assert data["name"] == "test-skill"
            assert data["title"] == "Test Skill"
            # Content should NOT have frontmatter
            assert "---" not in data["content"]
            assert "Do the thing" in data["content"]
        finally:
            skill_module.get_skills_loader = original
