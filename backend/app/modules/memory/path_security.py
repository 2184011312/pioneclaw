"""Path traversal protection for memory file operations."""

import os
import unicodedata

from .errors import SecurityError


class PathSecurity:
    """Validates and resolves memory file paths to prevent path traversal attacks."""

    @staticmethod
    def resolve_memory_path(input_path: str, memory_root: str) -> str:
        if not input_path or input_path.strip() == "":
            raise SecurityError("路径不能为空")

        if "\0" in input_path:
            raise SecurityError("路径包含非法字符 (null byte)")

        normalized = unicodedata.normalize("NFC", input_path)

        joined = os.path.join(memory_root, normalized)
        resolved = os.path.normpath(os.path.abspath(joined))

        try:
            real_path = os.path.realpath(resolved)
        except OSError:
            real_path = resolved

        real_root = os.path.realpath(os.path.abspath(memory_root))
        if not (
            real_path.startswith(real_root + os.sep) or real_path == real_root
        ):
            raise SecurityError(f"路径越界: {input_path}")

        basename = os.path.basename(real_path)
        if basename.startswith(".") and basename != ".lock":
            raise SecurityError("不允许操作隐藏文件")

        if basename == "MEMORY.md":
            raise SecurityError("不允许直接操作索引文件")

        return real_path

    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Validate and sanitize a memory file name.

        Returns the sanitized filename.
        Raises SecurityError if the name contains dangerous characters.
        """
        if not filename:
            raise SecurityError("文件名不能为空")

        dangerous_chars = ["\n", "\r", "\t", "\x00", "\\", "/"]
        for char in dangerous_chars:
            if char in filename:
                raise SecurityError(f"文件名包含非法字符: {repr(char)}")

        filename = filename.strip()
        if filename.startswith("."):
            raise SecurityError("文件名不能以 '.' 开头")

        return filename
