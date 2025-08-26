"""ResumeMate Analysis Agent 測試"""

import pytest
import sys
import os

# 添加 src 目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from backend.models import Question, QuestionType, AgentDecision
from backend.agents import AnalysisAgent
from backend.tools import RAGTools


class TestAnalysisAgent:
    """Analysis Agent 測試類別"""

    @pytest.fixture
    def rag_tools(self):
        """RAG 工具 fixture"""
        return RAGTools()

    @pytest.fixture
    def analysis_agent(self, rag_tools):
        """Analysis Agent fixture"""
        return AnalysisAgent(rag_tools)

    @pytest.mark.asyncio
    async def test_skill_question_classification(self, analysis_agent):
        """測試技能問題分類"""
        question = Question(text="你有什麼程式設計技能？")
        result = await analysis_agent.analyze(question)

        assert result.question_type == QuestionType.SKILL
        assert result.decision == AgentDecision.RETRIEVE
        assert len(result.retrievals) > 0
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_experience_question_classification(self, analysis_agent):
        """測試經驗問題分類"""
        question = Question(text="你的工作經驗如何？")
        result = await analysis_agent.analyze(question)

        assert result.question_type == QuestionType.EXPERIENCE
        assert result.decision == AgentDecision.RETRIEVE
        assert len(result.retrievals) > 0

    @pytest.mark.asyncio
    async def test_contact_question_classification(self, analysis_agent):
        """測試聯絡問題分類"""
        question = Question(text="如何聯絡你？")
        result = await analysis_agent.analyze(question)

        assert result.question_type == QuestionType.CONTACT
        assert result.decision == AgentDecision.OUT_OF_SCOPE

    @pytest.mark.asyncio
    async def test_irrelevant_question(self, analysis_agent):
        """測試不相關問題"""
        question = Question(text="今天天氣如何？")
        result = await analysis_agent.analyze(question)

        # 不相關問題應該被標記為超出範圍或需要澄清
        assert result.decision in [
            AgentDecision.OUT_OF_SCOPE,
            AgentDecision.ASK_CLARIFY,
        ]
        assert result.confidence < 0.5

    @pytest.mark.asyncio
    async def test_empty_question(self, analysis_agent):
        """測試空問題"""
        question = Question(text="")
        result = await analysis_agent.analyze(question)

        assert result.decision in [
            AgentDecision.OUT_OF_SCOPE,
            AgentDecision.ASK_CLARIFY,
        ]
        assert result.confidence < 0.5

    def test_question_type_classification(self, analysis_agent):
        """測試問題類型分類邏輯"""
        # 技能相關
        assert (
            analysis_agent._classify_question("你會什麼程式語言？")
            == QuestionType.SKILL
        )
        assert (
            analysis_agent._classify_question("What programming skills do you have?")
            == QuestionType.SKILL
        )

        # 經驗相關
        assert (
            analysis_agent._classify_question("你的工作經驗？")
            == QuestionType.EXPERIENCE
        )
        assert (
            analysis_agent._classify_question("Tell me about your projects")
            == QuestionType.EXPERIENCE
        )

        # 聯絡相關
        assert analysis_agent._classify_question("如何聯絡你？") == QuestionType.CONTACT
        assert (
            analysis_agent._classify_question("What's your email?")
            == QuestionType.CONTACT
        )

        # 事實查詢
        assert analysis_agent._classify_question("你是誰？") == QuestionType.FACT
        assert (
            analysis_agent._classify_question("What is your background?")
            == QuestionType.FACT
        )

    def test_search_query_generation(self, analysis_agent):
        """測試檢索查詢生成"""
        # 技能問題
        query = analysis_agent._generate_search_query(
            "你有什麼Python經驗？", QuestionType.SKILL
        )
        assert "Python" in query

        # 經驗問題
        query = analysis_agent._generate_search_query(
            "告訴我你的專案經驗", QuestionType.EXPERIENCE
        )
        assert len(query) > 0

    def test_confidence_calculation(self, analysis_agent):
        """測試信心分數計算"""
        from backend.models import SearchResult

        # 高分數結果
        high_score_results = [
            SearchResult(doc_id="test1", score=0.8, excerpt="test"),
            SearchResult(doc_id="test2", score=0.7, excerpt="test"),
            SearchResult(doc_id="test3", score=0.6, excerpt="test"),
        ]
        confidence = analysis_agent._calculate_confidence(high_score_results)
        assert confidence > 0.6

        # 低分數結果
        low_score_results = [
            SearchResult(doc_id="test1", score=0.1, excerpt="test"),
            SearchResult(doc_id="test2", score=0.05, excerpt="test"),
        ]
        confidence = analysis_agent._calculate_confidence(low_score_results)
        assert confidence < 0.3

        # 空結果
        confidence = analysis_agent._calculate_confidence([])
        assert confidence == 0.0


if __name__ == "__main__":
    # 執行特定測試
    pytest.main([__file__, "-v"])
