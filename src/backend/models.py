"""共用數據模型定義

根據開發計劃中的 Pydantic Models 設計
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict
from datetime import datetime
import enum


class QuestionType(str, enum.Enum):
    """問題類型枚舉"""

    FACT = "fact"  # 事實查詢
    SKILL = "skill"  # 技能相關
    EXPERIENCE = "experience"  # 經歷相關
    CONTACT = "contact"  # 聯絡相關
    OTHER = "other"  # 其他類型


class AgentDecision(str, enum.Enum):
    """代理人決策枚舉"""

    RETRIEVE = "retrieve"  # 需要檢索資訊
    OUT_OF_SCOPE = "oos"  # 超出範圍
    ASK_CLARIFY = "clarify"  # 需要澄清
    NEEDS_EDIT = "needs_edit"  # 需要編輯


class SearchResult(BaseModel):
    """RAG 檢索結果"""

    doc_id: str = Field(..., description="文件唯一識別碼")
    score: float = Field(..., ge=0, le=1, description="相關性分數")
    excerpt: str = Field(..., description="檢索片段內容")
    metadata: Dict = Field(default_factory=dict, description="額外元數據")


class Question(BaseModel):
    """使用者問題模型"""

    text: str = Field(..., description="原始問題文本")
    type: QuestionType = Field(default=QuestionType.OTHER, description="問題類型")
    timestamp: datetime = Field(default_factory=datetime.now)
    language: Literal["zh-TW", "en"] = Field(default="zh-TW", description="問題語言")
    context: Optional[List[str]] = Field(default=None, description="上下文對話歷史")


class AnalysisResult(BaseModel):
    """Analysis Agent 分析結果"""

    query: str = Field(..., description="優化後的檢索查詢")
    question_type: QuestionType = Field(..., description="識別的問題類型")
    decision: AgentDecision = Field(..., description="代理人決策")
    confidence: float = Field(..., ge=0, le=1, description="信心分數")
    retrievals: Optional[List[SearchResult]] = None
    draft_answer: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    """Evaluate Agent 評估結果"""

    final_answer: str = Field(..., description="最終回答內容")
    sources: List[str] = Field(..., description="來源文件ID列表")
    confidence: float = Field(..., ge=0, le=1, description="信心分數")
    status: AgentDecision = Field(..., description="評估狀態")
    suggestions: Optional[List[str]] = None
    metadata: Dict = Field(default_factory=dict)


class SystemResponse(BaseModel):
    """系統最終回應"""

    answer: str = Field(..., description="回答內容")
    sources: List[str] = Field(..., description="來源參考")
    confidence: float = Field(..., ge=0, le=1, description="系統信心分數")
    action: Optional[str] = None  # 例如："請填寫聯絡表單"
    metadata: Dict = Field(default_factory=dict)


class OutOfScopeRecord(BaseModel):
    """超出範圍問題記錄"""

    question_id: str = Field(..., description="問題唯一識別碼")
    question: Question
    user_meta: Dict = Field(..., description="使用者相關資訊")
    timestamp: datetime = Field(default_factory=datetime.now)
    status: Literal["pending", "contacted", "resolved"] = "pending"


class ConversationState(BaseModel):
    """對話狀態追蹤"""

    conversation_id: str
    question_history: List[Question]
    current_question: Question
    analysis_results: List[AnalysisResult]
    evaluation_results: List[EvaluationResult]
    metadata: Dict = Field(default_factory=dict)
