"""
MemoryStore 单元测试

覆盖：读写文件、frontmatter 解析、原子写入、大小限制
"""
import os
import tempfile
from datetime import datetime, timezone

import pytest

from app.modules.memory.errors import (
    FileNotFoundInMemoryError,
    FileSizeExceededError,
    InvalidMemoryTypeError,
    MissingRequiredFieldError,
)
from app.modules.memory.memory_store import MAX_FILE_SIZE, MemoryStore, generate_filename
from app.modules.memory.models import MemoryEntry, MemoryType


@pytest.fixture
def store():
    """创建临时目录作为记忆存储。"""
    tmp = tempfile.mkdtemp(prefix="memory_test_")
    s = MemoryStore(tmp)
    yield s
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def sample_entry():
    return MemoryEntry(
        id="user-hello.md",
        filename="user-hello.md",
        name="hello",
        description="A test memory",
        type=MemoryType.USER,
        content="This is a test memory content.",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestGenerateFilename:
    def test_user_type(self):
        fn = generate_filename(MemoryType.USER, "my setting")
        assert fn.startswith("user-")
        assert fn.endswith(".md")

    def test_project_type(self):
        fn = generate_filename(MemoryType.PROJECT, "API Design")
        assert fn.startswith("project-")
        assert "api-design" in fn


class TestMemoryStoreWriteRead:
    def test_write_and_read(self, store, sample_entry):
        store.write_file(sample_entry)
        entry = store.read_file(sample_entry.filename)
        assert entry.name == "hello"
        assert entry.description == "A test memory"
        assert entry.content == "This is a test memory content."
        assert entry.type == MemoryType.USER

    def test_read_nonexistent_raises(self, store):
        with pytest.raises(FileNotFoundInMemoryError):
            store.read_file("nonexistent.md")

    def test_write_atomic(self, store, sample_entry):
        store.write_file(sample_entry)
        # Write again — should overwrite cleanly
        sample_entry.content = "Updated content."
        store.write_file(sample_entry)
        entry = store.read_file(sample_entry.filename)
        assert entry.content == "Updated content."

    def test_delete_existing(self, store, sample_entry):
        store.write_file(sample_entry)
        assert store.delete_file(sample_entry.filename) is True
        with pytest.raises(FileNotFoundInMemoryError):
            store.read_file(sample_entry.filename)

    def test_delete_nonexistent(self, store):
        assert store.delete_file("ghost.md") is False

    def test_scan_files_empty(self, store):
        manifest = store.scan_files()
        assert len(manifest) == 0

    def test_scan_files_with_entries(self, store, sample_entry):
        store.write_file(sample_entry)
        manifest = store.scan_files()
        assert len(manifest) == 1
        assert manifest[0].filename == sample_entry.filename

    def test_scan_files_skips_memory_md(self, store):
        # Create a MEMORY.md file — should be excluded from manifest
        idx_path = os.path.join(store.memory_root, "MEMORY.md")
        with open(idx_path, "w", encoding="utf-8") as f:
            f.write("# Index\n")

        manifest = store.scan_files()
        for m in manifest:
            assert m.filename != "MEMORY.md"


class TestMemoryStoreGetAll:
    def test_get_all_empty(self, store):
        entries = store.get_all_files()
        assert entries == []

    def test_get_all_with_entries(self, store, sample_entry):
        store.write_file(sample_entry)
        entries = store.get_all_files()
        assert len(entries) >= 1

    def test_search_fulltext(self, store, sample_entry):
        store.write_file(sample_entry)
        matches = store.search_fulltext("test memory")
        assert sample_entry.filename in matches

    def test_search_no_match(self, store, sample_entry):
        store.write_file(sample_entry)
        matches = store.search_fulltext("nonexistent_content_xyz")
        assert len(matches) == 0


class TestFrontmatter:
    def test_missing_frontmatter_raises(self, store):
        path = os.path.join(store.memory_root, "bad.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("Just content, no frontmatter.")
        with pytest.raises(MissingRequiredFieldError):
            store.read_file("bad.md")

    def test_missing_name_field_raises(self, store):
        path = os.path.join(store.memory_root, "bad.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("---\ndescription: no name\n---\nbody")
        with pytest.raises(MissingRequiredFieldError, match="name"):
            store.read_file("bad.md")

    def test_invalid_type_raises(self, store):
        path = os.path.join(store.memory_root, "bad.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("---\nname: test\ndescription: desc\ntype: invalid_xyz\n---\nbody")
        with pytest.raises(InvalidMemoryTypeError):
            store.read_file("bad.md")


class TestFileSize:
    def test_size_limit(self, store):
        entry = MemoryEntry(
            id="user-big.md",
            filename="user-big.md",
            name="big",
            description="too big",
            type=MemoryType.USER,
            content="x" * (MAX_FILE_SIZE + 1),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        with pytest.raises(FileSizeExceededError):
            store.write_file(entry)


class TestFreshness:
    def test_today(self, store):
        label, is_stale = store._compute_freshness(datetime.now(timezone.utc))
        assert label == "今天"
        assert is_stale is False

    def test_stale_after_30_days(self):
        old = datetime.now(timezone.utc).replace(day=1)
        # Set to 40 days ago
        from datetime import timedelta
        old = datetime.now(timezone.utc) - timedelta(days=40)
        tmp = tempfile.mkdtemp(prefix="mem_fresh_")
        s = MemoryStore(tmp)
        _, stale = s._compute_freshness(old)
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
        assert stale is True
