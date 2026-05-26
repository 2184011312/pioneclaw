"""MEMORY.md index file management — atomic writes, file locking, size limits."""

from __future__ import annotations

import os
import re
import tempfile
import time
from typing import Dict, List, Optional

from .errors import MemoryLockError
from .models import IndexEntry, ManifestEntry, MemoryType

MAX_INDEX_LINES = 200
MAX_INDEX_SIZE = 25 * 1024
LOCK_TIMEOUT = 2.0
INDEX_FILENAME = "MEMORY.md"

TYPE_HEADERS: Dict[MemoryType, str] = {
    MemoryType.USER: "## 用户偏好 (user)",
    MemoryType.FEEDBACK: "## 用户反馈 (feedback)",
    MemoryType.PROJECT: "## 项目知识 (project)",
    MemoryType.REFERENCE: "## 参考资料 (reference)",
}

HEADER_LINE_RE = re.compile(r"^## ")
ENTRY_LINE_RE = re.compile(r"^- \[(.+?)\]\((.+?\.md)\)\s*[—\-]\s*(.+)$")


class MemoryIndex:
    """Manages the MEMORY.md index file."""

    def __init__(self, memory_root: str):
        self.memory_root = os.path.abspath(memory_root)
        self.index_path = os.path.join(self.memory_root, INDEX_FILENAME)
        self.lock_path = os.path.join(self.memory_root, ".lock")

    def _acquire_lock(self) -> bool:
        """Acquire a file lock with up to 2-second timeout. Returns True on success."""
        deadline = time.time() + LOCK_TIMEOUT
        while time.time() < deadline:
            try:
                fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                return True
            except OSError:
                time.sleep(0.05)
        return False

    def _release_lock(self) -> None:
        """Release the file lock."""
        try:
            os.remove(self.lock_path)
        except OSError:
            pass

    def _ensure_index_file(self) -> None:
        """Create MEMORY.md if it doesn't exist."""
        if not os.path.exists(self.index_path):
            header = (
                "# 记忆索引\n\n"
                "此文件由系统自动维护，请勿手动编辑。\n\n"
                "## 用户偏好 (user)\n\n\n"
                "## 用户反馈 (feedback)\n\n\n"
                "## 项目知识 (project)\n\n\n"
                "## 参考资料 (reference)\n"
            )
            with open(self.index_path, "w", encoding="utf-8") as f:
                f.write(header)

    def add_entry(self, filename: str, description: str) -> None:
        """Add an entry to MEMORY.md under the appropriate type section."""
        self._ensure_index_file()

        if not self._acquire_lock():
            raise MemoryLockError()

        try:
            entry_line = f"- [{description}]({filename}) — {description}\n"

            with open(self.index_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            mem_type = self._infer_type_from_filename(filename)
            type_header = TYPE_HEADERS.get(mem_type, TYPE_HEADERS[MemoryType.USER])
            header_idx = self._find_header_index(lines, type_header)

            if header_idx is not None:
                insert_idx = self._find_insert_point(lines, header_idx, filename)
                lines.insert(insert_idx, entry_line)
            else:
                lines.append(entry_line)

            self._atomically_write_index(lines)
        finally:
            self._release_lock()

        self.truncate()

    def remove_entry(self, filename: str) -> None:
        """Remove an entry from MEMORY.md by filename."""
        if not os.path.exists(self.index_path):
            return

        if not self._acquire_lock():
            raise MemoryLockError()

        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            new_lines = [
                line
                for line in lines
                if not (ENTRY_LINE_RE.match(line) and f"({filename})" in line)
            ]

            self._atomically_write_index(new_lines)
        finally:
            self._release_lock()

    def update_entry(self, filename: str, new_description: str) -> None:
        """Update the description text of an entry in MEMORY.md."""
        if not os.path.exists(self.index_path):
            return

        if not self._acquire_lock():
            raise MemoryLockError()

        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                m = ENTRY_LINE_RE.match(line)
                if m and f"({filename})" in line:
                    title = m.group(1)
                    lines[i] = f"- [{title}]({filename}) — {new_description}\n"
                    break

            self._atomically_write_index(lines)
        finally:
            self._release_lock()

        self.truncate()

    def get_entries(self) -> List[IndexEntry]:
        """Parse MEMORY.md and return all index entries."""
        if not os.path.exists(self.index_path):
            return []

        with open(self.index_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        entries: List[IndexEntry] = []
        for line in lines:
            m = ENTRY_LINE_RE.match(line)
            if m:
                entries.append(
                    IndexEntry(
                        filename=m.group(2),
                        description=m.group(3).strip().lstrip("—").lstrip("-").strip(),
                        path=m.group(2),
                    )
                )
        return entries

    def rebuild_index(self, manifest: List[ManifestEntry]) -> None:
        """Rebuild the entire index from a list of ManifestEntry items."""
        if not self._acquire_lock():
            raise MemoryLockError()

        try:
            new_lines = self._build_index_lines(manifest)
            self._atomically_write_index(new_lines)
        finally:
            self._release_lock()

    def count_by_type(self) -> dict:
        """Return total and per-type counts from MEMORY.md index (no filesystem scan)."""
        entries = self.get_entries()
        by_type = {}
        for e in entries:
            mem_type = self._infer_type_from_filename(e.filename)
            key = mem_type.value
            by_type[key] = by_type.get(key, 0) + 1
        return {"total": len(entries), "by_type": by_type}

    def truncate(self) -> int:
        """Remove oldest entries if index exceeds line/size limits. Returns removed count."""
        if not os.path.exists(self.index_path):
            return 0

        with open(self.index_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if len(lines) <= MAX_INDEX_LINES and sum(len(line) for line in lines) <= MAX_INDEX_SIZE:
            return 0

        if not self._acquire_lock():
            raise MemoryLockError()

        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            removed = 0

            while (
                sum(len(line) for line in lines) > MAX_INDEX_SIZE
                or self._count_entry_lines(lines) > MAX_INDEX_LINES
            ):
                entry_indices = [
                    i for i, line in enumerate(lines) if ENTRY_LINE_RE.match(line)
                ]
                if not entry_indices:
                    break
                mtimes: Dict[int, float] = {}
                for idx in entry_indices:
                    m = ENTRY_LINE_RE.match(lines[idx])
                    filename = m.group(2)
                    fpath = os.path.join(self.memory_root, filename)
                    if os.path.exists(fpath):
                        mtimes[idx] = os.path.getmtime(fpath)
                    else:
                        mtimes[idx] = 0.0

                oldest_idx = min(mtimes, key=mtimes.get)
                del lines[oldest_idx]
                removed += 1

            self._atomically_write_index(lines)
            return removed
        finally:
            self._release_lock()

    def _atomically_write_index(self, lines: List[str]) -> None:
        """Write lines to a temp file, then atomically rename."""
        content = "".join(lines)
        encoded = content.encode("utf-8")

        fd, tmp_path = tempfile.mkstemp(
            dir=self.memory_root, prefix=".tmp_index_", suffix=".md"
        )
        try:
            os.write(fd, encoded)
            os.fsync(fd)
            os.close(fd)
            os.replace(tmp_path, self.index_path)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise

    def _build_index_lines(self, manifest: List[ManifestEntry]) -> List[str]:
        """Build the full index content from manifest entries, grouped by type."""
        grouped: Dict[MemoryType, List[ManifestEntry]] = {t: [] for t in MemoryType}
        for m in manifest:
            grouped[m.type].append(m)

        lines = [
            "# 记忆索引\n",
            "\n",
            "此文件由系统自动维护，请勿手动编辑。\n",
            "\n",
        ]

        for mem_type in MemoryType:
            lines.append(TYPE_HEADERS[mem_type] + "\n")
            lines.append("\n")
            entries = grouped[mem_type]
            entries.sort(key=lambda e: e.name)
            for entry in entries:
                desc_short = entry.description
                name_short = entry.name
                lines.append(
                    f"- [{name_short}]({entry.filename}) — {desc_short}\n"
                )
            lines.append("\n")

        return lines

    def _infer_type_from_filename(self, filename: str) -> MemoryType:
        """Infer the memory type from the filename prefix."""
        for mem_type in MemoryType:
            if filename.startswith(f"{mem_type.value}-"):
                return mem_type
        return MemoryType.USER

    def _find_header_index(self, lines: List[str], header: str) -> Optional[int]:
        """Find the line index of a type section header."""
        for i, line in enumerate(lines):
            if line.strip() == header:
                return i
        return None

    def _find_insert_point(
        self, lines: List[str], header_idx: int, filename: str
    ) -> int:
        """Find where to insert a new entry within its type section, keeping sorted order."""
        start = header_idx + 1
        insert_idx = start
        for i in range(start, len(lines)):
            if HEADER_LINE_RE.match(lines[i]):
                break
            m = ENTRY_LINE_RE.match(lines[i])
            if m and m.group(2) > filename:
                insert_idx = i
                break
            insert_idx = i + 1
        return min(insert_idx, len(lines))

    def _count_entry_lines(self, lines: List[str]) -> int:
        """Count the number of memory entry lines in the index."""
        return sum(1 for line in lines if ENTRY_LINE_RE.match(line))
