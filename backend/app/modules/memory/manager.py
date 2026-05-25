"""Memory Manager — thread-safe singleton wrapper around MemoryManage.

Provides the global singleton pattern used by tools and API endpoints
to access the memory system without passing the manager through every layer.
"""

import logging
import threading
from typing import Callable, Optional

from .memory_manage import MemoryManage

logger = logging.getLogger(__name__)

_memory_manager: Optional[MemoryManage] = None
_lock = threading.Lock()


def get_current_memory_manager() -> Optional[MemoryManage]:
    """Get the thread-safe singleton MemoryManage instance."""
    return _memory_manager


def set_current_memory_manager(mm: Optional[MemoryManage]) -> None:
    """Set the thread-safe singleton MemoryManage instance."""
    global _memory_manager
    with _lock:
        _memory_manager = mm


def create_memory_manager(
    memory_root: str,
    llm_query_fn: Optional[Callable[[str], str]] = None,
    extract_agent_fn: Optional[Callable[[str, str], str]] = None,
) -> MemoryManage:
    """Create, register and return the singleton MemoryManage instance."""
    mm = MemoryManage(
        memory_root=memory_root,
        llm_query_fn=llm_query_fn,
        extract_agent_fn=extract_agent_fn,
    )
    set_current_memory_manager(mm)
    return mm
