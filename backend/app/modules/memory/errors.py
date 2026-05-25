"""Error types for the memory system."""

from typing import Any, Dict, Optional


class MemorySystemError(Exception):
    """Base exception for memory system."""

    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class SecurityError(MemorySystemError):
    """Raised for path traversal and other security violations."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("SECURITY_ERROR", message, details)


class FileNotFoundInMemoryError(MemorySystemError):
    """Raised when a memory file does not exist."""

    def __init__(self, path: str):
        super().__init__("FILE_NOT_FOUND", f"记忆文件不存在: {path}", {"path": path})


class InvalidMemoryTypeError(MemorySystemError):
    """Raised when the memory type is invalid."""

    def __init__(self, received: str):
        super().__init__(
            "INVALID_TYPE",
            f"无效的记忆类型: {received}。有效值: user, feedback, project, reference",
            {"received": received},
        )


class MissingRequiredFieldError(MemorySystemError):
    """Raised when a required frontmatter field is missing."""

    def __init__(self, field: str, filename: str):
        super().__init__(
            "MISSING_FIELD",
            f"文件 '{filename}' 缺少必填字段: {field}",
            {"field": field, "filename": filename},
        )


class DuplicateMemoryError(MemorySystemError):
    """Raised when attempting to create a duplicate memory entry."""

    def __init__(self, existing_path: str):
        super().__init__(
            "DUPLICATE",
            f"重复的记忆条目，已存在: {existing_path}",
            {"existing_path": existing_path},
        )


class FileSizeExceededError(MemorySystemError):
    """Raised when a memory file exceeds the size limit."""

    def __init__(self, size: int, limit: int):
        super().__init__(
            "FILE_TOO_LARGE",
            f"文件大小 ({size} bytes) 超过限制 ({limit} bytes)，请精简内容。",
            {"size": size, "limit": limit},
        )


class MemoryPermissionError(MemorySystemError):
    """Raised when there is insufficient permission."""

    def __init__(self, path: str):
        super().__init__("PERMISSION_DENIED", f"权限不足，无法操作文件: {path}", {"path": path})


class DiskFullError(MemorySystemError):
    """Raised when disk space is insufficient."""

    def __init__(self):
        super().__init__("DISK_FULL", "磁盘空间不足，无法写入记忆文件。")


class IndexCorruptedError(MemorySystemError):
    """Raised when MEMORY.md index is corrupted."""

    def __init__(self):
        super().__init__("INDEX_CORRUPTED", "索引文件已损坏，将自动重建。")


class ExtractionTimeoutError(MemorySystemError):
    """Raised when the extraction agent times out."""

    def __init__(self):
        super().__init__("EXTRACTION_TIMEOUT", "记忆提取超时，跳过本次提取。")


class MemoryLockError(MemorySystemError):
    """Raised when file lock cannot be acquired."""

    def __init__(self):
        super().__init__("LOCK_FAILED", "无法获取文件锁，可能其他进程正在写入。")
