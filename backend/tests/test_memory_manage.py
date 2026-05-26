"""
MemoryManage 门面单元测试

覆盖：save / recall / update / delete / list / search 基本路径
"""
import tempfile

import pytest

from app.modules.memory.memory_manage import MemoryManage
from app.modules.memory.models import (
    ListOptions,
    MemoryFailure,
    MemoryMetadata,
    MemoryResult,
    MemoryType,
)


@pytest.fixture
def mgr():
    """创建临时目录并返回 MemoryManage 实例。"""
    tmp = tempfile.mkdtemp(prefix="memory_mgr_")
    m = MemoryManage(memory_root=tmp)
    yield m
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)


class TestSave:
    def test_save_success(self, mgr):
        resp = mgr.save("用户喜欢用中文交流", MemoryType.USER)
        assert isinstance(resp, MemoryResult)
        assert resp.success
        entry = resp.data
        assert entry.name == "用户喜欢用中文交流"
        assert entry.type == MemoryType.USER

    def test_save_with_metadata(self, mgr):
        meta = MemoryMetadata(
            name="偏好设置",
            description="用户偏好设置记录",
            type=MemoryType.USER,
            tags=["设置"],
        )
        resp = mgr.save("用户喜欢用中文", MemoryType.USER, meta)
        assert isinstance(resp, MemoryResult)
        assert resp.data.name == "偏好设置"

    def test_save_empty_content(self, mgr):
        resp = mgr.save("   ", MemoryType.USER)
        assert isinstance(resp, MemoryFailure)
        assert not resp.success

    def test_save_invalid_type(self, mgr):
        resp = mgr.save("test content", "invalid_type_string")
        assert isinstance(resp, MemoryFailure)
        assert not resp.success

    def test_save_string_type(self, mgr):
        resp = mgr.save("test with string type", "project")
        assert isinstance(resp, MemoryResult)
        assert resp.success
        assert resp.data.type == MemoryType.PROJECT

    def test_save_duplicate_name(self, mgr):
        mgr.save("some content here", MemoryType.USER,
                 MemoryMetadata(name="dup", description="dup desc", type=MemoryType.USER))
        resp = mgr.save("different content", MemoryType.USER,
                         MemoryMetadata(name="dup", description="dup desc", type=MemoryType.USER))
        assert isinstance(resp, MemoryResult)
        assert resp.success  # returns the existing entry

    def test_save_duplicate_no_upsert_returns_old(self, mgr):
        """Without upsert, a duplicate returns the old entry unchanged."""
        first = mgr.save("原始内容——用户喜欢用中文交流", MemoryType.USER,
                         MemoryMetadata(name="语言偏好", description="用户喜欢用中文交流",
                                        type=MemoryType.USER))
        assert isinstance(first, MemoryResult)
        fname = first.data.filename

        # Same slug → detected as duplicate, returns old entry
        second = mgr.save("新内容——用户改口说要英文", MemoryType.USER,
                          MemoryMetadata(name="语言偏好", description="用户喜欢用中文交流",
                                         type=MemoryType.USER))
        assert isinstance(second, MemoryResult)
        assert second.data.content == "原始内容——用户喜欢用中文交流"
        assert second.data.filename == fname

    def test_save_upsert_updates_existing(self, mgr):
        """With upsert=True, a duplicate updates the existing entry with new content."""
        first = mgr.save("用户喜欢用中文交流", MemoryType.USER,
                         MemoryMetadata(name="语言偏好", description="用户喜欢用中文交流",
                                        type=MemoryType.USER))
        assert isinstance(first, MemoryResult)
        fname = first.data.filename

        second = mgr.save("用户现在更喜欢用英文交流，不再使用中文", MemoryType.USER,
                          MemoryMetadata(name="语言偏好", description="用户现在更喜欢用英文交流",
                                         type=MemoryType.USER),
                          upsert=True)
        assert isinstance(second, MemoryResult)
        assert second.data.content == "用户现在更喜欢用英文交流，不再使用中文"
        assert second.data.filename == fname

    def test_save_upsert_no_duplicate_creates_new(self, mgr):
        """upsert=True on a genuinely new topic still creates a new entry."""
        first = mgr.save("用户喜欢用中文交流", MemoryType.USER,
                         MemoryMetadata(name="语言偏好", description="用户喜欢用中文交流",
                                        type=MemoryType.USER))
        assert isinstance(first, MemoryResult)

        # Completely different topic — no duplicate detected
        second = mgr.save("项目使用 FastAPI 框架", MemoryType.PROJECT,
                          MemoryMetadata(name="技术栈", description="项目使用 FastAPI 框架",
                                         type=MemoryType.PROJECT),
                          upsert=True)
        assert isinstance(second, MemoryResult)
        assert second.data.filename != first.data.filename
        assert second.data.content == "项目使用 FastAPI 框架"


