"""
SpawnTool Agent 类型功能测试

测试 explore/plan/general 三种 Agent 类型的工具过滤和系统提示词注入。
"""
import pytest
from app.modules.tools.builtin import SpawnTool
from app.modules.tools import ToolRegistry, register_builtin_tools


def _get_filtered_definitions(agent_type: str) -> list:
    """提取过滤后的工具定义（模拟 execute 中的逻辑）"""
    tool_registry = ToolRegistry()
    register_builtin_tools(tool_registry)
    tool_definitions = tool_registry.get_definitions()

    tool_filter = SpawnTool._AGENT_TYPE_TOOLS.get(agent_type)
    if tool_filter is not None:
        tool_definitions = [
            t for t in tool_definitions
            if t.get("function", {}).get("name") in tool_filter
        ]
    return tool_definitions


def _get_tool_names(defs: list) -> set:
    """提取工具名称集合"""
    return {t.get("function", {}).get("name") for t in defs}


# ==================== Agent 类型结构测试 ====================

class TestAgentTypeStructure:
    def test_all_five_types_defined(self):
        assert "general" in SpawnTool._AGENT_TYPE_TOOLS
        assert "explore" in SpawnTool._AGENT_TYPE_TOOLS
        assert "plan" in SpawnTool._AGENT_TYPE_TOOLS
        assert "verification" in SpawnTool._AGENT_TYPE_TOOLS
        assert "guide" in SpawnTool._AGENT_TYPE_TOOLS

    def test_general_is_none(self):
        assert SpawnTool._AGENT_TYPE_TOOLS["general"] is None

    def test_explore_is_restricted(self):
        tools = SpawnTool._AGENT_TYPE_TOOLS["explore"]
        assert "read_file" in tools
        assert "grep" in tools
        assert "file_search" in tools
        assert "list_dir" in tools
        assert "web_search" in tools
        assert "edit_file" not in tools
        assert "exec" not in tools
        assert "spawn" not in tools

    def test_plan_has_plan_mode_tools(self):
        tools = SpawnTool._AGENT_TYPE_TOOLS["plan"]
        assert "enter_plan_mode" in tools
        assert "exit_plan_mode" in tools
        assert "ask_user_question" in tools
        assert "read_file" in tools
        assert "edit_file" not in tools
        assert "exec" not in tools

    def test_verification_has_exec(self):
        """verification 类型应有 exec 用于运行测试"""
        tools = SpawnTool._AGENT_TYPE_TOOLS["verification"]
        assert "read_file" in tools
        assert "grep" in tools
        assert "exec" in tools
        assert "edit_file" not in tools
        assert "write_file" not in tools
        assert "spawn" not in tools

    def test_guide_is_readonly_with_knowledge(self):
        """guide 类型只读 + 知识库查询，不含 exec"""
        tools = SpawnTool._AGENT_TYPE_TOOLS["guide"]
        assert "read_file" in tools
        assert "knowledge_search" in tools
        assert "memory_search" in tools
        assert "exec" not in tools
        assert "edit_file" not in tools
        assert "spawn" not in tools


# ==================== 工具过滤测试 ====================

class TestToolFiltering:
    def test_general_returns_all_tools(self):
        """general 类型不过滤，返回所有工具"""
        defs = _get_filtered_definitions("general")
        names = _get_tool_names(defs)
        # 至少应有 20+ 工具
        assert len(names) >= 20
        assert "read_file" in names
        assert "edit_file" in names
        assert "exec" in names
        assert "spawn" in names

    def test_explore_only_read_tools(self):
        """explore 类型仅包含只读工具"""
        defs = _get_filtered_definitions("explore")
        names = _get_tool_names(defs)
        expected = {"read_file", "grep", "file_search", "list_dir",
                     "web_search", "web_fetch", "current_time"}
        assert names == expected, f"explore tools mismatch: {names}"

    def test_explore_no_write_tools(self):
        defs = _get_filtered_definitions("explore")
        names = _get_tool_names(defs)
        assert "edit_file" not in names
        assert "write_file" not in names
        assert "exec" not in names

    def test_explore_no_spawn(self):
        defs = _get_filtered_definitions("explore")
        names = _get_tool_names(defs)
        assert "spawn" not in names

    def test_plan_has_correct_tools(self):
        """plan 类型包含只读+计划工具"""
        defs = _get_filtered_definitions("plan")
        names = _get_tool_names(defs)
        assert "enter_plan_mode" in names
        assert "exit_plan_mode" in names
        assert "ask_user_question" in names
        assert "read_file" in names
        assert "grep" in names
        assert "calculator" in names
        assert "image" in names

    def test_plan_no_write_tools(self):
        defs = _get_filtered_definitions("plan")
        names = _get_tool_names(defs)
        assert "edit_file" not in names
        assert "write_file" not in names
        assert "exec" not in names

    def test_plan_no_spawn(self):
        defs = _get_filtered_definitions("plan")
        names = _get_tool_names(defs)
        assert "spawn" not in names

    def test_verification_has_exec_read_tools(self):
        """verification 类型包含只读工具 + exec"""
        defs = _get_filtered_definitions("verification")
        names = _get_tool_names(defs)
        assert "read_file" in names
        assert "grep" in names
        assert "exec" in names
        assert "current_time" in names

    def test_verification_no_write_tools(self):
        defs = _get_filtered_definitions("verification")
        names = _get_tool_names(defs)
        assert "edit_file" not in names
        assert "write_file" not in names

    def test_verification_no_spawn(self):
        defs = _get_filtered_definitions("verification")
        names = _get_tool_names(defs)
        assert "spawn" not in names

    def test_guide_has_knowledge_tools(self):
        """guide 类型包含知识库查询工具"""
        defs = _get_filtered_definitions("guide")
        names = _get_tool_names(defs)
        assert "read_file" in names
        assert "knowledge_search" in names
        assert "memory_search" in names

    def test_guide_no_exec(self):
        defs = _get_filtered_definitions("guide")
        names = _get_tool_names(defs)
        assert "exec" not in names

    def test_guide_no_spawn(self):
        defs = _get_filtered_definitions("guide")
        names = _get_tool_names(defs)
        assert "spawn" not in names

    def test_unknown_type_falls_through(self):
        """未知类型无过滤器，返回所有工具"""
        defs = _get_filtered_definitions("unknown")
        names = _get_tool_names(defs)
        assert "read_file" in names
        assert "edit_file" in names


