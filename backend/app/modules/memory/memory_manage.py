"""Main public API — the single entry point for Agents to interact with memory."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable, List, Optional, Union

from .errors import (
    FileNotFoundInMemoryError,
    InvalidMemoryTypeError,
    MemorySystemError,
    MissingRequiredFieldError,
)
from .memory_extractor import DUPLICATE_SIMILARITY_THRESHOLD, MemoryExtractor, _text_overlap_ratio
from .memory_index import MemoryIndex
from .memory_ranker import MemoryRanker
from .memory_store import MemoryStore, generate_filename
from .models import (
    ConversationContext,
    ExtractionResult,
    ListOptions,
    MemoryAttachment,
    MemoryEntry,
    MemoryFailure,
    MemoryMetadata,
    MemoryResponse,
    MemoryResult,
    MemoryType,
    RecallOptions,
    SearchOptions,
)

logger = logging.getLogger(__name__)


class MemoryManage:
    """Facade for the AI Agent Memory System.

    The Agent interacts exclusively through this interface. All internal
    modules (MemoryStore, MemoryIndex, MemoryRanker, MemoryExtractor) are
    transparent to the caller.

    Usage:
        mgr = MemoryManage(
            memory_root="~/.agent/memory",
            llm_query_fn=my_llm_call,
            extract_agent_fn=my_agent_runner,
        )
        attachments = mgr.recall("help me write an API endpoint")
    """

    def __init__(
        self,
        memory_root: str,
        llm_query_fn: Optional[Callable[[str], str]] = None,
        extract_agent_fn: Optional[Callable[[str, str], str]] = None,
        turns_between_extraction: int = 5,
    ):
        self.store = MemoryStore(memory_root)
        self.index = MemoryIndex(memory_root)
        self.ranker = MemoryRanker(self.store, llm_query_fn)
        self.extractor = MemoryExtractor(
            self.store,
            self.index,
            extract_agent_fn or (lambda _sys, _usr: ""),
            turns_between_extraction,
        )

    # ═══════════════════════════════════════════════════════════════
    # recall — auto-retrieve relevant memories
    # ═══════════════════════════════════════════════════════════════

    def recall(
        self, query: str, options: Optional[RecallOptions] = None
    ) -> List[MemoryAttachment]:
        """Retrieve memories relevant to the given query."""
        opts = options or RecallOptions()
        try:
            manifest = self.store.scan_files()
            if not manifest:
                return []

            ranked = self.ranker.rank(
                manifest,
                query,
                exclude_types=opts.exclude_types,
                include_stale=opts.include_stale,
            )

            ranked = [
                r
                for r in ranked
                if r.relevance_score >= opts.min_relevance
            ]
            ranked = ranked[: opts.max_results]

            attachments: List[MemoryAttachment] = []
            surfaced = set()
            for r in ranked:
                if r.filename in surfaced:
                    continue
                surfaced.add(r.filename)
                try:
                    entry = self.store.read_file(r.filename)
                    attachments.append(
                        MemoryAttachment(
                            entry=entry,
                            relevance_score=r.relevance_score,
                            surfaced_at=datetime.now(timezone.utc),
                        )
                    )
                except Exception as e:
                    logger.warning("读取记忆文件 %s 失败: %s", r.filename, e)
                    continue

            return attachments

        except Exception as e:
            logger.error("召回失败: %s", e)
            return []

    # ═══════════════════════════════════════════════════════════════
    # save — create a new memory entry
    # ═══════════════════════════════════════════════════════════════

    def save(
        self,
        content: str,
        mem_type: Union[MemoryType, str],
        metadata: Optional[MemoryMetadata] = None,
        upsert: bool = False,
    ) -> MemoryResponse:
        """Save a new memory entry.

        When upsert=True and a duplicate is detected, the existing entry is
        updated with the new content instead of returning the old entry.
        """
        try:
            if not content or not content.strip():
                return MemoryFailure(
                    False,
                    MissingRequiredFieldError("content", "(new)")
                )

            if isinstance(mem_type, str):
                try:
                    mem_type = MemoryType(mem_type)
                except ValueError:
                    return MemoryFailure(False, InvalidMemoryTypeError(mem_type))

            meta = metadata or MemoryMetadata(
                name="",
                description="",
                type=mem_type,
            )

            if not meta.name:
                meta.name = content.strip()[:50]
            if not meta.description:
                meta.description = content.strip()[:100]

            filename = generate_filename(mem_type, meta.name)

            existing_manifest = self.store.scan_files()
            dup = self._find_duplicate(meta, existing_manifest)
            if dup:
                if upsert:
                    return self.update(dup.filename, content, meta)
                return MemoryResult(True, dup)

            now = datetime.now(timezone.utc)
            entry = MemoryEntry(
                id=filename,
                filename=filename,
                name=meta.name,
                description=meta.description,
                type=mem_type,
                content=content.strip(),
                created_at=now,
                updated_at=now,
                freshness="今天",
                is_stale=False,
                tags=meta.tags or [],
            )

            self.store.write_file(entry)

            try:
                self.index.add_entry(filename, meta.description)
            except Exception as e:
                logger.error("索引更新失败，回滚文件写入: %s", e)
                self.store.delete_file(filename)
                return MemoryFailure(False, e)

            return MemoryResult(True, entry)

        except MemorySystemError as e:
            return MemoryFailure(False, e)
        except Exception as e:
            logger.error("保存记忆失败: %s", e)
            return MemoryFailure(False, e)

    # ═══════════════════════════════════════════════════════════════
    # update — modify an existing memory entry
    # ═══════════════════════════════════════════════════════════════

    def update(
        self,
        path: str,
        content: str,
        metadata: Optional[MemoryMetadata] = None,
    ) -> MemoryResponse:
        """Update an existing memory entry."""
        try:
            existing = self.store.read_file(path)

            existing.content = content
            existing.updated_at = datetime.now(timezone.utc)
            if metadata:
                if metadata.name:
                    existing.name = metadata.name
                if metadata.description:
                    existing.description = metadata.description
                    try:
                        self.index.update_entry(path, metadata.description)
                    except Exception as e:
                        logger.warning("索引更新失败: %s", e)
                if metadata.tags is not None:
                    existing.tags = metadata.tags

            self.store.write_file(existing)
            return MemoryResult(True, existing)

        except FileNotFoundInMemoryError as e:
            return MemoryFailure(False, e)
        except MemorySystemError as e:
            return MemoryFailure(False, e)
        except Exception as e:
            logger.error("更新记忆失败: %s", e)
            return MemoryFailure(False, e)

    # ═══════════════════════════════════════════════════════════════
    # delete — remove a memory entry
    # ═══════════════════════════════════════════════════════════════

    def delete(self, path: str) -> MemoryResponse:
        """Delete a memory entry and its index reference."""
        try:
            self.store.read_file(path)
            self.store.delete_file(path)

            try:
                self.index.remove_entry(path)
            except Exception as e:
                logger.error("索引删除失败，重建索引: %s", e)
                self.index.rebuild_index(self.store.scan_files())

            return MemoryResult(True, True)

        except FileNotFoundInMemoryError as e:
            return MemoryFailure(False, e)
        except MemorySystemError as e:
            return MemoryFailure(False, e)
        except Exception as e:
            logger.error("删除记忆失败: %s", e)
            return MemoryFailure(False, e)

    # ═══════════════════════════════════════════════════════════════
    # list — enumerate memory entries
    # ═══════════════════════════════════════════════════════════════

    def list(
        self, options: Optional[ListOptions] = None
    ) -> MemoryResponse:
        """List all memory entries with optional filtering."""
        try:
            entries = self.store.get_all_files()
            opts = options or ListOptions()

            if opts.type:
                types = (
                    [opts.type]
                    if isinstance(opts.type, MemoryType)
                    else opts.type
                )
                entries = [e for e in entries if e.type in types]

            reverse = opts.order == "desc"
            if opts.sort_by == "name":
                entries.sort(key=lambda e: e.name, reverse=reverse)
            elif opts.sort_by == "createdAt":
                entries.sort(key=lambda e: e.created_at, reverse=reverse)
            else:
                entries.sort(key=lambda e: e.updated_at, reverse=reverse)

            if opts.offset > 0:
                entries = entries[opts.offset:]
            if opts.limit is not None:
                entries = entries[: opts.limit]

            return MemoryResult(True, entries)

        except Exception as e:
            logger.error("列出记忆失败: %s", e)
            return MemoryResult(True, [])

    # ═══════════════════════════════════════════════════════════════
    # search — full-text keyword search
    # ═══════════════════════════════════════════════════════════════

    def search(
        self, keyword: str, options: Optional[SearchOptions] = None
    ) -> MemoryResponse:
        """Full-text search across memory files."""
        opts = options or SearchOptions()
        try:
            matches = self.store.search_fulltext(
                keyword,
                case_sensitive=opts.case_sensitive,
            )

            entries: List[MemoryEntry] = []
            for fname in matches:
                try:
                    entry = self.store.read_file(fname)
                    if opts.type:
                        types = (
                            [opts.type]
                            if isinstance(opts.type, MemoryType)
                            else opts.type
                        )
                        if entry.type in types:
                            entries.append(entry)
                    else:
                        entries.append(entry)
                except Exception:
                    continue

            if opts.limit is not None:
                entries = entries[: opts.limit]

            return MemoryResult(True, entries)

        except Exception as e:
            logger.error("搜索记忆失败: %s", e)
            return MemoryResult(True, [])

    # ═══════════════════════════════════════════════════════════════
    # auto_extract — trigger background memory extraction
    # ═══════════════════════════════════════════════════════════════

    def auto_extract(self, context: ConversationContext) -> ExtractionResult:
        """Trigger background memory extraction after a conversation turn."""
        try:
            return self.extractor.extract(context)
        except Exception as e:
            logger.error("自动提取失败: %s", e)
            return ExtractionResult(
                extracted=0,
                skipped=True,
                error=str(e),
            )

    # ═══════════════════════════════════════════════════════════════
    # format_for_injection — format recalled memories for system prompt
    # ═══════════════════════════════════════════════════════════════

    def format_for_injection(
        self, attachments: List[MemoryAttachment]
    ) -> str:
        """Format recalled memories as a system-reminder injection text."""
        if not attachments:
            return ""

        lines = [
            "<system-reminder>",
            "以下是与当前对话可能相关的记忆:",
            "",
        ]

        for i, att in enumerate(attachments):
            entry = att.entry
            stale_warning = ""
            if entry.is_stale:
                stale_warning = (
                    " ⚠ 注意：此记忆已超过 30 天未更新，可能不再准确。"
                )

            lines.append(
                f"[记忆 {i + 1}] "
                f"(类型: {entry.type.value}, "
                f"更新于: {entry.freshness}, "
                f"相关度: {att.relevance_score:.2f})"
            )
            lines.append(f"文件: {entry.filename}")
            lines.append(f"描述: {entry.description}")
            lines.append(f"内容摘要: {entry.content[:300]}")
            if stale_warning:
                lines.append(stale_warning)
            lines.append("")

        lines.append("</system-reminder>")
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    # internal helpers
    # ═══════════════════════════════════════════════════════════════

    def _check_duplicate(
        self,
        meta: MemoryMetadata,
        manifest: list,
    ) -> Optional[MemoryEntry]:
        """Check if a memory with the same slug or highly similar description exists."""
        slug = MemoryStore.generate_slug(meta.name)
        for m in manifest:
            existing_slug = MemoryStore.generate_slug(m.name)
            if slug == existing_slug:
                try:
                    return self.store.read_file(m.filename)
                except Exception:
                    pass
                break

        if meta.description:
            for m in manifest:
                if meta.description.lower() == m.description.lower():
                    try:
                        return self.store.read_file(m.filename)
                    except Exception:
                        pass
                    break
                ratio = _text_overlap_ratio(meta.description, m.description)
                if ratio >= DUPLICATE_SIMILARITY_THRESHOLD:
                    try:
                        return self.store.read_file(m.filename)
                    except Exception:
                        pass
                    break
        return None

    def _find_duplicate(
        self,
        meta: MemoryMetadata,
        manifest: list,
    ) -> Optional[MemoryEntry]:
        """Find a duplicate memory using all available detection methods.

        Checks in order: slug match → exact description → CJK 2-gram overlap
        → LLM semantic match. Earlier checks are cheaper and run first.
        """
        dup = self._check_duplicate(meta, manifest)
        if dup:
            return dup

        if self.ranker.has_llm:
            dup = self._check_semantic_duplicate(meta, manifest)
            if dup:
                return dup

        return None

    def _check_semantic_duplicate(
        self,
        meta: MemoryMetadata,
        manifest: list,
    ) -> Optional[MemoryEntry]:
        """Use LLM to check if the new memory is semantically the same topic
        as any existing memory. Returns the matching entry or None.

        Feeds MEMORY.md index content (not per-file frontmatter) to the LLM —
        one file read instead of N.  The index is capped at 25KB / 200 lines,
        so the prompt size is bounded independently of the number of files.

        Only called when faster checks (slug, exact, CJK overlap) have failed.
        LLM call failures are silently degraded — they never block save().
        """
        if not meta.description:
            return None

        try:
            import os

            index_path = self.index.index_path
            if not os.path.exists(index_path):
                return None

            with open(index_path, "r", encoding="utf-8") as f:
                index_content = f.read()

            # Defensive truncation: even though write-path truncate() keeps
            # the index within limits, the read path should not trust it blindly.
            lines = index_content.splitlines()
            if len(lines) > 200:
                index_content = "\n".join(lines[:200])
            encoded = index_content.encode("utf-8")
            if len(encoded) > 25 * 1024:
                index_content = encoded[:25 * 1024].decode("utf-8", errors="ignore")

            if not index_content.strip():
                return None

            prompt = (
                "你是一个记忆去重助手。判断新记忆是否与已有记忆讨论同一主题/事实/偏好。\n"
                "\n"
                f"新记忆名称: {meta.name}\n"
                f"新记忆描述: {meta.description}\n"
                "\n"
                "已有记忆索引 (MEMORY.md):\n"
                f"{index_content}\n"
                "\n"
                "如果新记忆与某条已有记忆讨论的是同一件事（即使表述不同），返回该记忆的文件名。\n"
                "判断标准: 两条记忆是否在描述同一个用户偏好、同一项目约定、同一条用户反馈？\n"
                "如果新记忆是全新内容，返回 NONE。\n"
                "只返回文件名或 NONE，不要其他文字。\n"
            )

            response = self.ranker.query(prompt)
            if response is None:
                return None

            filename = self._extract_filename_from_llm(response)
            if filename is None:
                return None

            for m in manifest:
                if m.filename == filename or m.filename == f"{filename}.md":
                    try:
                        return self.store.read_file(m.filename)
                    except Exception:
                        return None

        except Exception:
            logger.debug("LLM semantic duplicate check failed, skipping", exc_info=True)

        return None

    @staticmethod
    def _extract_filename_from_llm(response: str) -> Optional[str]:
        """Parse an LLM response into a bare filename (without .md suffix).

        Handles common LLM output variations:
          - "user-称呼偏好.md"
          - '"user-称呼偏好.md"'
          - '`user-称呼偏好.md`'
          - "文件名是 user-称呼偏好.md"
          - "```\nuser-称呼偏好.md\n```"
        """
        import re

        text = response.strip()

        if not text or text.upper() == "NONE":
            return None

        # 1. Remove markdown code fences
        text = re.sub(r"^```\w*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        # 2. Remove wrapping quotes and backticks
        text = text.strip().strip("\"'`")

        # 3. Try to extract a valid memory filename via regex
        #    Matches: {type}-{slug}.md where slug is word chars + hyphens
        match = re.search(r"[\w\-]+\.md", text)
        if match:
            basename = match.group(0)
        else:
            # Fallback: use the whole cleaned string as-is
            basename = text.strip().strip(".")

        # 4. Strip .md suffix for matching (caller will compare both forms)
        if basename.endswith(".md"):
            basename = basename[:-3]

        if not basename:
            return None

        return basename
