"""AI Agent Memory System — 接口化的记忆管理模块。

Usage:
    from app.modules.memory import create_memory_manager, get_current_memory_manager

    mgr = create_memory_manager(
        memory_root="memory",
        llm_query_fn=your_llm_call_function,
        extract_agent_fn=your_agent_runner_function,
    )

    # Recall relevant memories
    attachments = mgr.recall("help me write an API endpoint")

    # Save a new memory
    result = mgr.save("用户喜欢用中文交流", MemoryType.USER)

    # Full-text search
    results = mgr.search("API认证")
"""

from .errors import (
    DuplicateMemoryError,
    ExtractionTimeoutError,
    FileNotFoundInMemoryError,
    FileSizeExceededError,
    IndexCorruptedError,
    InvalidMemoryTypeError,
    MemoryLockError,
    MemoryPermissionError,
    MemorySystemError,
    MissingRequiredFieldError,
    SecurityError,
)
from .manager import (
    create_memory_manager,
    get_current_memory_manager,
    set_current_memory_manager,
)
from .memory_extractor import MemoryExtractor
from .memory_index import MemoryIndex
from .memory_manage import MemoryManage
from .memory_ranker import MemoryRanker
from .memory_store import MemoryStore, generate_filename
from .models import (
    # Context
    ConversationContext,
    ErrorLevel,
    # Results
    ExtractionResult,
    IndexEntry,
    ListOptions,
    # Internal
    ManifestEntry,
    MemoryAttachment,
    MemoryEntry,
    # Errors
    MemoryError,
    MemoryFailure,
    MemoryMetadata,
    MemoryResponse,
    MemoryResult,
    # Core types
    MemoryType,
    Message,
    RankedMemory,
    # Options
    RecallOptions,
    SearchOptions,
)
from .path_security import PathSecurity

__all__ = [
    # Main API
    "MemoryManage",
    # Singleton
    "get_current_memory_manager",
    "set_current_memory_manager",
    "create_memory_manager",
    # Storage
    "MemoryStore",
    "MemoryIndex",
    "MemoryRanker",
    "MemoryExtractor",
    "PathSecurity",
    # Types
    "MemoryType",
    "MemoryMetadata",
    "MemoryEntry",
    "MemoryAttachment",
    "RecallOptions",
    "ListOptions",
    "SearchOptions",
    "ConversationContext",
    "Message",
    "ExtractionResult",
    "MemoryResult",
    "MemoryFailure",
    "MemoryResponse",
    "ManifestEntry",
    "RankedMemory",
    "IndexEntry",
    "MemoryError",
    "ErrorLevel",
    # Errors
    "MemorySystemError",
    "MemoryPermissionError",
    "SecurityError",
    "FileNotFoundInMemoryError",
    "InvalidMemoryTypeError",
    "MissingRequiredFieldError",
    "DuplicateMemoryError",
    "FileSizeExceededError",
    "IndexCorruptedError",
    "ExtractionTimeoutError",
    "MemoryLockError",
    # Utilities
    "generate_filename",
]
