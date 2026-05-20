"""
Trie 树多模式匹配引擎

用于敏感词、风控词、放通词的高效匹配。
时间复杂度: O(N * L), N 为文本长度, L 为最长词长度。
"""

from typing import Dict, Any, List


class TrieNode:
    __slots__ = ["children", "is_end", "meta"]

    def __init__(self):
        self.children: Dict[str, "TrieNode"] = {}
        self.is_end: bool = False
        self.meta: Dict[str, Any] = {}


class Trie:
    """Trie 树多模式匹配"""

    def __init__(self):
        self.root = TrieNode()
        self._word_count = 0

    def add(self, word: str, meta: Dict[str, Any]):
        """添加一个词到 Trie"""
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True
        node.meta = meta
        self._word_count += 1

    def clear(self):
        """清空 Trie"""
        self.root = TrieNode()
        self._word_count = 0

    @property
    def word_count(self) -> int:
        return self._word_count

    def search(self, text: str) -> List[Dict[str, Any]]:
        """搜索文本中的所有匹配

        Returns:
            [{word, start, end, meta}, ...]
        """
        results = []
        for i, ch in enumerate(text):
            node = self.root
            for j in range(i, len(text)):
                c = text[j]
                if c not in node.children:
                    break
                node = node.children[c]
                if node.is_end:
                    results.append(
                        {
                            "word": text[i : j + 1],
                            "start": i,
                            "end": j,
                            "meta": node.meta,
                        }
                    )
        return results

    def contains(self, text: str) -> bool:
        """检查文本中是否包含任一已添加的词"""
        for i, ch in enumerate(text):
            node = self.root
            for j in range(i, len(text)):
                c = text[j]
                if c not in node.children:
                    break
                node = node.children[c]
                if node.is_end:
                    return True
        return False