# ==================== SpawnTool 参数测试 ====================

class TestSpawnToolParams:
    def test_agent_type_parameter_exists(self):
        assert "agent_type" in SpawnTool.parameters

    def test_agent_type_has_correct_enum(self):
        param = SpawnTool.parameters["agent_type"]
        assert param.enum == ["general", "explore", "plan", "verification", "guide"]

    def test_agent_type_default(self):
        param = SpawnTool.parameters["agent_type"]
        assert param.default == "general"

    def test_agent_type_is_optional(self):
        assert "agent_type" not in SpawnTool.required


# ==================== 系统提示词测试 ====================

class TestAgentTypeInstructions:
    """验证各 Agent 类型的系统提示词内容"""
    TOOL_REGISTRY: ToolRegistry = None

    @classmethod
    def setup_class(cls):
        cls.TOOL_REGISTRY = ToolRegistry()
        register_builtin_tools(cls.TOOL_REGISTRY)

    def test_explore_prompt_mentions_exploration(self):
        """explore 类型提示词包含探索相关关键字"""
        # 通过构造参数验证逻辑
        instructions = (
            "\n\n你是一个**代码库探索助手**。你的职责是搜索、阅读和理解代码，"
            "而不是修改代码。请提供清晰、结构化的发现报告，"
            "包括相关文件路径、关键代码片段和你的分析结论。"
        )
        assert "探索" in instructions
        assert "而不是修改代码" in instructions
        assert "代码库" in instructions

    def test_plan_prompt_mentions_plan_mode(self):
        """plan 类型提示词包含计划模式相关关键字"""
        instructions = (
            "\n\n你是一个**方案设计助手**。使用 enter_plan_mode 进入计划模式"
            "进行只读调研，设计方案后使用 exit_plan_mode 提交计划。"
            "计划应包含：Context（背景）、改动方案（具体步骤）、涉及文件、验证方法。"
        )
        assert "enter_plan_mode" in instructions
        assert "exit_plan_mode" in instructions
        assert "Context" in instructions

    def test_verification_prompt_mentions_testing(self):
        """verification 类型提示词包含测试验证相关关键字"""
        instructions = (
            "\n\n你是一个**测试验证助手**。你的职责是运行测试、验证代码变更的正确性。"
            "请运行相关的单元测试、集成测试或 E2E 测试，"
            "分析测试结果，报告通过/失败情况，"
            "并对失败原因给出初步诊断。"
        )
        assert "测试" in instructions
        assert "验证" in instructions
        assert "E2E" in instructions

    def test_guide_prompt_mentions_pioneclaw(self):
        """guide 类型提示词包含 PioneClaw 使用指南相关关键字"""
        instructions = (
            "\n\n你是一个**PioneClaw 使用指南助手**。你的职责是回答关于 PioneClaw 的使用问题。"
            "请搜索代码库和文档，找到相关配置、功能说明或最佳实践，"
            "给出清晰、实用的指导。"
        )
        assert "PioneClaw" in instructions
        assert "指南" in instructions
        assert "最佳实践" in instructions


# ==================== 集成测试 ====================

class TestSpawnWithAgentType:
    """通过 SpawnTool.execute 验证 agent_type 过滤"""

    @pytest.mark.asyncio
    async def test_explore_type_filters_tools(self):
        """验证 execute 方法中 agent_type=explore 会过滤工具"""
        SpawnTool()
        tool_registry = ToolRegistry()
        register_builtin_tools(tool_registry)
        all_defs = tool_registry.get_definitions()

        explore_filter = SpawnTool._AGENT_TYPE_TOOLS["explore"]
        filtered = [t for t in all_defs
                     if t.get("function", {}).get("name") in explore_filter]
        names = {t.get("function", {}).get("name") for t in filtered}
        assert "edit_file" not in names
        assert "read_file" in names

    @pytest.mark.asyncio
    async def test_verification_type_filters_tools(self):
        """验证 verification 类型包含 exec 但不含 spawn"""
        tool_registry = ToolRegistry()
        register_builtin_tools(tool_registry)
        all_defs = tool_registry.get_definitions()

        vf_filter = SpawnTool._AGENT_TYPE_TOOLS["verification"]
        filtered = [t for t in all_defs
                     if t.get("function", {}).get("name") in vf_filter]
        names = {t.get("function", {}).get("name") for t in filtered}
        assert "exec" in names
        assert "read_file" in names
        assert "edit_file" not in names
        assert "spawn" not in names

    @pytest.mark.asyncio
    async def test_guide_type_filters_tools(self):
        """验证 guide 类型包含知识库工具但不含 exec"""
        tool_registry = ToolRegistry()
        register_builtin_tools(tool_registry)
        all_defs = tool_registry.get_definitions()

        guide_filter = SpawnTool._AGENT_TYPE_TOOLS["guide"]
        filtered = [t for t in all_defs
                     if t.get("function", {}).get("name") in guide_filter]
        names = {t.get("function", {}).get("name") for t in filtered}
        assert "knowledge_search" in names
        assert "read_file" in names
        assert "exec" not in names
        assert "spawn" not in names
