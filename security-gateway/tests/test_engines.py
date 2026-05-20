"""
安全网关引擎单元测试

覆盖 Trie 树、正则引擎、决策引擎、词引擎的核心逻辑。
"""

import pytest
from engines.trie import Trie
from engines.regex_engine import RegexEngine
from engines.decision_engine import DecisionEngine, SafetyAction
from engines.word_engine import WordEngine


class TestTrie:
    """Trie 树匹配测试"""

    def test_add_and_search(self):
        trie = Trie()
        trie.add("敏感词", {"type": "sensitive", "severity": 3})
        trie.add("风险", {"type": "risk", "severity": 2})

        results = trie.search("这句话包含敏感词和风险内容")
        assert len(results) == 2

        words = [r["word"] for r in results]
        assert "敏感词" in words
        assert "风险" in words

    def test_search_positions(self):
        trie = Trie()
        trie.add("abc", {"type": "test"})

        results = trie.search("xxabcyy")
        assert len(results) == 1
        assert results[0]["start"] == 2
        assert results[0]["end"] == 4
        assert results[0]["word"] == "abc"

    def test_no_match(self):
        trie = Trie()
        trie.add("不存在", {"type": "test"})

        results = trie.search("这句话没问题")
        assert len(results) == 0

    def test_overlapping_matches(self):
        trie = Trie()
        trie.add("abcde", {"type": "test"})
        trie.add("bcd", {"type": "test"})

        results = trie.search("abcde")
        assert len(results) == 2
        words = [r["word"] for r in results]
        assert "abcde" in words
        assert "bcd" in words

    def test_contains(self):
        trie = Trie()
        trie.add("命中", {"type": "test"})

        assert trie.contains("这里命中了") is True
        assert trie.contains("这里没有") is False

    def test_word_count(self):
        trie = Trie()
        assert trie.word_count == 0
        trie.add("词1", {})
        trie.add("词2", {})
        assert trie.word_count == 2
        trie.clear()
        assert trie.word_count == 0


class TestRegexEngine:
    """正则引擎检测与脱敏测试"""

    def test_detect_id_card(self):
        engine = RegexEngine()
        text = "我的身份证号是 51012319900101001X，请帮忙查询"
        results = engine.detect(text)

        id_card_results = [r for r in results if r["type"] == "id_card"]
        assert len(id_card_results) == 1
        assert id_card_results[0]["match"] == "51012319900101001X"
        assert id_card_results[0]["severity"] == 4

    def test_detect_phone(self):
        engine = RegexEngine()
        text = "联系电话：13800138000"
        results = engine.detect(text)

        phone_results = [r for r in results if r["type"] == "phone"]
        assert len(phone_results) == 1
        assert phone_results[0]["match"] == "13800138000"
        assert phone_results[0]["severity"] == 3

    def test_detect_multiple(self):
        engine = RegexEngine()
        text = "身份证 51012319900101001X，手机 13800138000"
        results = engine.detect(text)

        assert len(results) == 2
        types = [r["type"] for r in results]
        assert "id_card" in types
        assert "phone" in types

    def test_desensitize_id_card(self):
        engine = RegexEngine()
        text = "身份证 51012319900101001X"
        result = engine.desensitize(text, rules=["id_card"])
        assert result == "身份证 510123********001X"

    def test_desensitize_phone(self):
        engine = RegexEngine()
        text = "手机 13800138000"
        result = engine.desensitize(text, rules=["phone"])
        assert result == "手机 138****8000"

    def test_desensitize_bank_card(self):
        engine = RegexEngine()
        text = "银行卡 6222021234567890123"
        result = engine.desensitize(text, rules=["bank_card"])
        assert result == "银行卡 6222***********0123"

    def test_desensitize_all(self):
        engine = RegexEngine()
        text = "身份证 51012319900101001X，手机 13800138000"
        result = engine.desensitize(text)
        assert "510123********001X" in result
        assert "138****8000" in result

    def test_contains(self):
        engine = RegexEngine()
        assert engine.contains("身份证 51012319900101001X") is True
        assert engine.contains("普通文本") is False

    def test_detect_internal_ip(self):
        engine = RegexEngine()
        text = "内网地址 192.168.1.100"
        results = engine.detect(text)

        ip_results = [r for r in results if r["type"] == "internal_ip"]
        assert len(ip_results) == 1
        assert ip_results[0]["match"] == "192.168.1.100"


