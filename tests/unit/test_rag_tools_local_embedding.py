"""RAG 本地嵌入配置與遷移測試。"""

import os
import sys
from typing import Any

import pytest

# 添加 src 目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from backend.tools.rag import RAGConfig, RAGTools  # noqa: E402


class FakeCollection:
    """簡化版 Chroma collection stub。"""

    def __init__(self, rows: list[tuple[str, str, dict[str, Any]]]):
        self._rows = list(rows)
        self.upsert_calls: list[dict[str, Any]] = []

    def count(self) -> int:
        return len(self._rows)

    def get(
        self,
        include: list[str] | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> dict[str, Any]:
        end = None if limit is None else offset + limit
        chunk = self._rows[offset:end]
        return {
            "ids": [row[0] for row in chunk],
            "documents": [row[1] for row in chunk],
            "metadatas": [row[2] for row in chunk],
        }

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None:
        self.upsert_calls.append(
            {
                "ids": ids,
                "documents": documents,
                "metadatas": metadatas,
                "embeddings": embeddings,
            }
        )
        for index, doc_id in enumerate(ids):
            self._rows.append((doc_id, documents[index], metadatas[index]))


class FakeDbClient:
    """僅提供舊 collection 讀取的 DB stub。"""

    def __init__(self, legacy_collection: FakeCollection):
        self.legacy_collection = legacy_collection

    def get_collection(self, name: str) -> FakeCollection:
        if name != "markdown_documents_openai":
            raise RuntimeError(f"Unknown collection: {name}")
        return self.legacy_collection


def test_rag_config_defaults_to_local_minilm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """預設應該是本地 MiniLM collection。"""
    monkeypatch.delenv("EMBEDDING_PROVIDER", raising=False)
    monkeypatch.delenv("LOCAL_MODEL_NAME", raising=False)
    monkeypatch.delenv("CHROMA_COLLECTION_NAME", raising=False)

    config = RAGConfig.from_env()

    assert config.local_model_name == "all-MiniLM-L6-v2"
    assert config.get_collection_name() == "markdown_documents_minilm"


def test_rag_config_rejects_non_local_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """不允許非 local 的 provider 設定。"""
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")

    with pytest.raises(
        ValueError,
        match="Only local embeddings are supported",
    ):
        RAGConfig.from_env()


def test_ragtools_init_does_not_require_openai_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """local 模式初始化不應依賴 OPENAI_API_KEY。"""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")
    monkeypatch.setattr(RAGTools, "_initialize_db", lambda self: None)

    tools = RAGTools()

    assert isinstance(tools, RAGTools)


def test_auto_migrate_from_openai_collection_runs_once(tmp_path) -> None:
    """啟動遷移應完成資料搬移，且由 marker 防止重複執行。"""
    target_collection = FakeCollection([])
    legacy_collection = FakeCollection(
        [
            ("doc-1", "resume section 1", {"source": "resume.md"}),
            ("doc-2", "resume section 2", {"source": "resume.md"}),
        ]
    )

    tools = object.__new__(RAGTools)
    tools.config = RAGConfig(
        local_model_name="all-MiniLM-L6-v2",
        db_path=str(tmp_path),
        batch_size=2,
    )
    tools.collection = target_collection
    tools.dbClient = FakeDbClient(legacy_collection)
    tools._embed_texts_local = lambda docs: [[0.1, 0.2] for _ in docs]

    tools._auto_migrate_from_openai_collection("markdown_documents_minilm")
    marker_path = tools._get_migration_marker_path("markdown_documents_minilm")

    assert os.path.exists(marker_path)
    assert len(target_collection.upsert_calls) == 1
    assert target_collection.count() == 2

    tools._auto_migrate_from_openai_collection("markdown_documents_minilm")
    assert len(target_collection.upsert_calls) == 1
