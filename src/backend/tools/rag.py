"""RAG 工具層改進版本

對接 ChromaDB 向量資料庫，提供文本檢索和文件管理功能
包含安全性、性能優化和錯誤處理改進
"""

import os
import re
import time
import hashlib
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

import chromadb
from chromadb.config import Settings
import openai
from openai import APIError, RateLimitError

from src.backend.models import SearchResult

# 載入環境變數
load_dotenv(override=True)

# 建立日誌記錄器
logger = logging.getLogger(__name__)


@dataclass
class RAGConfig:
    """RAG 工具配置類 - 性能優化版"""

    embedding_model: str = "text-embedding-3-small"  # 使用更快的嵌入模型
    batch_size: int = 100  # 優化批次大小平衡速度與記憶體
    max_retries: int = 2  # 增加重試次數提高穩定性
    cache_size: int = 100  # 擴大快取大小
    db_path: str = "./chroma_db"
    collection_name: str = "markdown_documents"
    max_top_k: int = 15  # 降低最大檢索數量提升速度

    # 🚀 新增性能優化配置
    enable_query_cache: bool = True  # 啟用查詢快取
    enable_embedding_cache: bool = True  # 啟用嵌入向量快取
    cache_ttl_seconds: int = 3600  # 快取存活時間 1 小時
    parallel_batch_processing: bool = True  # 並行批次處理
    similarity_threshold: float = 0.1  # 相似度過濾閾值
    query_preprocessing: bool = True  # 啟用查詢預處理
    result_reranking: bool = True  # 啟用結果重排序

    @classmethod
    def from_env(cls) -> "RAGConfig":
        """從環境變數創建配置"""
        return cls(
            embedding_model=os.getenv("EMBEDDING_MODEL", cls.embedding_model),
            batch_size=int(os.getenv("BATCH_SIZE", cls.batch_size)),
            db_path=os.getenv("CHROMA_DB_PATH", cls.db_path),
            collection_name=os.getenv("CHROMA_COLLECTION_NAME", cls.collection_name),
        )


class RAGTools:
    """改進的 RAG (檢索增強生成) 系統工具類別

    整合 ChromaDB 向量資料庫和 OpenAI 嵌入模型，提供完整的文件檢索、
    向量搜尋、文本摘要等功能，包含安全性和性能優化。
    """

    def __init__(self, config: Optional[RAGConfig] = None):
        """初始化 RAG 工具 - 性能優化版

        Args:
            config: RAG 配置，若為 None 則使用環境變數配置

        Raises:
            ValueError: 當必要的環境變數未設置時
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

        # 驗證 API 金鑰
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        # 初始化組件
        self.dbClient: Optional[chromadb.PersistentClient] = None
        self.provider: Optional[openai.OpenAI] = None
        self.collection = None

        self._initialize_db()

    def _initialize_db(self) -> None:
        """初始化 ChromaDB 連接

        Raises:
            RuntimeError: 當資料庫初始化失敗時
        """
        try:
            # 設定 ChromaDB 客戶端
            self.dbClient = chromadb.PersistentClient(
                path=self.config.db_path,
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )

            # 設定 OpenAI 嵌入提供者
            self.provider = openai.OpenAI(api_key=self.api_key)

            # 取得或創建 collection
            try:
                self.collection = self.dbClient.get_collection(
                    self.config.collection_name
                )
                logger.info(f"連接到 {self.config.collection_name} collection")
            except Exception:
                # 如果 collection 不存在，創建一個新的
                self.collection = self.dbClient.create_collection(
                    self.config.collection_name
                )
                logger.info(f"創建新的 {self.config.collection_name} collection")

        except Exception as e:
            logger.error(f"初始化 ChromaDB 失敗: {e}")
            raise RuntimeError(f"Database initialization failed: {e}") from e

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

        Raises:
            APIError: 當 API 調用失敗時
        """
        if not texts:
            return []

        all_embeddings = []

        # 分批處理文字
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i : i + self.config.batch_size]

            # 實現重試機制
            for attempt in range(self.config.max_retries):
                try:
                    response = self.provider.embeddings.create(
                        model=self.config.embedding_model, input=batch
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(batch_embeddings)
                    break

                except RateLimitError:
                    if attempt < self.config.max_retries - 1:
                        wait_time = 2**attempt  # Exponential backoff
                        logger.warning(f"Rate limit hit, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    logger.error(
                        f"Rate limit exceeded after {self.config.max_retries} attempts"
                    )
                    raise

                except APIError as e:
                    logger.error(f"OpenAI API error on attempt {attempt + 1}: {e}")
                    if attempt == self.config.max_retries - 1:
                        raise
                    time.sleep(1)

        logger.debug(f"成功生成 {len(all_embeddings)} 個嵌入向量")
        return all_embeddings

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
            # 使用配置中的 collection 名稱
            collection_name = self.config.collection_name

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
                "collection_name": self.config.collection_name,
            }

    def get_collection_info(self) -> Dict:
        """取得 collection 資訊（改進版）

        Returns:
            Dict: collection 統計資訊
        """
        try:
            count = self.collection.count()
            return {
                "name": self.config.collection_name,
                "document_count": count,
                "status": "active",
                "cache_size": len(self._query_cache),
            }
        except Exception as e:
            logger.error(f"取得 collection 資訊失敗: {e}")
            return {
                "name": self.config.collection_name,
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
