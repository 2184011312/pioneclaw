"""
路径安全测试 — path_security.py

覆盖：路径越界防护、隐藏文件拦截、null byte 检查、索引文件保护
"""
import os
import tempfile

import pytest

from app.modules.memory.errors import SecurityError
from app.modules.memory.path_security import PathSecurity


class TestPathSecurity:
    def test_normal_path_ok(self):
        root = os.path.join(tempfile.gettempdir(), "memory_test")
        os.makedirs(root, exist_ok=True)
        try:
            result = PathSecurity.resolve_memory_path("user-test.md", root)
            assert result.endswith("user-test.md")
        finally:
            os.rmdir(root)

    def test_empty_path_raises(self):
        root = os.path.join(tempfile.gettempdir(), "memory_test")
        os.makedirs(root, exist_ok=True)
        try:
            with pytest.raises(SecurityError, match="路径不能为空"):
                PathSecurity.resolve_memory_path("", root)
            with pytest.raises(SecurityError, match="路径不能为空"):
                PathSecurity.resolve_memory_path("   ", root)
        finally:
            os.rmdir(root)

    def test_null_byte_raises(self):
        root = os.path.join(tempfile.gettempdir(), "memory_test")
        os.makedirs(root, exist_ok=True)
        try:
            with pytest.raises(SecurityError, match="null byte"):
                PathSecurity.resolve_memory_path("good\x00bad.md", root)
        finally:
            os.rmdir(root)

    def test_path_traversal_raises(self):
        root = os.path.join(tempfile.gettempdir(), "memory_test")
        os.makedirs(root, exist_ok=True)
        try:
            with pytest.raises(SecurityError, match="路径越界"):
                PathSecurity.resolve_memory_path("../outside.md", root)
        finally:
            os.rmdir(root)

    def test_hidden_file_raises(self):
        root = os.path.join(tempfile.gettempdir(), "memory_test")
        os.makedirs(root, exist_ok=True)
        try:
            with pytest.raises(SecurityError, match="隐藏文件"):
                PathSecurity.resolve_memory_path(".secret.md", root)
        finally:
            os.rmdir(root)

    def test_index_file_raises(self):
        root = os.path.join(tempfile.gettempdir(), "memory_test")
        os.makedirs(root, exist_ok=True)
        try:
            with pytest.raises(SecurityError, match="索引文件"):
                PathSecurity.resolve_memory_path("MEMORY.md", root)
        finally:
            os.rmdir(root)

    def test_lock_file_allowed(self):
        root = os.path.join(tempfile.gettempdir(), "memory_test")
        os.makedirs(root, exist_ok=True)
        try:
            result = PathSecurity.resolve_memory_path(".lock", root)
            assert result.endswith(".lock")
        finally:
            os.rmdir(root)

    def test_validate_filename_normal(self):
        assert PathSecurity.validate_filename("user-test.md") == "user-test.md"

    def test_validate_filename_empty_raises(self):
        with pytest.raises(SecurityError, match="文件名不能为空"):
            PathSecurity.validate_filename("")

    def test_validate_filename_dot_start_raises(self):
        with pytest.raises(SecurityError, match="不能以 '.' 开头"):
            PathSecurity.validate_filename(".hidden.md")

    def test_validate_filename_newline_raises(self):
        with pytest.raises(SecurityError, match="非法字符"):
            PathSecurity.validate_filename("bad\nname.md")

    def test_validate_filename_slash_raises(self):
        with pytest.raises(SecurityError, match="非法字符"):
            PathSecurity.validate_filename("sub/file.md")
