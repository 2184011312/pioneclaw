"""
过滤核心业务服务

整合词引擎、正则引擎、决策器，提供统一的过滤接口。
"""

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from engines.word_engine import WordEngine
from engines.regex_engine import RegexEngine
from engines.decision_engine import DecisionEngine, SafetyAction
from engines.model_engine import ModelEngine
from config import settings

logger = logging.getLogger(__name__)


class FilterService:
    """过滤服务

    管理检测引擎的生命周期，提供 filter_input/filter_output/check_tool 接口。
    使用单例模式确保引擎只加载一次。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._word_engine = WordEngine()
        self._regex_engine = RegexEngine()
        self._model_engine = ModelEngine()
        self._decision = DecisionEngine()
        self._initialized = True
        logger.info("FilterService initialized")

    async def reload_engines(self, session: AsyncSession):
        """从数据库重新加载词库"""
        if not settings.ENABLE_WORD_ENGINE:
            return
        try:
            from services.word_service import WordService
            word_service = WordService()
            words = await word_service.get_all_active(session)
            self._word_engine.load(words)
            logger.info(f"Word engine reloaded with {len(words)} words")
        except Exception as e:
            logger.error(f"Failed to reload word engine: {e}")

    def is_ready(self) -> bool:
        """检查服务是否就绪"""
        return (
            not settings.ENABLE_WORD_ENGINE or self._word_engine.is_loaded
        )

    async def filter_input(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """pre_input_call: 输入过滤

        Returns:
            {action, content, reason, risk_level, matched_rules}
        """
        word_matches = []
        regex_matches = []
        model_result = None

        if settings.ENABLE_WORD_ENGINE and self._word_engine.is_loaded:
            word_matches = self._word_engine.check(text)

        if settings.ENABLE_REGEX_ENGINE:
            regex_matches = self._regex_engine.detect(text)

        # 模型引擎：语义风险检测
        if settings.ENABLE_MODEL_ENGINE:
            try:
                model_result = await self._model_engine.check(text)
            except Exception as e:
                logger.warning(f"Model engine check failed: {e}")

        result = self._decision.decide(
            word_matches=word_matches,
            regex_matches=regex_matches,
            model_result=model_result,
            check_point="input",
        )

        # 将模型引擎原始结果附加到响应（便于调试和审计）
        if model_result:
            result["model_result"] = {
                "category": model_result.get("meta", {}).get("category"),
                "severity": model_result.get("severity"),
                "description": model_result.get("meta", {}).get("description"),
                "source": model_result.get("meta", {}).get("source", "rule"),
            }

        # 脱敏
        if result["action"] == SafetyAction.SANITIZE:
            result["content"] = self._regex_engine.desensitize(text)

        return result

    async def filter_output(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """post_llm_call: 输出过滤

        输出侧只检测敏感数据泄露，不做 Prompt 注入检测。
        """
        regex_matches = []
        if settings.ENABLE_REGEX_ENGINE:
            regex_matches = self._regex_engine.detect(text)

        result = self._decision.decide(
            word_matches=[],
            regex_matches=regex_matches,
            check_point="output",
        )

        if result["action"] == SafetyAction.SANITIZE:
            result["content"] = self._regex_engine.desensitize(text)

        return result

    async def check_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """pre_tool_call: 工具调用安全检查

        目前实现基础检查：
        1. 高危工具名检查
        2. 参数中的路径遍历检查
        3. 参数中的 SQL 注入检查
        """
        matched_rules = []

        # 高危工具检查
        dangerous_tools = {"exec", "shell", "eval", "system"}
        if tool_name.lower() in dangerous_tools:
            matched_rules.append(
                {
                    "type": "dangerous_tool",
                    "match": tool_name,
                    "severity": 3,
                    "meta": {"category": "高危工具"},
                }
            )

        # 参数安全检查
        args_str = str(arguments)

        # 路径遍历检查
        if ".." in args_str or "~" in args_str:
            matched_rules.append(
                {
                    "type": "path_traversal",
                    "match": "..",
                    "severity": 4,
                    "meta": {"category": "路径遍历"},
                }
            )

        # SQL 注入检查（简单模式）
        sql_patterns = ["' OR ", "' AND ", "; DROP ", "; DELETE ", "UNION SELECT"]
        for pattern in sql_patterns:
            if pattern.upper() in args_str.upper():
                matched_rules.append(
                    {
                        "type": "sql_injection",
                        "match": pattern,
                        "severity": 4,
                        "meta": {"category": "SQL注入"},
                    }
                )
                break

        result = self._decision.decide(
            word_matches=[],
            regex_matches=matched_rules,
            check_point="tool",
        )

        return result
