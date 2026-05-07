"""Compatibility shim for the removed RAG layer.

The project now uses Dify instead of the legacy local RAG implementation.
This shim preserves imports from older scripts without reintroducing the old
dependency stack.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class RAGTools:
    """Legacy placeholder that keeps old imports from breaking."""

    def __init__(self, *args: Any, **kwargs: Any):
        logger.warning("RAGTools 已退役，請改用 Dify Chatflow 流程")

    def rag_search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        logger.warning("RAGTools.rag_search 已停用，query=%s, top_k=%s", query, top_k)
        return []

    def clear_cache(self) -> None:
        return None

    def get_performance_stats(self) -> dict[str, Any]:
        return {"status": "deprecated", "backend": "dify"}
