"""
安全决策器 - 聚合三重引擎结果并做出最终决策
"""

from enum import Enum
from typing import List, Dict, Any, Optional


class SafetyAction(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    SANITIZE = "sanitize"
    APPROVE = "approve"


class DecisionEngine:
    """安全决策器

    聚合各检测引擎的结果，根据严重程度和检查点做出最终决策。
    """

    def decide(
        self,
        word_matches: Optional[List[Dict[str, Any]]] = None,
        regex_matches: Optional[List[Dict[str, Any]]] = None,
        model_result: Optional[Dict[str, Any]] = None,
        check_point: str = "input",
    ) -> Dict[str, Any]:
        """做出安全决策

        决策逻辑：
        1. 无匹配 -> ALLOW
        2. severity >= 4 -> BLOCK
        3. severity == 3 -> APPROVE（转人工审批）
        4. severity <= 2 -> SANITIZE

        Args:
            word_matches: 词引擎匹配结果
            regex_matches: 正则引擎匹配结果
            model_result: 模型引擎结果（Phase 2）
            check_point: 检查点类型 (input/output/tool)

        Returns:
            {action, reason, risk_level, matched_rules}
        """
        word_matches = word_matches or []
        regex_matches = regex_matches or []

        all_matches = list(word_matches) + list(regex_matches)

        # 如果有模型引擎结果，也加入评估
        if model_result and model_result.get("risk_level") != "low":
            all_matches.append(
                {
                    "type": "model_detection",
                    "match": "",
                    "severity": self._risk_level_to_severity(
                        model_result.get("risk_level", "low")
                    ),
                    "meta": {
                        "category": model_result.get("category", "unknown"),
                        "reason": model_result.get("reason", ""),
                    },
                }
            )

        if not all_matches:
            return {
                "action": SafetyAction.ALLOW,
                "reason": None,
                "risk_level": "low",
                "matched_rules": [],
            }

        # 找出最高严重级别
        max_severity = max(
            (m.get("severity", 1) for m in all_matches), default=1
        )

        # 根据检查点调整策略
        if check_point == "output":
            # 输出侧：只拦截高危泄露，其他脱敏即可
            if max_severity >= 4:
                return {
                    "action": SafetyAction.BLOCK,
                    "reason": f"模型输出包含高危敏感信息（severity={max_severity}）",
                    "risk_level": "critical",
                    "matched_rules": all_matches,
                }
            else:
                return {
                    "action": SafetyAction.SANITIZE,
                    "reason": f"模型输出包含敏感信息，已脱敏（severity={max_severity}）",
                    "risk_level": "medium",
                    "matched_rules": all_matches,
                }

        # 输入侧 / 工具侧默认策略
        if max_severity >= 4:
            return {
                "action": SafetyAction.BLOCK,
                "reason": f"检测到高危敏感信息（severity={max_severity}）",
                "risk_level": "critical",
                "matched_rules": all_matches,
            }
        elif max_severity == 3:
            return {
                "action": SafetyAction.APPROVE,
                "reason": f"检测到中危信息，需人工审批（severity={max_severity}）",
                "risk_level": "high",
                "matched_rules": all_matches,
            }
        else:
            return {
                "action": SafetyAction.SANITIZE,
                "reason": f"检测到敏感信息，已自动脱敏（severity={max_severity}）",
                "risk_level": "medium",
                "matched_rules": all_matches,
            }

    @staticmethod
    def _risk_level_to_severity(risk_level: str) -> int:
        mapping = {"low": 1, "medium": 2, "high": 3, "critical": 5}
        return mapping.get(risk_level, 1)
