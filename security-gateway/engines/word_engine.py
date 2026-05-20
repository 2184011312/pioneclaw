"""
词引擎 - 基于 Trie 树的敏感词/风控词/放通词检测
"""

from typing import List, Dict, Any, Optional
from engines.trie import Trie
from models.security import WordType


class WordEngine:
    """词引擎

    使用 Trie 树进行高效多模式匹配，支持敏感词、风控词、放通词。
    放通词优先级最高，命中放通词时忽略同位置的敏感词匹配。
    """

    def __init__(self):
        self._sensitive_trie = Trie()
        self._risk_trie = Trie()
        self._allow_words: set = set()
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def load(self, words: List[Any]):
        """从词库记录加载

        Args:
            words: WordLibrary 对象列表
        """
        self._sensitive_trie.clear()
        self._risk_trie.clear()
        self._allow_words.clear()

        for w in words:
            if not w.is_active:
                continue
            if w.word_type == WordType.ALLOW:
                self._allow_words.add(w.word)
            elif w.word_type == WordType.SENSITIVE:
                self._sensitive_trie.add(
                    w.word,
                    {"type": "sensitive", "severity": w.severity, "category": w.category},
                )
            elif w.word_type == WordType.RISK:
                self._risk_trie.add(
                    w.word,
                    {"type": "risk", "severity": w.severity, "category": w.category},
                )

        self._loaded = True

    def check(self, text: str) -> List[Dict[str, Any]]:
        """检测文本中的敏感词和风控词

        Returns:
            匹配结果列表，每个元素包含 word, start, end, meta
        """
        if not self._loaded:
            return []

        # 1. 先检查放通词
        for allow_word in self._allow_words:
            if allow_word in text:
                # 如果文本只包含放通词（简化判断：文本就是放通词本身），直接放行
                if text.strip() == allow_word:
                    return []

        # 2. 扫描敏感词
        sensitive_matches = self._sensitive_trie.search(text)

        # 3. 扫描风控词
        risk_matches = self._risk_trie.search(text)

        # 4. 合并结果，放通词覆盖
        all_matches = []
        for m in sensitive_matches + risk_matches:
            # 检查该匹配是否被放通词覆盖
            if self._is_allowed_at_position(text, m["start"], m["end"]):
                continue
            all_matches.append(m)

        return all_matches

    def _is_allowed_at_position(
        self, text: str, start: int, end: int
    ) -> bool:
        """检查某个位置的匹配是否被放通词覆盖"""
        for allow_word in self._allow_words:
            # 检查放通词是否覆盖该位置
            idx = text.find(allow_word)
            while idx != -1:
                allow_start = idx
                allow_end = idx + len(allow_word) - 1
                # 如果敏感词匹配区间与放通词区间重叠
                if not (end < allow_start or start > allow_end):
                    return True
                idx = text.find(allow_word, idx + 1)
        return False
