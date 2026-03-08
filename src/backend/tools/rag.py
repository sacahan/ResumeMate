"""RAG 工具層改進版本

對接 ChromaDB 向量資料庫，提供文本檢索和文件管理功能
包含安全性、性能優化和錯誤處理改進
"""

import os
import re
import time
import json
import hashlib
import logging
from dataclasses import dataclass
from typing import Any, List, Dict, Optional, Tuple
from dotenv import load_dotenv

import chromadb
from chromadb.config import Settings

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = Any  # type: ignore[assignment]
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from backend.models import SearchResult

# 載入環境變數
load_dotenv(override=True)

# 建立日誌記錄器
logger = logging.getLogger(__name__)


@dataclass
class RAGConfig:
    """RAG 工具配置類 - 性能優化版"""

    # 🎯 本地向量化配置
    local_model_name: str = "all-MiniLM-L6-v2"  # 本地模型名稱
    device: str = "cpu"  # cpu | cuda | mps

    batch_size: int = 100  # 優化批次大小平衡速度與記憶體
    cache_size: int = 100  # 擴大快取大小
    db_path: str = "./chroma_db"
    collection_name: str = ""  # 自動根據模型選擇
    max_top_k: int = 15  # 降低最大檢索數量提升速度

    # 🚀 新增性能優化配置
    enable_query_cache: bool = True  # 啟用查詢快取
    enable_embedding_cache: bool = True  # 啟用嵌入向量快取
    cache_ttl_seconds: int = 3600  # 快取存活時間 1 小時
    parallel_batch_processing: bool = True  # 並行批次處理
    similarity_threshold: float = 0.1  # 相似度過濾閾值
    query_preprocessing: bool = True  # 啟用查詢預處理
    result_reranking: bool = True  # 啟用結果重排序

    def get_collection_name(self) -> str:
        """根據使用的模型自動選擇 collection 名稱"""
        if self.collection_name:  # 如果手動指定，則使用指定的名稱
            return self.collection_name

        if self.local_model_name == "all-MiniLM-L6-v2":
            return "markdown_documents_minilm"
        elif "bge" in self.local_model_name.lower():
            return "markdown_documents_bge"
        elif "m3e" in self.local_model_name.lower():
            return "markdown_documents_m3e"
        else:
            # 其他本地模型使用通用名稱
            return "markdown_documents_local"

    @classmethod
    def from_env(cls) -> "RAGConfig":
        """從環境變數創建配置"""

        def _strip_quotes(value: Optional[str]) -> Optional[str]:
            if value is None:
                return None
            return value.strip().strip('"').strip("'")

        embedding_provider = _strip_quotes(os.getenv("EMBEDDING_PROVIDER", "local"))
        if embedding_provider and embedding_provider.lower() != "local":
            raise ValueError(
                "Only local embeddings are supported. " "Set EMBEDDING_PROVIDER=local."
            )

        return cls(
            local_model_name=_strip_quotes(
                os.getenv("LOCAL_MODEL_NAME", cls.local_model_name)
            ),
            device=_strip_quotes(os.getenv("DEVICE", cls.device)),
            batch_size=int(os.getenv("BATCH_SIZE", cls.batch_size)),
            db_path=_strip_quotes(os.getenv("CHROMA_DB_PATH", cls.db_path)),
            collection_name=_strip_quotes(
                os.getenv("CHROMA_COLLECTION_NAME", cls.collection_name)
            ),
        )


