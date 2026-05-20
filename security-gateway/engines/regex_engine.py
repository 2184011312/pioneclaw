"""
正则引擎 - 结构化敏感数据检测与脱敏

预编译正则模式，支持身份证号、手机号、银行卡号、案件编号等检测。
"""

import re
from typing import List, Dict, Any, Optional


class RegexEngine:
    """正则引擎"""

    # 预编译正则模式
    PATTERNS = {
        "id_card": {
            "pattern": re.compile(
                r"[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]"
            ),
            "severity": 4,
        },
        "phone": {
            "pattern": re.compile(r"(?<![\d])1[3-9]\d{9}(?![\d])"),
            "severity": 3,
        },
        "bank_card": {
            "pattern": re.compile(r"\b\d{16,19}\b"),
            "severity": 3,
        },
        "case_no": {
            "pattern": re.compile(r"[A-Z]\d{4,}\d{4,}"),
            "severity": 3,
        },
        "internal_ip": {
            "pattern": re.compile(
                r"(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})"
            ),
            "severity": 3,
        },
    }

    # 脱敏规则
    DESENSITIZE_RULES = {
        "id_card": lambda m: m.group()[:6] + "*" * (len(m.group()) - 10) + m.group()[-4:],
        "phone": lambda m: m.group()[:3] + "****" + m.group()[-4:],
        "bank_card": lambda m: m.group()[:4] + "*" * (len(m.group()) - 8) + m.group()[-4:],
        "case_no": lambda m: m.group()[:3] + "****" + m.group()[-3:],
        "internal_ip": lambda m: m.group()[:m.group().rfind(".")+1] + "***",
    }

    def detect(self, text: str) -> List[Dict[str, Any]]:
        """检测文本中的所有正则匹配

        Returns:
            [{type, match, start, end, severity}, ...]
        """
        results = []
        for name, cfg in self.PATTERNS.items():
            for m in cfg["pattern"].finditer(text):
                results.append(
                    {
                        "type": name,
                        "match": m.group(),
                        "start": m.start(),
                        "end": m.end(),
                        "severity": cfg["severity"],
                        "meta": {"category": name},
                    }
                )
        # 按位置排序
        results.sort(key=lambda x: x["start"])
        return results

    def desensitize(
        self, text: str, rules: Optional[List[str]] = None
    ) -> str:
        """脱敏处理

        Args:
            text: 原始文本
            rules: 指定要脱敏的规则列表，None 表示全部

        Returns:
            脱敏后的文本
        """
        rules = rules or list(self.PATTERNS.keys())
        result = text
        for name in rules:
            if name in self.PATTERNS and name in self.DESENSITIZE_RULES:
                pattern = self.PATTERNS[name]["pattern"]
                repl = self.DESENSITIZE_RULES[name]
                result = pattern.sub(repl, result)
        return result

    def contains(self, text: str, rule_types: Optional[List[str]] = None) -> bool:
        """检查文本是否包含指定类型的敏感数据"""
        types = rule_types or list(self.PATTERNS.keys())
        for name in types:
            if name in self.PATTERNS:
                if self.PATTERNS[name]["pattern"].search(text):
                    return True
        return False
