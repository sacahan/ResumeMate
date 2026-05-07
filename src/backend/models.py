"""共用數據模型定義"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict
from datetime import datetime


class Question(BaseModel):
    """使用者問題模型"""

    text: str = Field(..., description="原始問題文本")
    timestamp: datetime = Field(default_factory=datetime.now)
    language: Literal["zh-TW", "en"] = Field(default="zh-TW", description="問題語言")
    context: Optional[List[str]] = Field(default=None, description="上下文對話歷史")


class SystemResponse(BaseModel):
    """系統最終回應"""

    answer: str = Field(..., description="回答內容")
    sources: List[str] = Field(..., description="來源參考")
    confidence: float = Field(..., ge=0, le=1, description="系統信心分數")
    action: Optional[str] = None  # 例如："請填寫聯絡表單"
    metadata: Dict = Field(default_factory=dict)
