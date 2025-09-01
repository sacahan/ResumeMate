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
        assert result.decision == AgentDecision.RETRIEVE

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

        # With forced tool usage, empty questions may still retrieve content
        assert result.decision in [
            AgentDecision.RETRIEVE,
            AgentDecision.OUT_OF_SCOPE,
            AgentDecision.ASK_CLARIFY,
        ]

    @pytest.mark.asyncio
    async def test_self_introduction_questions(self, analysis_agent):
        """測試自我介紹問題（重要的履歷核心功能）"""
        questions = ["介紹一下自己", "你是誰？", "Tell me about yourself", "自我介紹"]

        for question_text in questions:
            question = Question(text=question_text)
            result = await analysis_agent.analyze(question)

            # 自我介紹應該使用RAG檢索，不應該是out-of-scope
            assert (
                result.decision == AgentDecision.RETRIEVE
            ), f"Question '{question_text}' should retrieve, got {result.decision}"
            assert (
                result.confidence > 0.5
            ), f"Low confidence for '{question_text}': {result.confidence}"

    @pytest.mark.asyncio
    async def test_forced_tool_usage(self, analysis_agent):
        """測試強制工具使用功能"""
        # 測試各種問題類型都能觸發適當的工具
        questions = [
            ("你的技能是什麼？", "rag"),
            ("工作經驗如何？", "rag"),
            ("聯絡方式是什麼？", "contact"),
            ("介紹一下自己", "rag"),
        ]

        for question_text, expected_tool in questions:
            question = Question(text=question_text)
            result = await analysis_agent.analyze(question)

            # 由於設定了 tool_choice="required"，所有問題都應該使用檢索
            assert (
                result.decision == AgentDecision.RETRIEVE
            ), f"Question '{question_text}' should retrieve"

            # 檢查是否有使用適當的工具
            if expected_tool == "contact":
                # 聯絡問題使用 get_contact_info，會有 draft_answer
                assert (
                    result.draft_answer is not None
                ), f"No contact info for '{question_text}'"
            else:
                # 其他問題使用 RAG，會有 retrievals
                assert (
                    len(result.retrievals) > 0
                ), f"No retrievals for '{question_text}'"

    @pytest.mark.asyncio
    async def test_career_related_questions(self, analysis_agent):
        """測試所有履歷相關問題都被正確處理"""
        career_questions = [
            "你有什麼技能？",
            "工作經驗如何？",
            "做過什麼專案？",
            "教育背景是什麼？",
            "專業能力有哪些？",
        ]

        for question_text in career_questions:
            question = Question(text=question_text)
            result = await analysis_agent.analyze(question)

            # 所有履歷相關問題都應該檢索，不應該是out-of-scope
            assert (
                result.decision == AgentDecision.RETRIEVE
            ), f"Career question '{question_text}' should retrieve"
            assert (
                result.confidence >= 0.5
            ), f"Low confidence for career question '{question_text}': {result.confidence}"


if __name__ == "__main__":
    # 執行特定測試
    pytest.main([__file__, "-v"])