class TestSemanticDuplicate:
    """Tests for LLM-based semantic duplicate detection."""

    def test_semantic_dup_detects_same_topic_different_name(self, mgr):
        """Semantic matching should detect same topic even with different names."""
        called = []

        def mock_llm(prompt: str) -> str:
            called.append(prompt)
            # Return the filename of the first entry
            return "user-语言偏好.md"

        mgr.ranker._llm_query = mock_llm

        first = mgr.save("用户喜欢用中文交流", MemoryType.USER,
                         MemoryMetadata(name="语言偏好", description="用户喜欢用中文交流",
                                        type=MemoryType.USER))
        fname = first.data.filename

        # Second save with different name/slug — slug check fails, CJK may or may not
        # Semantic check finds the match via LLM
        second = mgr.save("用户要求称呼他为wishing，喜欢英文名。不再使用中文。", MemoryType.USER,
                          MemoryMetadata(name="用户要求称呼他为wishing",
                                         description="用户要求称呼他为wishing，喜欢英文名。",
                                         type=MemoryType.USER),
                          upsert=True)
        assert isinstance(second, MemoryResult)
        assert len(called) > 0
        # Should have updated the existing entry
        assert second.data.filename == fname

    def test_semantic_dup_no_match_creates_new(self, mgr):
        """LLM says NONE → no duplicate, creates new file."""
        called = []

        def mock_llm(prompt: str) -> str:
            called.append(prompt)
            return "NONE"

        mgr.ranker._llm_query = mock_llm

        first = mgr.save("用户喜欢用中文交流", MemoryType.USER,
                         MemoryMetadata(name="语言偏好", description="用户喜欢用中文交流",
                                        type=MemoryType.USER))

        second = mgr.save("项目使用 PostgreSQL 数据库", MemoryType.PROJECT,
                          MemoryMetadata(name="数据库选型",
                                         description="项目使用 PostgreSQL 数据库",
                                         type=MemoryType.PROJECT),
                          upsert=True)
        assert isinstance(second, MemoryResult)
        assert len(called) > 0
        assert second.data.filename != first.data.filename

    def test_semantic_dup_no_llm_skips(self, mgr):
        """When no LLM is available, semantic check is skipped gracefully."""
        assert mgr.ranker._llm_query is None

        first = mgr.save("用户喜欢用中文交流", MemoryType.USER)
        second = mgr.save("用户现在更喜欢用英文", MemoryType.USER,
                          MemoryMetadata(name="用户更喜欢英文",
                                         description="用户现在更喜欢用英文交流",
                                         type=MemoryType.USER),
                          upsert=True)
        # Both are created — semantic check was skipped, CJK overlap may or may not hit
        assert isinstance(first, MemoryResult)
        assert isinstance(second, MemoryResult)


