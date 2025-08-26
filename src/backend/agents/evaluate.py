"""Evaluate Agent 實作

負責評估 Analysis Agent 的結果，生成最終回答
"""

import logging
from typing import List
from backend.models import AnalysisResult, EvaluationResult, AgentDecision

logger = logging.getLogger(__name__)


class EvaluateAgent:
    """Evaluate Agent - 回答評估與品質控制代理人"""

    def __init__(self):
        """初始化 Evaluate Agent"""
        self.confidence_threshold = 0.3  # 低信心閾值
        self.min_source_support = 0.5  # 最小來源支持度

    async def evaluate(self, analysis: AnalysisResult) -> EvaluationResult:
        """評估分析結果並生成最終回答

        Args:
            analysis: Analysis Agent 的分析結果

        Returns:
            EvaluationResult: 評估結果
        """
        logger.info("開始評估分析結果")

        try:
            # 處理不同的決策類型
            if analysis.decision == AgentDecision.OUT_OF_SCOPE:
                return self._handle_out_of_scope(analysis)

            elif analysis.decision == AgentDecision.ASK_CLARIFY:
                return self._handle_clarification(analysis)

            elif analysis.decision == AgentDecision.RETRIEVE:
                return self._evaluate_retrieval_result(analysis)

            else:
                # 未知決策類型
                return EvaluationResult(
                    final_answer="抱歉，系統發生未知錯誤，請稍後再試。",
                    sources=[],
                    confidence=0.0,
                    status=AgentDecision.OUT_OF_SCOPE,
                    metadata={"error": "未知決策類型"},
                )

        except Exception as e:
            logger.error(f"評估過程中發生錯誤: {e}")
            return EvaluationResult(
                final_answer="抱歉，系統處理您的問題時發生錯誤，請稍後再試。",
                sources=[],
                confidence=0.0,
                status=AgentDecision.OUT_OF_SCOPE,
                metadata={"error": str(e)},
            )

    def _handle_out_of_scope(self, analysis: AnalysisResult) -> EvaluationResult:
        """處理超出範圍的問題

        Args:
            analysis: 分析結果

        Returns:
            EvaluationResult: 評估結果
        """
        # 根據問題類型生成不同的回應
        if analysis.question_type.value == "contact":
            final_answer = """感謝您想要聯絡我！

您可以透過以下方式與我聯繫：
• Email: 請透過 LinkedIn 或其他專業平台與我聯繫
• 或者您可以在下方留下您的問題和聯絡方式

我會盡快回覆您的訊息。"""
        else:
            final_answer = """抱歉，這個問題可能超出了我的履歷範圍，或者我無法找到足夠相關的資訊來回答。

如果您有其他關於我的：
• 專業技能和經驗
• 工作經歷和專案
• 教育背景
• 職業發展

等問題，我很樂意為您解答。

如果您希望獲得更詳細的資訊，也歡迎直接與我聯繫！"""

        return EvaluationResult(
            final_answer=final_answer,
            sources=[],
            confidence=0.1,
            status=AgentDecision.OUT_OF_SCOPE,
            metadata={
                "reason": "超出履歷範圍",
                "original_reason": analysis.metadata.get("reason", ""),
            },
        )

    def _handle_clarification(self, analysis: AnalysisResult) -> EvaluationResult:
        """處理需要澄清的問題

        Args:
            analysis: 分析結果

        Returns:
            EvaluationResult: 評估結果
        """
        final_answer = """我需要更多資訊才能更好地回答您的問題。

您可以嘗試：
• 更具體地描述您想了解的內容
• 詢問特定的技能、專案或經驗
• 使用更明確的關鍵字

例如：
• "你有什麼程式設計經驗？"
• "你參與過哪些專案？"
• "你的教育背景是什麼？"

請隨時重新提問，我會盡力為您解答！"""

        return EvaluationResult(
            final_answer=final_answer,
            sources=[],
            confidence=0.2,
            status=AgentDecision.ASK_CLARIFY,
            metadata={"reason": "問題需要澄清"},
        )

    def _evaluate_retrieval_result(self, analysis: AnalysisResult) -> EvaluationResult:
        """評估檢索結果並生成最終回答

        Args:
            analysis: 分析結果

        Returns:
            EvaluationResult: 評估結果
        """
        if not analysis.retrievals or not analysis.draft_answer:
            return self._handle_out_of_scope(analysis)

        # 檢查來源支持度
        source_support = self._calculate_source_support(analysis.retrievals)

        # 根據信心水平決定處理方式
        if analysis.confidence < self.confidence_threshold:
            # 低信心：需要警告用戶
            return self._handle_low_confidence(analysis, source_support)

        elif source_support < self.min_source_support:
            # 來源支持度不足：需要編輯
            return EvaluationResult(
                final_answer=analysis.draft_answer,
                sources=self._extract_source_ids(analysis.retrievals),
                confidence=analysis.confidence,
                status=AgentDecision.NEEDS_EDIT,
                suggestions=["add_source_warning", "improve_source_support"],
                metadata={"source_support": source_support, "requires_editing": True},
            )

        else:
            # 高信心且來源充足：直接使用
            refined_answer = self._refine_answer(
                analysis.draft_answer, analysis.retrievals
            )

            return EvaluationResult(
                final_answer=refined_answer,
                sources=self._extract_source_ids(analysis.retrievals),
                confidence=analysis.confidence,
                status=AgentDecision.RETRIEVE,
                metadata={"source_support": source_support, "quality": "high"},
            )

    def _handle_low_confidence(
        self, analysis: AnalysisResult, source_support: float
    ) -> EvaluationResult:
        """處理低信心的回答

        Args:
            analysis: 分析結果
            source_support: 來源支持度

        Returns:
            EvaluationResult: 評估結果
        """
        # 在回答前加上信心警告
        confidence_warning = "⚠️ 以下資訊可能不夠完整，建議進一步確認：\n\n"

        refined_answer = confidence_warning + analysis.draft_answer

        # 添加聯絡建議
        contact_suggestion = "\n\n如需更詳細或準確的資訊，歡迎直接與我聯繫。"
        refined_answer += contact_suggestion

        return EvaluationResult(
            final_answer=refined_answer,
            sources=self._extract_source_ids(analysis.retrievals),
            confidence=analysis.confidence,
            status=AgentDecision.RETRIEVE,
            metadata={
                "source_support": source_support,
                "quality": "low_confidence",
                "warning_added": True,
            },
        )

    def _calculate_source_support(self, retrievals: List) -> float:
        """計算來源支持度

        Args:
            retrievals: 檢索結果列表

        Returns:
            float: 來源支持度 (0-1)
        """
        if not retrievals:
            return 0.0

        # 基於相關性分數計算支持度
        scores = [r.score for r in retrievals]
        avg_score = sum(scores) / len(scores)

        # 考慮結果數量的影響
        count_factor = min(len(retrievals) / 3.0, 1.0)  # 3個或更多結果視為完整

        return avg_score * count_factor

    def _extract_source_ids(self, retrievals: List) -> List[str]:
        """提取來源ID列表

        Args:
            retrievals: 檢索結果列表

        Returns:
            List[str]: 來源ID列表
        """
        return [r.doc_id for r in retrievals[:3]]  # 限制最多3個來源

    def _refine_answer(self, draft_answer: str, retrievals: List) -> str:
        """精煉回答內容

        Args:
            draft_answer: 草稿回答
            retrievals: 檢索結果

        Returns:
            str: 精煉後的回答
        """
        if not draft_answer:
            return draft_answer

        refined = draft_answer

        # 確保回答有適當的結構
        if not refined.startswith(("根據", "基於", "從我的")):
            refined = "根據我的履歷資料，" + refined

        # 確保有來源標註
        if "[來源:" not in refined and retrievals:
            source_ids = [r.doc_id for r in retrievals[:2]]
            refined += f"\n\n[參考來源: {', '.join(source_ids)}]"

        # 添加友善的結尾
        if not refined.endswith(("。", "！", "?")):
            refined += "。"

        refined += "\n\n如果您需要更多詳細資訊，歡迎進一步提問！"

        return refined
