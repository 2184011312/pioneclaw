"""Data models for the AI Agent Memory System."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class MemoryType(str, Enum):
    USER = "user"
    FEEDBACK = "feedback"
    PROJECT = "project"
    REFERENCE = "reference"


@dataclass
class MemoryMetadata:
    name: str
    description: str
    type: MemoryType = MemoryType.USER
    tags: List[str] = field(default_factory=list)
    created: Optional[datetime] = None
    updated: Optional[datetime] = None


@dataclass
class MemoryEntry:
    id: str
    filename: str
    name: str
    description: str
    type: MemoryType
    content: str
    created_at: datetime
    updated_at: datetime
    freshness: str = ""
    is_stale: bool = False
    tags: List[str] = field(default_factory=list)


@dataclass
class MemoryAttachment:
    entry: MemoryEntry
    relevance_score: float
    surfaced_at: datetime = field(default_factory=datetime.now)


@dataclass
class RecallOptions:
    max_results: int = 5
    min_relevance: float = 0.3
    exclude_types: List[MemoryType] = field(default_factory=list)
    include_stale: bool = False


@dataclass
class ListOptions:
    type: Optional[Union[MemoryType, List[MemoryType]]] = None
    sort_by: str = "updatedAt"
    order: str = "desc"
    limit: Optional[int] = None
    offset: int = 0


@dataclass
class SearchOptions:
    type: Optional[Union[MemoryType, List[MemoryType]]] = None
    case_sensitive: bool = False
    limit: Optional[int] = None


@dataclass
class Message:
    uuid: str
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConversationContext:
    session_id: str
    messages: List[Message] = field(default_factory=list)
    last_memory_message_uuid: Optional[str] = None
    main_agent_wrote_memory: bool = False


@dataclass
class ExtractionResult:
    extracted: int = 0
    skipped: bool = False
    reason: Optional[str] = None
    new_entries: List[MemoryEntry] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ManifestEntry:
    filename: str
    name: str
    description: str
    type: MemoryType


@dataclass
class RankedMemory:
    filename: str
    relevance_score: float


@dataclass
class IndexEntry:
    filename: str
    description: str
    path: str


class ErrorLevel(str, Enum):
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"


@dataclass
class MemoryError:
    code: str
    message: str
    level: ErrorLevel = ErrorLevel.ERROR
    recoverable: bool = True
    details: Optional[Dict[str, Any]] = None


@dataclass
class MemoryResult:
    success: bool = True
    data: Any = None


@dataclass
class MemoryFailure:
    success: bool = False
    error: MemoryError = None


MemoryResponse = Union[MemoryResult, MemoryFailure]