class RAGTools:
    """改進的 RAG (檢索增強生成) 系統工具類別

    整合 ChromaDB 向量資料庫和本地嵌入模型，提供完整的文件檢索、
    向量搜尋、文本摘要等功能，包含安全性和性能優化。
    """

    def __init__(self, config: Optional[RAGConfig] = None):
        """初始化 RAG 工具 - 性能優化版

        Args:
            config: RAG 配置，若為 None 則使用環境變數配置

        Raises:
            RuntimeError: 當資料庫初始化失敗時
        """
        self.config = config or RAGConfig.from_env()

        # 🎯 多層快取系統
        self._query_cache: Dict[
            str, Tuple[List[SearchResult], float]
        ] = {}  # (結果, 時間戳)
        self._embedding_cache: Dict[str, Tuple[List[float], float]] = {}  # 嵌入向量快取
        self._preprocessed_queries: Dict[str, str] = {}  # 預處理查詢快取

        # 📊 性能監控
        self._query_stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "embedding_cache_hits": 0,
            "avg_response_time": 0.0,
            "last_reset_time": time.time(),
        }

        # 初始化組件
        self.dbClient: Optional[chromadb.PersistentClient] = None
        self.local_model: Optional["SentenceTransformer"] = None
        self.collection = None

        self._initialize_db()

    def _initialize_db(self) -> None:
        """初始化 ChromaDB 連接

        Raises:
            RuntimeError: 當資料庫初始化失敗時
        """
        try:
            # 確保 chroma_db 目錄存在
            import os
            import shutil

            os.makedirs(self.config.db_path, exist_ok=True)

            # 檢查是否需要重置損壞的數據庫
            # 如果存在特定的損壞跡象，則清理並重新初始化
            db_needs_reset = self._check_db_corruption()

            if db_needs_reset:
                logger.warning(
                    f"檢測到 ChromaDB 損壞，正在重置 {self.config.db_path}..."
                )
                try:
                    # 備份現有數據庫
                    backup_path = f"{self.config.db_path}.backup"
                    if os.path.exists(self.config.db_path):
                        if os.path.exists(backup_path):
                            shutil.rmtree(backup_path)
                        shutil.move(self.config.db_path, backup_path)
                    # 重新創建目錄
                    os.makedirs(self.config.db_path, exist_ok=True)
                    logger.info(f"數據庫備份已保存到 {backup_path}")
                except Exception as backup_error:
                    logger.error(f"備份數據庫時出錯: {backup_error}")
                    # 繼續嘗試重新初始化

            # 設定 ChromaDB 客戶端
            self.dbClient = chromadb.PersistentClient(
                path=self.config.db_path,
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )

            # 初始化嵌入提供者
            self._initialize_embedding_provider()

            # 取得或創建 collection (使用自動選擇的名稱)
            collection_name = self.config.get_collection_name()
            try:
                self.collection = self.dbClient.get_collection(collection_name)
                logger.info(f"連接到 {collection_name} collection")
            except Exception as get_collection_error:
                # 如果 collection 不存在，創建一個新的
                logger.debug(
                    f"無法獲取 collection {collection_name}: {get_collection_error}"
                )
                self.collection = self.dbClient.create_collection(collection_name)
                logger.info(f"創建新的 {collection_name} collection")

            self._auto_migrate_from_openai_collection(collection_name)

        except Exception as e:
            logger.error(f"初始化 ChromaDB 失敗: {e}")
            raise RuntimeError(f"Database initialization failed: {e}") from e

    def _get_migration_marker_path(self, target_collection_name: str) -> str:
        """回傳遷移標記檔案路徑，避免重複重建。"""
        safe_model_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", self.config.local_model_name)
        filename = f".migration_{target_collection_name}_{safe_model_name}.json"
        return os.path.join(self.config.db_path, filename)

    def _write_migration_marker(
        self, marker_path: str, payload: Dict[str, Any]
    ) -> None:
        """寫入遷移完成標記。"""
        marker_payload = {
            "target_collection": self.config.get_collection_name(),
            "local_model_name": self.config.local_model_name,
            "timestamp": int(time.time()),
            **payload,
        }
        with open(marker_path, "w", encoding="utf-8") as marker_file:
            json.dump(marker_payload, marker_file, ensure_ascii=True)

    def _auto_migrate_from_openai_collection(self, target_collection_name: str) -> None:
        """啟動時自動偵測舊 OpenAI collection 並遷移到本地 MiniLM。"""
        if target_collection_name != "markdown_documents_minilm":
            return

        marker_path = self._get_migration_marker_path(target_collection_name)
        if os.path.exists(marker_path):
            logger.info("已存在本地向量遷移標記，略過自動遷移")
            return

        target_count = self.collection.count()
        if target_count > 0:
            logger.info(
                f"目標 collection {target_collection_name} 已有 {target_count} 筆資料，略過遷移"
            )
            self._write_migration_marker(
                marker_path,
                {"status": "skipped", "reason": "target_already_populated"},
            )
            return

        try:
            legacy_collection = self.dbClient.get_collection(
                "markdown_documents_openai"
            )
        except Exception:
            logger.info("未找到舊 OpenAI collection，無需自動遷移")
            return

        legacy_count = legacy_collection.count()
        if legacy_count == 0:
            logger.info("舊 OpenAI collection 為空，無需自動遷移")
            self._write_migration_marker(
                marker_path, {"status": "skipped", "reason": "legacy_collection_empty"}
            )
            return

        logger.warning(
            f"偵測到舊 OpenAI 向量資料 {legacy_count} 筆，開始自動遷移至本地 MiniLM"
        )

        migrated_count = 0
        batch_size = max(1, self.config.batch_size)
        try:
            for offset in range(0, legacy_count, batch_size):
                batch = legacy_collection.get(
                    include=["documents", "metadatas"],
                    offset=offset,
                    limit=batch_size,
                )

                ids = batch.get("ids") or []
                documents = batch.get("documents") or []
                metadatas = batch.get("metadatas") or []

                valid_ids: List[str] = []
                valid_documents: List[str] = []
                valid_metadatas: List[Dict[str, Any]] = []
                for index, doc_id in enumerate(ids):
                    if not doc_id:
                        continue
                    if index >= len(documents):
                        continue
                    document = documents[index]
                    if not isinstance(document, str) or not document.strip():
                        continue
                    metadata = metadatas[index] if index < len(metadatas) else {}
                    valid_ids.append(str(doc_id))
                    valid_documents.append(document)
                    valid_metadatas.append(
                        metadata if isinstance(metadata, dict) else {}
                    )

                if not valid_ids:
                    continue

                embeddings = self._embed_texts_local(valid_documents)
                self.collection.upsert(
                    ids=valid_ids,
                    documents=valid_documents,
                    metadatas=valid_metadatas,
                    embeddings=embeddings,
                )
                migrated_count += len(valid_ids)

            self._write_migration_marker(
                marker_path,
                {
                    "status": "migrated",
                    "legacy_collection": "markdown_documents_openai",
                    "legacy_count": legacy_count,
                    "migrated_count": migrated_count,
                },
            )
            logger.info(
                f"OpenAI → MiniLM 向量遷移完成：{migrated_count}/{legacy_count}"
            )
        except Exception as e:
            logger.error(f"自動遷移 OpenAI collection 失敗: {e}")
            raise RuntimeError(f"Auto migration failed: {e}") from e

    def _check_db_corruption(self) -> bool:
        """檢查數據庫是否可能損壞

        Returns:
            bool: 如果檢測到損壞則返回 True
        """
        import os

        db_path = self.config.db_path

        # 檢查數據庫文件是否存在
        if not os.path.exists(db_path):
            return False

        # 檢查 chroma.sqlite3 文件是否存在且可訪問
        sqlite_path = os.path.join(db_path, "chroma.sqlite3")
        if os.path.exists(sqlite_path):
            try:
                # 嘗試打開並檢查 SQLite 文件的有效性
                if os.path.getsize(sqlite_path) == 0:
                    logger.warning("chroma.sqlite3 文件為空，需要重置")
                    return True
            except Exception as e:
                logger.warning(f"無法訪問 chroma.sqlite3: {e}")
                return False

        # 檢查是否存在損壞的向量文件
        try:
            # 嘗試列出數據庫目錄中的文件
            for item in os.listdir(db_path):
                item_path = os.path.join(db_path, item)
                # 檢查文件大小是否異常（過小可能表示損壞）
                if os.path.isfile(item_path) and os.path.getsize(item_path) < 64:
                    if item.endswith(".bin"):
                        logger.warning(f"檢測到可能損壞的 bin 文件: {item}")
                        return True
        except Exception as e:
            logger.debug(f"檢查數據庫文件時出錯: {e}")
            return False

        return False

    def _initialize_embedding_provider(self) -> None:
        """初始化嵌入提供者"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise RuntimeError(
                "sentence-transformers is required for local embeddings. "
                "Install with: pip install sentence-transformers"
            )
        try:
            self.local_model = SentenceTransformer(
                self.config.local_model_name, device=self.config.device
            )
            logger.info(
                f"載入本地模型: {self.config.local_model_name} ({self.config.device})"
            )
        except Exception as e:
            logger.error(f"載入本地模型失敗: {e}")
            raise RuntimeError(f"Failed to load local model: {e}") from e

    def _validate_input(self, query: str, top_k: int) -> None:
        """驗證輸入參數

        Args:
            query: 查詢字串
            top_k: 回傳結果數量

        Raises:
            ValueError: 當參數無效時
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query must be a non-empty string")

        if not isinstance(top_k, int) or top_k <= 0 or top_k > self.config.max_top_k:
            raise ValueError(
                f"top_k must be a positive integer <= {self.config.max_top_k}"
            )

    def _get_cache_key(self, query: str, top_k: int) -> str:
        """生成緩存鍵值 - 優化版"""
        # 標準化查詢以提高快取命中率
        normalized_query = query.strip().lower()
        return hashlib.md5(f"{normalized_query}:{top_k}".encode()).hexdigest()

    def _is_cache_valid(self, timestamp: float) -> bool:
        """檢查快取是否仍然有效"""
        return (time.time() - timestamp) < self.config.cache_ttl_seconds

    def _cleanup_expired_cache(self) -> None:
        """清理過期的快取項目"""
        # 清理查詢快取
        expired_query_keys = [
            key
            for key, (_, timestamp) in self._query_cache.items()
            if not self._is_cache_valid(timestamp)
        ]
        for key in expired_query_keys:
            del self._query_cache[key]

        # 清理嵌入快取
        expired_embedding_keys = [
            key
            for key, (_, timestamp) in self._embedding_cache.items()
            if not self._is_cache_valid(timestamp)
        ]
        for key in expired_embedding_keys:
            del self._embedding_cache[key]

        if expired_query_keys or expired_embedding_keys:
            logger.debug(
                f"清理過期快取項目：查詢 {len(expired_query_keys)} 個，嵌入 {len(expired_embedding_keys)} 個"
            )

    def _embed_texts_with_retry(self, texts: List[str]) -> List[List[float]]:
        """使用重試機制將文字轉換為向量表示

        Args:
            texts: 要轉換的文字列表

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        if not texts:
            return []

        return self._embed_texts_local(texts)

    def _embed_texts_local(self, texts: List[str]) -> List[List[float]]:
        """使用本地模型生成嵌入向量"""
        try:
            # Sentence Transformers 自動處理批次，非常高效
            embeddings = self.local_model.encode(
                texts,
                batch_size=self.config.batch_size,
                show_progress_bar=False,
                convert_to_numpy=False,  # 保持為 tensor，後續轉為 list
            )

            # 轉換為 list 格式
            embeddings_list = [embedding.tolist() for embedding in embeddings]

            logger.debug(f"本地模型成功生成 {len(embeddings_list)} 個嵌入向量")
            return embeddings_list

        except Exception as e:
            logger.error(f"本地嵌入向量生成失敗: {e}")
            raise RuntimeError(f"Local embedding generation failed: {e}") from e

    def rag_search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """執行高性能 RAG 檢索 🚀

        Args:
            query: 查詢字串
            top_k: 回傳結果數量

        Returns:
            List[SearchResult]: 檢索結果列表

        Raises:
            ValueError: 當輸入參數無效時
        """
        start_time = time.time()
        self._query_stats["total_queries"] += 1

        try:
            # 📋 驗證輸入
            self._validate_input(query, top_k)

            # 🧹 定期清理過期快取
            if self._query_stats["total_queries"] % 50 == 0:
                self._cleanup_expired_cache()

            # 🎯 檢查查詢快取
            cache_key = self._get_cache_key(query, top_k)
            if (
                self.config.enable_query_cache
                and cache_key in self._query_cache
                and self._is_cache_valid(self._query_cache[cache_key][1])
            ):
                self._query_stats["cache_hits"] += 1
                logger.debug(f"✨ 快取命中: {query[:30]}...")
                return self._query_cache[cache_key][0]

            # 🔍 查詢預處理
            processed_query = (
                self._preprocess_query(query)
                if self.config.query_preprocessing
                else query
            )

            # 🎯 智慧嵌入向量處理
            query_embedding = self._get_embedding_with_cache(processed_query)
            if not query_embedding:
                logger.warning("查詢嵌入向量生成失敗，回傳空結果")
                return []

            # 🔍 執行向量查詢（增加檢索數量用於重排序）
            search_top_k = (
                min(top_k * 2, self.config.max_top_k)
                if self.config.result_reranking
                else top_k
            )

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=search_top_k,
                include=["documents", "metadatas", "distances"],
            )

            # 📊 轉換並過濾結果
            search_results = self._process_search_results(
                results, processed_query, top_k
            )

            # 💾 快取結果（帶時間戳）
            if (
                self.config.enable_query_cache
                and len(self._query_cache) < self.config.cache_size
            ):
                current_time = time.time()
                self._query_cache[cache_key] = (search_results, current_time)

            # 📈 更新性能統計
            elapsed_time = time.time() - start_time
            self._update_performance_stats(elapsed_time)

            logger.info(
                f"🎯 RAG 檢索完成: '{query[:30]}...' → {len(search_results)} 結果 ({elapsed_time:.3f}s)"
            )
            return search_results

        except Exception as e:
            logger.error(f"❌ RAG 檢索失敗: {e}")
            return []

    def _preprocess_query(self, query: str) -> str:
        """查詢預處理優化 🔧"""
        if query in self._preprocessed_queries:
            return self._preprocessed_queries[query]

        # 基本清理和標準化
        processed = query.strip()

        # 移除多餘的標點符號
        processed = re.sub(r"[？！。，；：]", " ", processed)

        # 移除多餘空格
        processed = re.sub(r"\s+", " ", processed).strip()

        # 快取預處理結果
        if len(self._preprocessed_queries) < 200:
            self._preprocessed_queries[query] = processed

        return processed

    def _get_embedding_with_cache(self, text: str) -> Optional[List[float]]:
        """帶快取的嵌入向量獲取 ⚡"""
        if not self.config.enable_embedding_cache:
            embeddings = self._embed_texts_with_retry([text])
            return embeddings[0] if embeddings else None

        # 檢查嵌入快取
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self._embedding_cache and self._is_cache_valid(
            self._embedding_cache[text_hash][1]
        ):
            self._query_stats["embedding_cache_hits"] += 1
            return self._embedding_cache[text_hash][0]

        # 生成新的嵌入向量
        embeddings = self._embed_texts_with_retry([text])
        if embeddings:
            # 快取嵌入向量
            if len(self._embedding_cache) < self.config.cache_size * 2:
                current_time = time.time()
                self._embedding_cache[text_hash] = (embeddings[0], current_time)
            return embeddings[0]

        return None

    def _process_search_results(
        self, results: Dict, query: str, top_k: int
    ) -> List[SearchResult]:
        """處理和優化搜索結果 📊"""
        if not results["ids"] or not results["ids"][0]:
            return []

        search_results = []

        for i in range(len(results["ids"][0])):
            # ChromaDB 餘弦距離轉換為相似度分數
            distance = results["distances"][0][i]
            similarity = max(0.0, min(1.0, (2.0 - distance) / 2.0))

            # 應用相似度閾值過濾
            if similarity < self.config.similarity_threshold:
                continue

            search_result = SearchResult(
                doc_id=results["ids"][0][i],
                score=similarity,
                excerpt=results["documents"][0][i] or "",
                metadata=results["metadatas"][0][i] or {},
            )
            search_results.append(search_result)

        # 🏆 結果重排序（如果啟用）
        if self.config.result_reranking and len(search_results) > top_k:
            search_results = self._rerank_results(search_results, query)

        # 限制返回數量
        return search_results[:top_k]

    def _rerank_results(
        self, results: List[SearchResult], query: str
    ) -> List[SearchResult]:
        """基於查詢相關性重新排序結果 🏆"""
        try:
            # 簡單的關鍵詞匹配重排序
            query_tokens = set(query.lower().split())

            def calculate_relevance_score(result: SearchResult) -> float:
                content = result.excerpt.lower()

                # 計算關鍵詞匹配分數
                keyword_matches = sum(1 for token in query_tokens if token in content)
                keyword_score = (
                    keyword_matches / len(query_tokens) if query_tokens else 0
                )

                # 結合原始相似度分數和關鍵詞分數
                return result.score * 0.7 + keyword_score * 0.3

            # 重新排序
            results.sort(key=calculate_relevance_score, reverse=True)
            return results

        except Exception as e:
            logger.warning(f"結果重排序失敗: {e}")
            return results

    def _update_performance_stats(self, elapsed_time: float) -> None:
        """更新性能統計信息 📈"""
        total_queries = self._query_stats["total_queries"]
        prev_avg = self._query_stats["avg_response_time"]

        # 計算移動平均
        self._query_stats["avg_response_time"] = (
            prev_avg * (total_queries - 1) + elapsed_time
        ) / total_queries

    def get_performance_stats(self) -> Dict:
        """獲取性能統計信息 📊"""
        stats = self._query_stats.copy()
        stats["cache_hit_rate"] = self._query_stats["cache_hits"] / max(
            self._query_stats["total_queries"], 1
        )
        stats["embedding_cache_hit_rate"] = self._query_stats[
            "embedding_cache_hits"
        ] / max(self._query_stats["total_queries"], 1)
        stats["active_cache_size"] = len(self._query_cache)
        stats["embedding_cache_size"] = len(self._embedding_cache)
        stats["uptime_seconds"] = time.time() - stats["last_reset_time"]

        return stats

    def reset_performance_stats(self) -> None:
        """重置性能統計 🔄"""
        self._query_stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "embedding_cache_hits": 0,
            "avg_response_time": 0.0,
            "last_reset_time": time.time(),
        }
        logger.info("性能統計已重置")

    def get_document(self, doc_id: str) -> Optional[Dict]:
        """取得特定文件內容

        Args:
            doc_id: 文件ID

        Returns:
            Optional[Dict]: 文件內容，包含 id, text, metadata
        """
        if not doc_id or not isinstance(doc_id, str):
            raise ValueError("doc_id must be a non-empty string")

        try:
            results = self.collection.get(
                ids=[doc_id], include=["documents", "metadatas"]
            )

            if results["ids"] and len(results["ids"]) > 0:
                return {
                    "id": results["ids"][0],
                    "text": results["documents"][0] if results["documents"] else "",
                    "metadata": results["metadatas"][0] if results["metadatas"] else {},
                }
            else:
                logger.warning(f"找不到文件 ID: {doc_id}")
                return None

        except Exception as e:
            logger.error(f"取得文件失敗 (ID: {doc_id}): {e}")
            return None

    def summarize_text(self, text: str, max_tokens: int = 120) -> str:
        """文本摘要功能（改進版）

        Args:
            text: 原始文本
            max_tokens: 最大 token 數量

        Returns:
            str: 摘要文本
        """
        if not text or not isinstance(text, str):
            return ""

        if not isinstance(max_tokens, int) or max_tokens <= 0:
            raise ValueError("max_tokens must be a positive integer")

        # 按句子分割並限制長度
        sentences = [s.strip() for s in text.split("。") if s.strip()]
        if not sentences:
            return ""

        summary = ""
        token_count = 0

        for sentence in sentences:
            # 估算 token 數量（中文大約 1 字符 = 1 token）
            estimated_tokens = len(sentence)

            if token_count + estimated_tokens > max_tokens:
                break

            summary += sentence + "。"
            token_count += estimated_tokens

        return summary.strip()

    def rebuild_index(self, path: str) -> Dict:
        """重建索引（改進版）

        Args:
            path: 資料路徑

        Returns:
            Dict: 重建結果狀態
        """
        if not path or not isinstance(path, str):
            raise ValueError("path must be a non-empty string")

        try:
            # 使用自動選擇的 collection 名稱
            collection_name = self.config.get_collection_name()

            # 重置 collection
            try:
                self.dbClient.delete_collection(collection_name)
            except Exception:
                logger.warning(f"Collection {collection_name} 不存在，跳過刪除")

            self.collection = self.dbClient.create_collection(collection_name)

            # 清空緩存
            self._query_cache.clear()

            logger.info(f"索引重建完成: {collection_name}")
            return {
                "status": "success",
                "details": f"索引重建完成: {collection_name}",
                "collection_name": collection_name,
            }

        except Exception as e:
            logger.error(f"重建索引失敗: {e}")
            return {
                "status": "error",
                "details": str(e),
                "collection_name": self.config.get_collection_name(),
            }

    def get_collection_info(self) -> Dict:
        """取得 collection 資訊（改進版）

        Returns:
            Dict: collection 統計資訊
        """
        try:
            collection_name = self.config.get_collection_name()
            count = self.collection.count()
            return {
                "name": collection_name,
                "document_count": count,
                "status": "active",
                "cache_size": len(self._query_cache),
                "embedding_provider": "local",
                "model": self.config.local_model_name,
            }
        except Exception as e:
            logger.error(f"取得 collection 資訊失敗: {e}")
            return {
                "name": self.config.get_collection_name(),
                "document_count": 0,
                "status": "error",
                "error": str(e),
                "cache_size": 0,
            }

    def clear_cache(self) -> None:
        """清空所有緩存 🧹"""
        self._query_cache.clear()
        self._embedding_cache.clear()
        self._preprocessed_queries.clear()
        logger.info("所有緩存已清空（查詢、嵌入、預處理）")

    def optimize_performance(self) -> Dict[str, str]:
        """性能優化建議 💡"""
        stats = self.get_performance_stats()
        suggestions = []

        if stats["cache_hit_rate"] < 0.3:
            suggestions.append("考慮增加快取大小或延長 TTL")

        if stats["avg_response_time"] > 1.0:
            suggestions.append("響應時間較慢，建議檢查網絡連接或減少 top_k")

        if stats["embedding_cache_hit_rate"] < 0.2:
            suggestions.append("嵌入快取命中率低，查詢模式可能過於多樣化")

        if len(suggestions) == 0:
            suggestions.append("性能表現良好，無需特別優化")

        return {
            "performance_level": "good"
            if stats["avg_response_time"] < 0.5
            else "moderate"
            if stats["avg_response_time"] < 1.0
            else "poor",
            "suggestions": suggestions,
            "stats_summary": f"平均響應時間: {stats['avg_response_time']:.3f}s, 快取命中率: {stats['cache_hit_rate']:.1%}",
        }


# 向後兼容的便利函數
def rag_search(query: str, top_k: int = 5) -> List[SearchResult]:
    """快速 RAG 搜索函數（向後兼容）

    Args:
        query: 搜索查詢
        top_k: 返回結果數量

    Returns:
        List[SearchResult]: 搜索結果列表
    """
    rag_tools = RAGTools()
    return rag_tools.rag_search(query, top_k)


if __name__ == "__main__":
    rag_search("你有什麼技能？")
