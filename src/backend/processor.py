"""ResumeMate 主要處理邏輯

協調 Analysis Agent 和 Evaluate Agent 的互動，使用 OpenAI Agents SDK 標準實現
"""

import logging
from typing import Any, Dict, List

from backend.models import Question, SystemResponse
from backend.tools.rag import RAGTools  # ← 修正可能的匯入路徑
from backend.agents import AnalysisAgent, EvaluateAgent

logger = logging.getLogger(__name__)


class ResumeMateProcessor:
    """ResumeMate 主處理器"""

    def __init__(self):
        """初始化處理器

        Args:
            db_path: ChromaDB 資料庫路徑
        """

        self.rag_tools = RAGTools()
        self.analysis_agent = AnalysisAgent()
        self.evaluate_agent = EvaluateAgent()
        logger.info("初始化 ResumeMate 處理器完成")

    async def process_question(self, question: Question) -> SystemResponse:
        """主要處理流程，協調不同代理人的互動"""
        logger.info(f"開始處理問題: {question.text}")
        try:
            # 1) Analysis
            analysis = await self.analysis_agent.analyze(question)

            # 1.1 回填 sources（reviewer 需要可靠來源以評分）
            analysis.metadata = analysis.metadata or {}
            analysis.metadata.setdefault("sources", self._ensure_sources(analysis))

            # 2) Evaluate（不分支，統一交給 reviewer 做最終裁決）
            evaluation = await self.evaluate_agent.evaluate(analysis)

            # 3) 格式化最終回覆
            final_answer = self._format_system_response(evaluation)
            logger.info(f"最終回覆: {final_answer}")
            return final_answer

        except Exception as e:
            logger.error(f"處理問題時發生錯誤: {e}")
            return SystemResponse(
                answer="抱歉，處理您的問題時發生錯誤，請稍後再試。",
                sources=[],
                confidence=0.0,
                metadata={"error": str(e)},
            )

    # --------- 工具：把 retrievals/metadata 轉為 reviewer 可用的 sources ----------
    def _ensure_sources(self, analysis) -> List[Dict[str, Any]]:
        sources: List[Dict[str, Any]] = []

        # (A) 從 retrievals 轉成可追溯來源
        try:
            if getattr(analysis, "retrievals", None):
                for r in analysis.retrievals:
                    md = getattr(r, "metadata", {}) or {}
                    sources.append(
                        {
                            "id": getattr(r, "doc_id", getattr(r, "id", None)),
                            "title": md.get("title"),
                            "loc": md.get("loc"),
                            "score": getattr(r, "score", None),
                        }
                    )
        except Exception as e:
            logger.warning(f"轉換 retrievals 為 sources 失敗：{e}")

        # (B) 若 analysis.metadata 已有 sources，合併
        try:
            meta_sources = (analysis.metadata or {}).get("sources", [])
            if isinstance(meta_sources, list):
                # 轉換 sources 為統一格式
                for source in meta_sources:
                    if isinstance(source, str):
                        # 如果是字串 ID，轉為字典格式
                        sources.append(
                            {
                                "id": source,
                                "title": None,
                                "loc": None,
                                "score": 0.8,
                            }
                        )
                    elif isinstance(source, dict):
                        # 如果已經是字典，直接使用
                        sources.append(source)
        except Exception as e:
            logger.warning(f"轉換 metadata sources 失敗：{e}")

        # 去重（以 id+loc）
        seen = set()
        uniq: List[Dict[str, Any]] = []
        for s in sources:
            key = (s.get("id"), s.get("loc"))
            if key in seen:
                continue
            seen.add(key)
            uniq.append(s)

        return uniq[:5]  # 控制上限

    # --------- 產出最終 SystemResponse（含動作建議） ----------
    def _format_system_response(self, evaluation) -> SystemResponse:
        """格式化為系統回應"""
        conf = max(0.0, min(1.0, float(getattr(evaluation, "confidence", 0.0))))

        # 允許不同枚舉/字串；統一歸一化
        status_str = str(getattr(evaluation.status, "value", evaluation.status)).lower()
        action = None

        if status_str in ("needs_clarification", "clarify"):
            action = "請提供更多資訊"
        elif status_str in ("out_of_scope", "oos"):
            # out_of_scope 也應該升級到人工處理
            action = "請填寫聯絡表單"
        elif status_str == "escalate_to_human":
            action = "請填寫聯絡表單"

        return SystemResponse(
            answer=evaluation.final_answer,
            sources=evaluation.sources or [],
            confidence=conf,
            action=action,
            metadata={
                "status": status_str,
                **(evaluation.metadata or {}),
            },
        )

    # --------- 系統資訊 ----------
    def get_system_info(self) -> dict:
        """取得系統資訊"""
        db_info = {"document_count": 0, "status": "unknown"}
        if hasattr(self.rag_tools, "collection") and self.rag_tools.collection:
            try:
                count = self.rag_tools.collection.count()
                db_info["document_count"] = count
                db_info["status"] = "connected" if count > 0 else "empty"
            except Exception as e:
                logger.error(f"獲取數據庫資訊時發生錯誤: {e}")
                db_info["status"] = "error"

        return {"version": "1.0.0", "database": db_info}
