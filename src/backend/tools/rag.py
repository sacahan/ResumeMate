"""RAG 工具層改進版本

對接 ChromaDB 向量資料庫，提供文本檢索和文件管理功能
包含安全性、性能優化和錯誤處理改進
"""

import os
import time
import hashlib
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional
from dotenv import load_dotenv

import chromadb
from chromadb.config import Settings
import openai
from openai import APIError, RateLimitError

from backend.models import SearchResult

# 載入環境變數
load_dotenv(override=True)

# 建立日誌記錄器
logger = logging.getLogger(__name__)


@dataclass
class RAGConfig:
    """RAG 工具配置類"""

    embedding_model: str = "text-embedding-3-small"
    batch_size: int = 1000
    max_retries: int = 1
    cache_size: int = 50
    db_path: str = "./chroma_db"
    collection_name: str = "markdown_documents"
    max_top_k: int = 20

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
        """初始化 RAG 工具

        Args:
            config: RAG 配置，若為 None 則使用環境變數配置

        Raises:
            ValueError: 當必要的環境變數未設置時
            RuntimeError: 當資料庫初始化失敗時
        """
        self.config = config or RAGConfig.from_env()
        self._query_cache: Dict[str, List[SearchResult]] = {}

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
        """生成緩存鍵值"""
        return hashlib.md5(f"{query}:{top_k}".encode()).hexdigest()

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
        """執行 RAG 檢索（帶緩存和驗證）

        Args:
            query: 查詢字串
            top_k: 回傳結果數量

        Returns:
            List[SearchResult]: 檢索結果列表

        Raises:
            ValueError: 當輸入參數無效時
        """
        # 驗證輸入
        self._validate_input(query, top_k)

        # 檢查緩存
        cache_key = self._get_cache_key(query, top_k)
        if cache_key in self._query_cache:
            logger.debug(f"從緩存返回查詢結果: {query}")
            return self._query_cache[cache_key]

        try:
            # 將查詢字串轉為向量
            query_embedding = self._embed_texts_with_retry([query])
            if not query_embedding:
                logger.warning("查詢嵌入向量生成失敗，回傳空結果")
                return []

            # 執行向量查詢
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )

            # 轉換結果為 SearchResult 模型
            search_results = []

            if not results["ids"] or not results["ids"][0]:
                return []

            for i in range(len(results["ids"][0])):
                # ChromaDB 餘弦距離轉換為相似度分數
                distance = results["distances"][0][i]
                similarity = max(0.0, min(1.0, (2.0 - distance) / 2.0))

                search_result = SearchResult(
                    doc_id=results["ids"][0][i],
                    score=similarity,
                    excerpt=results["documents"][0][i] or "",
                    metadata=results["metadatas"][0][i] or {},
                )
                search_results.append(search_result)

            # 緩存結果
            if len(self._query_cache) < self.config.cache_size:
                self._query_cache[cache_key] = search_results

            logger.info(
                f"RAG 檢索完成，查詢: '{query[:50]}...'，回傳 {len(search_results)} 個結果"
            )
            return search_results

        except Exception as e:
            logger.error(f"RAG 檢索失敗: {e}")
            return []

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
        """清空查詢緩存"""
        self._query_cache.clear()
        logger.info("查詢緩存已清空")


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
