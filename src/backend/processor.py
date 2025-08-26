"""ResumeMate 主要處理邏輯

協調 Analysis Agent 和 Evaluate Agent 的互動
"""

import logging
from backend.models import Question, SystemResponse, AgentDecision
from backend.agents import AnalysisAgent, EvaluateAgent
from backend.tools import RAGTools

logger = logging.getLogger(__name__)


class ResumeMateProcessor:
    """ResumeMate 主處理器"""

    def __init__(self, db_path: str = "chroma_db"):
        """初始化處理器

        Args:
            db_path: ChromaDB 資料庫路徑
        """
        self.rag_tools = RAGTools(db_path)

        # Try to create an OpenAI Agents adapter if the SDK is available.
        self.openai_adapter = None
        try:
            from backend.agents.openai_adapter import OpenAIAgentsAdapter

            self.openai_adapter = OpenAIAgentsAdapter(self.rag_tools)
        except Exception:
            self.openai_adapter = None

        # Local in-repo agents (fallback)
        self.analysis_agent = AnalysisAgent(self.rag_tools)
        self.evaluate_agent = EvaluateAgent()

    async def process_question(self, question: Question) -> SystemResponse:
        """主要處理流程，協調不同代理人的互動

        Args:
            question: 使用者問題

        Returns:
            SystemResponse: 系統回應
        """
        logger.info(f"開始處理問題: {question.text}")
        try:
            # 如果有可用的 OpenAI Agents adapter，優先走 SDK 路徑
            if getattr(self, "openai_adapter", None) and getattr(
                self.openai_adapter, "available", False
            ):
                # 使用 adapter 執行整個 agent 流程，並將 SDK 結果轉譯為 SystemResponse
                sdk_result = await self.openai_adapter.run(question.text)

                # 嘗試從 SDK 結果抽取 final output 與來源資訊
                final_output = getattr(sdk_result, "final_output", None)
                # final_output 可能是字串或結構化物件；若為字串則直接使用
                if isinstance(final_output, str):
                    return SystemResponse(
                        answer=final_output,
                        sources=[],
                        confidence=0.9,
                        metadata={"sdk_result": True},
                    )

                # 若 final_output 有屬性可以取用（例如 dict 形式），嘗試解析
                try:
                    out = dict(final_output)
                    answer = out.get("answer") or out.get("text") or str(out)
                    sources = out.get("sources") or out.get("source_ids") or []
                    confidence = out.get("confidence", 0.0)
                    return SystemResponse(
                        answer=answer,
                        sources=sources,
                        confidence=float(confidence),
                        metadata={"sdk_result": True},
                    )
                except Exception:
                    # 若無法解析，回退到內部流程
                    pass

            # Analysis Agent - 本地實作（fallback）
            analysis = await self.analysis_agent.analyze(question)

            # 處理超出範圍的問題
            if analysis.decision == AgentDecision.OUT_OF_SCOPE:
                evaluation = await self.evaluate_agent.evaluate(analysis)
                return self._format_system_response(evaluation)

            # 處理需要澄清的問題
            if analysis.decision == AgentDecision.ASK_CLARIFY:
                evaluation = await self.evaluate_agent.evaluate(analysis)
                return self._format_system_response(evaluation)

            # Evaluate Agent - 本地實作
            evaluation = await self.evaluate_agent.evaluate(analysis)

            # 如果需要編輯，讓 Analysis Agent 修正
            if evaluation.status == AgentDecision.NEEDS_EDIT:
                revised_analysis = await self.analysis_agent.revise(
                    analysis, evaluation.suggestions or []
                )
                evaluation = await self.evaluate_agent.evaluate(revised_analysis)

            # 格式化最終回應
            return self._format_system_response(evaluation)

        except Exception as e:
            logger.error(f"處理問題時發生錯誤: {e}")
            return SystemResponse(
                answer="抱歉，系統處理您的問題時發生錯誤，請稍後再試。",
                sources=[],
                confidence=0.0,
                metadata={"error": str(e)},
            )

    def _format_system_response(self, evaluation) -> SystemResponse:
        """格式化系統回應

        Args:
            evaluation: 評估結果

        Returns:
            SystemResponse: 格式化的系統回應
        """
        # 根據狀態決定是否需要特殊動作
        action = None
        if evaluation.status == AgentDecision.OUT_OF_SCOPE:
            action = "suggest_contact"
        elif evaluation.status == AgentDecision.ASK_CLARIFY:
            action = "request_clarification"

        return SystemResponse(
            answer=evaluation.final_answer,
            sources=evaluation.sources,
            confidence=evaluation.confidence,
            action=action,
            metadata=evaluation.metadata,
        )

    def get_system_info(self) -> dict:
        """取得系統資訊

        Returns:
            dict: 系統狀態資訊
        """
        collection_info = self.rag_tools.get_collection_info()

        return {
            "status": "active",
            "version": "0.1.0",
            "database": collection_info,
            "agents": {"analysis": "active", "evaluate": "active"},
        }
