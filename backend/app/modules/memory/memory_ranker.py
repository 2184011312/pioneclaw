"""Semantic ranking of memory entries — LLM primary, keyword/TF-IDF fallback."""

from __future__ import annotations

import re
from typing import Callable, List, Optional

from .memory_store import MemoryStore
from .models import ManifestEntry, MemoryType, RankedMemory


class MemoryRanker:
    """Two-phase ranking: (1) LLM semantic screening, (2) freshness weighting.

    Fallback chain: LLM → TF-IDF keyword → recent N entries.
    """

    MAX_RANK_RESULTS = 5

    def __init__(
        self,
        memory_store: MemoryStore,
        llm_query_fn: Optional[Callable[[str], str]] = None,
    ):
        self.store = memory_store
        self._llm_query = llm_query_fn

    def rank(
        self,
        manifest: List[ManifestEntry],
        query: str,
        exclude_types: Optional[List[MemoryType]] = None,
        include_stale: bool = False,
    ) -> List[RankedMemory]:
        """Rank memory entries by relevance to the query. Returns top-N results."""
        if not manifest:
            return []

        filtered = self._filter_by_type(manifest, exclude_types or [])

        if not filtered:
            return []

        if self._llm_query:
            ranked = self._llm_rank(filtered, query)
            if ranked is not None:
                ranked = self._apply_freshness_weight(ranked, include_stale)
                return ranked[: self.MAX_RANK_RESULTS]

        ranked = self._keyword_rank(filtered, query)
        if ranked:
            ranked = self._apply_freshness_weight(ranked, include_stale)
            return ranked[: self.MAX_RANK_RESULTS]

        return self._recent_entries(manifest, exclude_types or [])[
            : self.MAX_RANK_RESULTS
        ]

    def _llm_rank(
        self, manifest: List[ManifestEntry], query: str
    ) -> Optional[List[RankedMemory]]:
        """Use LLM to rank entries by relevance. Returns None on failure."""
        prompt = self._build_ranking_prompt(manifest, query)
        try:
            response = self._llm_query(prompt)
            filenames = self._parse_ranking_response(response)
        except Exception:
            return None

        results: List[RankedMemory] = []
        for i, fname in enumerate(filenames):
            for m in manifest:
                if m.filename == fname:
                    score = 1.0 - (i * 0.15)
                    score = max(score, 0.15)
                    results.append(RankedMemory(filename=fname, relevance_score=score))
                    break

        return results if results else None

    def _keyword_rank(
        self, manifest: List[ManifestEntry], query: str
    ) -> List[RankedMemory]:
        """Keyword + character-overlap ranking as fallback (handles Chinese)."""
        results: List[RankedMemory] = []
        query_lower = query.lower()

        for m in manifest:
            doc_text = f"{m.name} {m.description}".lower()

            word_terms = set(re.findall(r"\w+", query_lower))
            doc_word_terms = set(re.findall(r"\w+", doc_text))
            word_overlap = word_terms & doc_word_terms

            query_chars = set(c for c in query_lower if c.isalnum())
            doc_chars = set(c for c in doc_text if c.isalnum())
            char_overlap = query_chars & doc_chars
            char_score = len(char_overlap) / max(len(query_chars), 1)

            sub_score = 0.0
            for term in word_terms:
                if term and len(term) >= 2 and term in doc_text:
                    sub_score = max(sub_score, 0.5)

            score = max(
                (len(word_overlap) / max(len(word_terms), 1)) * 0.7 if word_terms else 0,
                char_score * 0.5,
                sub_score,
            )

            if score > 0:
                results.append(
                    RankedMemory(filename=m.filename, relevance_score=round(score, 4))
                )

        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results

    def _recent_entries(
        self,
        manifest: List[ManifestEntry],
        exclude_types: Optional[List[MemoryType]] = None,
    ) -> List[RankedMemory]:
        """Return the most recently updated entries as last-resort fallback."""
        filtered = self._filter_by_type(manifest, exclude_types or [])
        results: List[RankedMemory] = []
        for m in filtered:
            results.append(RankedMemory(filename=m.filename, relevance_score=0.1))
        return sorted(results, key=lambda r: r.relevance_score, reverse=True)

    def _apply_freshness_weight(
        self, ranked: List[RankedMemory], include_stale: bool
    ) -> List[RankedMemory]:
        """Apply freshness bonus weighting: final = relevance * 0.8 + freshness * 0.2."""
        weighted: List[RankedMemory] = []
        for r in ranked:
            try:
                entry = self.store.read_file(r.filename)
            except Exception:
                weighted.append(r)
                continue

            bonus = MemoryStore.compute_freshness_bonus(entry.updated_at)
            if entry.is_stale:
                if not include_stale:
                    bonus = 0.05

            final_score = r.relevance_score * 0.8 + bonus * 0.2
            weighted.append(
                RankedMemory(
                    filename=r.filename,
                    relevance_score=round(final_score, 4),
                )
            )

        weighted.sort(key=lambda r: r.relevance_score, reverse=True)
        return weighted

    def _filter_by_type(
        self,
        manifest: List[ManifestEntry],
        exclude_types: List[MemoryType],
    ) -> List[ManifestEntry]:
        if not exclude_types:
            return list(manifest)
        exclude_values = {t.value for t in exclude_types}
        return [m for m in manifest if m.type.value not in exclude_values]

    @staticmethod
    def _build_ranking_prompt(manifest: List[ManifestEntry], query: str) -> str:
        lines = ["你是一个记忆相关性排序助手。\n"]
        lines.append("给定用户的查询和记忆清单，选出最相关的记忆。\n\n")
        lines.append(f"用户查询: {query}\n\n")
        lines.append("记忆清单:\n")
        for m in manifest:
            lines.append(f"{m.filename} — {m.description}\n")
        lines.append("\n请返回最相关的记忆文件名（最多5个），按相关性降序排列。\n")
        lines.append("只返回文件名，每行一个。如果没有相关的记忆，返回 NONE。\n")
        return "".join(lines)

    @staticmethod
    def _parse_ranking_response(response: str) -> List[str]:
        filenames: List[str] = []
        for line in response.strip().splitlines():
            fname = line.strip()
            if not fname or fname.upper() == "NONE":
                continue
            if "," in fname:
                fname = fname.split(",")[0].strip()
            if fname.endswith(".md"):
                filenames.append(fname)
            elif fname:
                filenames.append(fname)
                if not fname.endswith(".md"):
                    filenames[-1] = fname + ".md" if not fname.endswith(".md") else fname
        return filenames[:5]
