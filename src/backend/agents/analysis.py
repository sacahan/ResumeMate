"""Analysis Agent 實作

負責解析使用者問題、辨識問題類型、決定檢索策略
"""

import logging
from typing import List
from backend.models import (
    Question,
    AnalysisResult,
    QuestionType,
    AgentDecision,
    SearchResult,
)
from backend.tools.rag import rag_search

logger = logging.getLogger(__name__)


class AnalysisAgent:
    """Analysis Agent - 問題分析與檢索代理人"""

    def __init__(self, rag_tools=None):
        """初始化 Analysis Agent

        Args:
            rag_tools: optional 注入的 RAGTools 實例，測試與外部呼叫可傳入
        """
        # 注入的 RAG 工具（若有）
        self.rag_tools = rag_tools
        # 進一步降低閾值，適應當前嵌入模型
        self.similarity_threshold = 0.01

    async def analyze(self, question: Question) -> AnalysisResult:
        """分析問題並執行檢索

        Args:
            question: 使用者問題

        Returns:
            AnalysisResult: 分析結果
        """
        logger.info(f"開始分析問題: {question.text}")

        try:
            # 1. 問題類型識別
            question_type = self._classify_question(question.text)

            # 2. 判斷是否需要檢索
            if self._should_retrieve(question.text, question_type):
                # 3. 生成檢索查詢
                query = self._generate_search_query(question.text, question_type)

                # 4. 執行 RAG 檢索
                retrievals = rag_search(query, top_k=5)

                # 5. 檢查檢索結果品質
                if self._is_retrieval_sufficient(retrievals):
                    # 6. 生成草稿回答
                    draft_answer = self._generate_draft_answer(
                        question.text, retrievals
                    )

                    return AnalysisResult(
                        query=query,
                        question_type=question_type,
                        decision=AgentDecision.RETRIEVE,
                        confidence=self._calculate_confidence(retrievals),
                        retrievals=retrievals,
                        draft_answer=draft_answer,
                        metadata={
                            "retrieval_count": len(retrievals),
                            "max_score": max([r.score for r in retrievals])
                            if retrievals
                            else 0,
                        },
                    )
                else:
                    # 檢索結果不足，標記為超出範圍
                    return AnalysisResult(
                        query=query,
                        question_type=question_type,
                        decision=AgentDecision.OUT_OF_SCOPE,
                        confidence=0.1,
                        retrievals=retrievals,
                        metadata={
                            "reason": "檢索結果相關性不足",
                            "max_score": max([r.score for r in retrievals])
                            if retrievals
                            else 0,
                        },
                    )
            else:
                # 不需要檢索的問題類型
                if question_type == QuestionType.CONTACT:
                    return AnalysisResult(
                        query="",
                        question_type=question_type,
                        decision=AgentDecision.OUT_OF_SCOPE,
                        confidence=0.9,
                        metadata={"reason": "聯絡資訊請求"},
                    )
                else:
                    return AnalysisResult(
                        query="",
                        question_type=question_type,
                        decision=AgentDecision.ASK_CLARIFY,
                        confidence=0.3,
                        metadata={"reason": "問題不夠明確"},
                    )

        except Exception as e:
            logger.error(f"分析問題時發生錯誤: {e}")
            return AnalysisResult(
                query="",
                question_type=QuestionType.OTHER,
                decision=AgentDecision.OUT_OF_SCOPE,
                confidence=0.0,
                metadata={"error": str(e)},
            )

    def _classify_question(self, question_text: str) -> QuestionType:
        """問題類型分類

        Args:
            question_text: 問題文本

        Returns:
            QuestionType: 問題類型
        """
        text_lower = question_text.lower()

        # 技能相關關鍵字
        skill_keywords = [
            "技能",
            "skill",
            "程式",
            "programming",
            "開發",
            "development",
            "語言",
            "language",
            "框架",
            "framework",
            "工具",
            "tool",
        ]

        # 經歷相關關鍵字
        experience_keywords = [
            "經驗",
            "experience",
            "工作",
            "work",
            "專案",
            "project",
            "公司",
            "company",
            "職位",
            "position",
            "角色",
            "role",
        ]

        # 聯絡相關關鍵字
        contact_keywords = [
            "聯絡",
            "contact",
            "email",
            "電話",
            "phone",
            "地址",
            "address",
            "面試",
            "interview",
            "合作",
            "collaboration",
        ]

        # 事實查詢關鍵字
        fact_keywords = [
            "什麼",
            "what",
            "誰",
            "who",
            "哪裡",
            "where",
            "何時",
            "when",
            "如何",
            "how",
            "為什麼",
            "why",
        ]

        # 根據關鍵字判斷類型
        if any(keyword in text_lower for keyword in skill_keywords):
            return QuestionType.SKILL
        elif any(keyword in text_lower for keyword in experience_keywords):
            return QuestionType.EXPERIENCE
        elif any(keyword in text_lower for keyword in contact_keywords):
            return QuestionType.CONTACT
        elif any(keyword in text_lower for keyword in fact_keywords):
            return QuestionType.FACT
        else:
            return QuestionType.OTHER

    def _should_retrieve(self, question_text: str, question_type: QuestionType) -> bool:
        """判斷是否需要進行檢索

        Args:
            question_text: 問題文本
            question_type: 問題類型

        Returns:
            bool: 是否需要檢索
        """
        # 聯絡類型問題通常不需要檢索
        if question_type == QuestionType.CONTACT:
            return False

        # 若為事實查詢（FACT），通常不是履歷內容可回答的，回傳 False
        if question_type == QuestionType.FACT:
            return False

        # 其他類型問題需要檢索
        return True

    def _generate_search_query(
        self, question_text: str, question_type: QuestionType
    ) -> str:
        """生成檢索查詢

        Args:
            question_text: 原始問題
            question_type: 問題類型

        Returns:
            str: 優化後的檢索查詢
        """
        # 基本清理：移除標點符號、轉換為小寫
        query = question_text.strip()

        # 根據問題類型添加關鍵字
        if question_type == QuestionType.SKILL:
            # 技能問題：保持原樣或添加技能相關詞彙
            pass
        elif question_type == QuestionType.EXPERIENCE:
            # 經歷問題：添加工作、專案相關詞彙
            pass
        elif question_type == QuestionType.FACT:
            # 事實問題：移除疑問詞，保留核心概念
            question_words = [
                "什麼",
                "誰",
                "哪裡",
                "何時",
                "如何",
                "為什麼",
                "什么",
                "谁",
                "哪里",
                "何时",
                "怎么",
                "为什么",
            ]
            for word in question_words:
                query = query.replace(word, "")

        return query.strip()

    def _is_retrieval_sufficient(self, retrievals: List[SearchResult]) -> bool:
        """檢查檢索結果是否足夠

        Args:
            retrievals: 檢索結果列表

        Returns:
            bool: 檢索結果是否足夠
        """
        if not retrievals:
            return False

        # 檢查最高分數是否超過閾值
        max_score = max([r.score for r in retrievals])
        return max_score >= self.similarity_threshold

    def _calculate_confidence(self, retrievals: List[SearchResult]) -> float:
        """計算信心分數

        Args:
            retrievals: 檢索結果列表

        Returns:
            float: 信心分數 (0-1)
        """
        if not retrievals:
            return 0.0

        # 基於最高分數和結果數量計算信心
        max_score = max([r.score for r in retrievals])
        avg_score = sum([r.score for r in retrievals]) / len(retrievals)

        # 信心分數計算：加權平均
        confidence = max_score * 0.7 + avg_score * 0.3

        # 根據結果數量調整
        if len(retrievals) >= 3:
            confidence *= 1.0
        elif len(retrievals) == 2:
            confidence *= 0.8
        else:
            confidence *= 0.6

        return min(confidence, 1.0)

    def _generate_draft_answer(
        self, question: str, retrievals: List[SearchResult]
    ) -> str:
        """生成草稿回答

        Args:
            question: 原始問題
            retrievals: 檢索結果

        Returns:
            str: 草稿回答
        """
        if not retrievals:
            return "抱歉，我找不到相關的資訊來回答您的問題。"

        # 根據問題類型選擇最相關的片段
        question_lower = question.lower()
        relevant_excerpts = []
        high_priority_excerpts = []  # 高優先級的片段

        # 篩選高品質的檢索結果
        for retrieval in retrievals:
            if retrieval.score >= 0.3:  # 只使用高相關性的結果
                # 根據問題關鍵字進一步篩選
                excerpt_lower = retrieval.excerpt.lower()
                doc_id = retrieval.doc_id.lower()
                is_relevant = False
                is_high_priority = False

                # 技能相關問題 - 優先選擇 skills_ 開頭的文件
                if any(
                    keyword in question_lower
                    for keyword in [
                        "技能",
                        "skill",
                        "能力",
                        "會",
                        "語言",
                        "框架",
                        "程式",
                    ]
                ):
                    if "skills_" in doc_id:
                        is_relevant = True
                        is_high_priority = True  # 技能文件優先級最高
                    elif any(
                        tech in excerpt_lower
                        for tech in [
                            "python",
                            "javascript",
                            "react",
                            "django",
                            "程式",
                            "技術",
                            "開發",
                            "語言",
                        ]
                    ):
                        is_relevant = True

                # 經驗相關問題 - 優先選擇 experience_ 開頭的文件
                elif any(
                    keyword in question_lower
                    for keyword in ["經驗", "experience", "工作", "專案", "project"]
                ):
                    if "experience_" in doc_id or "projects_" in doc_id:
                        is_relevant = True
                        is_high_priority = True  # 經驗和專案文件優先級最高
                    elif any(
                        exp in excerpt_lower
                        for exp in ["工程師", "專案", "系統", "開發", "負責", "參與"]
                    ):
                        is_relevant = True

                # 教育相關問題 - 優先選擇 education_ 開頭的文件
                elif any(
                    keyword in question_lower
                    for keyword in ["教育", "學歷", "畢業", "大學", "學位"]
                ):
                    if "education_" in doc_id:
                        is_relevant = True
                        is_high_priority = True  # 教育文件優先級最高
                    elif any(
                        edu in excerpt_lower for edu in ["學位", "大學", "畢業", "學習"]
                    ):
                        is_relevant = True

                # 通用相關性檢查
                else:
                    is_relevant = retrieval.score >= 0.4

                if is_relevant:
                    if is_high_priority:
                        high_priority_excerpts.append(retrieval)
                    else:
                        relevant_excerpts.append(retrieval)

        # 合併，高優先級的在前面
        final_excerpts = high_priority_excerpts + relevant_excerpts

        # 如果沒有找到相關內容，降低標準重新選擇
        if not final_excerpts:
            final_excerpts = [r for r in retrievals[:2] if r.score >= 0.2]

        if not final_excerpts:
            return "抱歉，找到的資訊與您的問題關聯性較低，無法提供準確的回答。"

        # 根據問題類型生成更有針對性的回答
        best_retrieval = final_excerpts[0]
        if any(keyword in question_lower for keyword in ["技能", "skill", "能力"]):
            draft = "關於我的技能，" + best_retrieval.excerpt
        elif any(
            keyword in question_lower for keyword in ["經驗", "experience", "工作"]
        ):
            draft = "關於我的工作經驗，" + best_retrieval.excerpt
        elif any(keyword in question_lower for keyword in ["教育", "學歷"]):
            draft = "關於我的教育背景，" + best_retrieval.excerpt
        else:
            draft = "根據我的資料，" + best_retrieval.excerpt

        # 添加來源提示
        source_ids = [r.doc_id for r in final_excerpts[:2]]
        draft += f"\n\n[來源: {', '.join(source_ids)}]"

        return draft

    async def revise(
        self, analysis: AnalysisResult, suggestions: List[str]
    ) -> AnalysisResult:
        """根據建議修正分析結果

        Args:
            analysis: 原始分析結果
            suggestions: 修正建議

        Returns:
            AnalysisResult: 修正後的分析結果
        """
        logger.info(f"根據建議修正分析結果: {suggestions}")

        # 簡單的修正邏輯：重新生成草稿
        if analysis.retrievals:
            revised_draft = self._apply_suggestions(analysis.draft_answer, suggestions)
            analysis.draft_answer = revised_draft
            analysis.metadata["revised"] = True
            analysis.metadata["suggestions"] = suggestions

        return analysis

    def _apply_suggestions(self, draft: str, suggestions: List[str]) -> str:
        """應用修正建議

        Args:
            draft: 原始草稿
            suggestions: 建議列表

        Returns:
            str: 修正後的草稿
        """
        if not draft:
            return draft

        revised = draft

        # 簡單的建議應用邏輯
        for suggestion in suggestions:
            if "too_long" in suggestion:
                # 縮短回答
                sentences = revised.split("。")
                revised = "。".join(sentences[:2]) + "。"
            elif "add_source" in suggestion:
                # 確保有來源標註
                if "[來源:" not in revised:
                    revised += "\n\n[來源: 相關文件]"

        return revised