class TestDecisionEngine:
    """决策引擎严重度分级测试"""

    def test_no_match_allow(self):
        engine = DecisionEngine()
        result = engine.decide([], [])

        assert result["action"] == SafetyAction.ALLOW
        assert result["risk_level"] == "low"
        assert result["matched_rules"] == []

    def test_severity_4_block(self):
        engine = DecisionEngine()
        matches = [{"type": "id_card", "severity": 4}]
        result = engine.decide([], matches)

        assert result["action"] == SafetyAction.BLOCK
        assert result["risk_level"] == "critical"
        assert len(result["matched_rules"]) == 1

    def test_severity_5_block(self):
        engine = DecisionEngine()
        matches = [{"type": "sensitive", "severity": 5}]
        result = engine.decide(matches, [])

        assert result["action"] == SafetyAction.BLOCK
        assert result["risk_level"] == "critical"

    def test_severity_3_approve(self):
        engine = DecisionEngine()
        matches = [{"type": "phone", "severity": 3}]
        result = engine.decide([], matches)

        assert result["action"] == SafetyAction.APPROVE
        assert result["risk_level"] == "high"

    def test_severity_2_sanitize(self):
        engine = DecisionEngine()
        matches = [{"type": "risk", "severity": 2}]
        result = engine.decide(matches, [])

        assert result["action"] == SafetyAction.SANITIZE
        assert result["risk_level"] == "medium"

    def test_severity_1_sanitize(self):
        engine = DecisionEngine()
        matches = [{"type": "risk", "severity": 1}]
        result = engine.decide(matches, [])

        assert result["action"] == SafetyAction.SANITIZE
        assert result["risk_level"] == "medium"

    def test_output_checkpoint_block(self):
        engine = DecisionEngine()
        matches = [{"type": "id_card", "severity": 4}]
        result = engine.decide([], matches, check_point="output")

        assert result["action"] == SafetyAction.BLOCK
        assert result["risk_level"] == "critical"

    def test_output_checkpoint_sanitize(self):
        engine = DecisionEngine()
        matches = [{"type": "phone", "severity": 3}]
        result = engine.decide([], matches, check_point="output")

        # 输出侧：severity < 4 统一脱敏
        assert result["action"] == SafetyAction.SANITIZE
        assert result["risk_level"] == "medium"

    def test_combined_matches(self):
        engine = DecisionEngine()
        word_matches = [{"type": "risk", "severity": 2}]
        regex_matches = [{"type": "phone", "severity": 3}]
        result = engine.decide(word_matches, regex_matches)

        # 取最高 severity = 3 -> APPROVE
        assert result["action"] == SafetyAction.APPROVE

    def test_model_result_high_risk(self):
        engine = DecisionEngine()
        model_result = {"risk_level": "high", "category": "jailbreak", "reason": "越狱尝试"}
        result = engine.decide([], [], model_result=model_result)

        assert result["action"] == SafetyAction.APPROVE
        assert result["risk_level"] == "high"


class MockWord:
    """模拟 WordLibrary 对象"""

    def __init__(self, word, word_type, severity=3, category="", is_active=True):
        self.word = word
        self.word_type = word_type
        self.severity = severity
        self.category = category
        self.is_active = is_active


class TestWordEngine:
    """词引擎测试"""

    def test_load_and_check_sensitive(self):
        engine = WordEngine()
        words = [
            MockWord("暴力", "sensitive", severity=4),
            MockWord("正常", "allow"),
        ]
        engine.load(words)

        results = engine.check("这句话包含暴力内容")
        assert len(results) == 1
        assert results[0]["word"] == "暴力"
        assert results[0]["meta"]["type"] == "sensitive"

    def test_allow_word_override(self):
        engine = WordEngine()
        words = [
            MockWord("敏感词", "sensitive", severity=4),
            MockWord("敏感词", "allow"),
        ]
        engine.load(words)

        results = engine.check("这句话包含敏感词")
        # 放通词覆盖敏感词
        assert len(results) == 0

    def test_allow_word_exact_match(self):
        engine = WordEngine()
        words = [
            MockWord("敏感词", "sensitive", severity=4),
            MockWord("敏感词", "allow"),
        ]
        engine.load(words)

        results = engine.check("敏感词")
        assert len(results) == 0

    def test_inactive_word_ignored(self):
        engine = WordEngine()
        words = [
            MockWord("禁用词", "sensitive", severity=4, is_active=False),
        ]
        engine.load(words)

        results = engine.check("这句话包含禁用词")
        assert len(results) == 0

    def test_not_loaded_returns_empty(self):
        engine = WordEngine()
        results = engine.check("任何文本")
        assert results == []

    def test_risk_word(self):
        engine = WordEngine()
        words = [
            MockWord("风险词", "risk", severity=3),
        ]
        engine.load(words)

        results = engine.check("这句话包含风险词")
        assert len(results) == 1
        assert results[0]["meta"]["type"] == "risk"