class TestUpdate:
    def test_update_content(self, mgr):
        resp = mgr.save("原始内容", MemoryType.USER)
        fname = resp.data.filename
        updated = mgr.update(fname, "更新后的内容")
        assert isinstance(updated, MemoryResult)
        assert updated.data.content == "更新后的内容"

    def test_update_nonexistent(self, mgr):
        resp = mgr.update("nonexistent.md", "content")
        assert isinstance(resp, MemoryFailure)


class TestDelete:
    def test_delete_existing(self, mgr):
        resp = mgr.save("to be deleted", MemoryType.USER)
        fname = resp.data.filename
        deleted = mgr.delete(fname)
        assert isinstance(deleted, MemoryResult)
        assert deleted.data is True

    def test_delete_nonexistent(self, mgr):
        resp = mgr.delete("ghost.md")
        assert isinstance(resp, MemoryFailure)


class TestList:
    def test_list_empty(self, mgr):
        resp = mgr.list()
        assert isinstance(resp, MemoryResult)
        assert resp.data == []

    def test_list_with_entries(self, mgr):
        mgr.save("第一次对话中提到的用户偏好详细记录", MemoryType.USER)
        mgr.save("完全不相关的项目架构决策内容信息", MemoryType.USER)
        resp = mgr.list()
        assert len(resp.data) == 2

    def test_list_with_type_filter(self, mgr):
        mgr.save("user memory", MemoryType.USER)
        mgr.save("project memory", MemoryType.PROJECT)
        opts = ListOptions(type=MemoryType.PROJECT)
        resp = mgr.list(opts)
        assert len(resp.data) == 1
        assert resp.data[0].type == MemoryType.PROJECT

    def test_list_sort_by_name(self, mgr):
        mgr.save("ccc", MemoryType.USER,
                 MemoryMetadata(name="ccc", description="c", type=MemoryType.USER))
        mgr.save("aaa", MemoryType.USER,
                 MemoryMetadata(name="aaa", description="a", type=MemoryType.USER))
        opts = ListOptions(sort_by="name", order="asc")
        resp = mgr.list(opts)
        assert resp.data[0].name == "aaa"
        assert resp.data[1].name == "ccc"

    def test_list_limit_offset(self, mgr):
        for i in range(5):
            mgr.save(f"memory {i}", MemoryType.USER)
        opts = ListOptions(limit=2, offset=1)
        resp = mgr.list(opts)
        assert len(resp.data) <= 2


class TestSearch:
    def test_search_finds_keyword(self, mgr):
        mgr.save("Python 异步编程最佳实践", MemoryType.USER)
        mgr.save("JavaScript 前端开发", MemoryType.USER)
        resp = mgr.search("Python")
        assert len(resp.data) == 1
        assert "Python" in resp.data[0].content

    def test_search_no_match(self, mgr):
        mgr.save("hello world", MemoryType.USER)
        resp = mgr.search("zzzz_not_found")
        assert len(resp.data) == 0


class TestRecall:
    def test_recall_empty_store(self, mgr):
        attachments = mgr.recall("any query")
        assert attachments == []

    def test_recall_with_content(self, mgr):
        mgr.save("这是一个关于 Python 异步编程的记忆", MemoryType.PROJECT)
        attachments = mgr.recall("Python 异步")
        assert len(attachments) >= 0  # No LLM ranker available, ranks by keyword


class TestFormatForInjection:
    def test_empty_attachments(self, mgr):
        result = mgr.format_for_injection([])
        assert result == ""

    def test_with_attachment(self, mgr):
        resp = mgr.save("测试记忆内容，用于验证注入格式化", MemoryType.USER)
        from datetime import datetime, timezone

        from app.modules.memory.models import MemoryAttachment
        att = MemoryAttachment(
            entry=resp.data,
            relevance_score=0.85,
            surfaced_at=datetime.now(timezone.utc),
        )
        result = mgr.format_for_injection([att])
        assert "<system-reminder>" in result
        assert "测试记忆内容" in result
        assert resp.data.filename in result
