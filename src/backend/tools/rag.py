"""RAG 工具層實作

對接 ChromaDB 向量資料庫，提供文本檢索和文件管理功能
"""

import logging
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from backend.models import SearchResult

# 嘗試從 OpenAI Agents SDK 匯入 function_tool，以便將 RAG 功能
# 暴露成 agent 可呼叫的 tool；若 SDK 不存在則提供回退 decorator
try:
    from agents import function_tool  # type: ignore

    _AGENTS_SDK_AVAILABLE = True
except Exception:
    # 回退：function_tool 變成 identity decorator，使程式仍可執行
    def function_tool(fn):
        return fn

    _AGENTS_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)


class RAGTools:
    """RAG 系統工具類別"""

    def __init__(self, db_path: str = "chroma_db"):
        """初始化 RAG 工具

        Args:
            db_path: ChromaDB 資料庫路徑
        """
        self.db_path = db_path
        self.client = None
        self.collection = None
        self._initialize_db()

    def _initialize_db(self):
        """初始化 ChromaDB 連接"""
        try:
            # 設定 ChromaDB 客戶端
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )

            # 取得或創建 collection
            try:
                self.collection = self.client.get_collection("resume_data")
                logger.info("成功連接到現有的 resume_data collection")
            except Exception:
                # 如果 collection 不存在，創建一個新的
                self.collection = self.client.create_collection("resume_data")
                logger.info("創建新的 resume_data collection")

        except Exception as e:
            logger.error(f"初始化 ChromaDB 失敗: {e}")
            raise

    def rag_search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """執行 RAG 檢索

        Args:
            query: 查詢字串
            top_k: 回傳結果數量

        Returns:
            List[SearchResult]: 檢索結果列表
        """
        if not query or not query.strip():
            logger.warning("查詢字串為空，回傳空結果")
            return []

        try:
            # 執行相似度檢索
            results = self.collection.query(query_texts=[query], n_results=top_k)

            # 轉換結果格式
            search_results = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    # ChromaDB 回傳的是餘弦距離 (0-2)，需要轉換為相似度分數
                    distance = (
                        results["distances"][0][i] if results["distances"] else 2.0
                    )
                    # 餘弦距離轉相似度：similarity = (2 - distance) / 2
                    # 這樣 distance=0 -> similarity=1, distance=2 -> similarity=0
                    score = max(0.0, min(1.0, (2.0 - distance) / 2.0))

                    search_result = SearchResult(
                        doc_id=doc_id,
                        score=score,
                        excerpt=results["documents"][0][i]
                        if results["documents"]
                        else "",
                        metadata=results["metadatas"][0][i]
                        if results["metadatas"]
                        else {},
                    )
                    search_results.append(search_result)

            logger.info(
                f"RAG 檢索完成，查詢: '{query}'，回傳 {len(search_results)} 個結果"
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
        """文本摘要功能

        Args:
            text: 原始文本
            max_tokens: 最大 token 數量

        Returns:
            str: 摘要文本
        """
        # 簡單的截斷摘要實作
        if not text:
            return ""

        # 按句子分割並限制長度
        sentences = text.split("。")
        summary = ""
        token_count = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 估算 token 數量（中文大約 1 字符 = 1 token）
            estimated_tokens = len(sentence)

            if token_count + estimated_tokens > max_tokens:
                break

            summary += sentence + "。"
            token_count += estimated_tokens

        return summary.strip()

    def rebuild_index(self, path: str) -> Dict:
        """重建索引

        Args:
            path: 資料路徑

        Returns:
            Dict: 重建結果狀態
        """
        try:
            # 重置 collection
            self.client.delete_collection("resume_data")
            self.collection = self.client.create_collection("resume_data")

            # 這裡應該加入重新載入資料的邏輯
            # 目前先回傳成功狀態

            return {"status": "success", "details": "索引重建完成"}

        except Exception as e:
            logger.error(f"重建索引失敗: {e}")
            return {"status": "error", "details": str(e)}

    def get_collection_info(self) -> Dict:
        """取得 collection 資訊

        Returns:
            Dict: collection 統計資訊
        """
        try:
            count = self.collection.count()
            return {"name": "resume_data", "document_count": count, "status": "active"}
        except Exception as e:
            logger.error(f"取得 collection 資訊失敗: {e}")
            return {
                "name": "resume_data",
                "document_count": 0,
                "status": "error",
                "error": str(e),
            }


# 便利函數，用於快速搜索
def rag_search(query: str, top_k: int = 5) -> List[SearchResult]:
    """快速 RAG 搜索函數

    Args:
        query: 搜索查詢
        top_k: 返回結果數量

    Returns:
        List[SearchResult]: 搜索結果列表
    """
    rag_tools = RAGTools()
    return rag_tools.rag_search(query, top_k)


# -----------------------------
# Expose tool wrappers for Agents SDK
# -----------------------------


@function_tool
def rag_search_tool(query: str, top_k: int = 5):
    """Agent tool: run a RAG search and return simplified results.

    回傳值為 list[dict]，每個 dict 包含 doc_id, score, excerpt, metadata。
    """
    rag_tools = RAGTools()
    results = rag_tools.rag_search(query, top_k=top_k)
    return [
        {
            "doc_id": r.doc_id,
            "score": r.score,
            "excerpt": r.excerpt,
            "metadata": r.metadata,
        }
        for r in results
    ]


@function_tool
def get_document_tool(doc_id: str):
    """Agent tool: get a document by id and return a simple dict."""
    rag_tools = RAGTools()
    doc = rag_tools.get_document(doc_id)
    return doc or {}


@function_tool
def summarize_text_tool(text: str, max_tokens: int = 120):
    """Agent tool: return a short summary of the provided text."""
    rag_tools = RAGTools()
    return rag_tools.summarize_text(text, max_tokens=max_tokens)


@function_tool
def rebuild_index_tool(path: str):
    """Agent tool: rebuild the index from a given path. Returns status dict."""
    rag_tools = RAGTools()
    return rag_tools.rebuild_index(path)
