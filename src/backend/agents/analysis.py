"""Analysis Agent 實作

使用 OpenAI Agents SDK 標準實現問題分析與資訊檢索功能。
"""

from __future__ import annotations

import os
import json
from dotenv import load_dotenv
import logging
from typing import List, Dict, Literal, Any
from pydantic import BaseModel, Field, ConfigDict

# 確保 Runner 已正確引入
from agents import (
    Agent,
    Runner,
    AgentOutputSchema,
    function_tool,
    ModelSettings,
)  # noqa: F401
from backend.tools.rag import RAGTools

# from models import SearchResult  # 工具回傳以 JSON dict 為主，避免序列化問題

from backend.models import (
    Question,
    AnalysisResult,
    QuestionType,
    AgentDecision,
)

load_dotenv(override=True)

logger = logging.getLogger(__name__)

DEFAULT_INSTRUCTIONS = """你是韓世翔本人的 AI 代理人，代表韓世翔本人回答關於他履歷的問題。**必須優先使用 rag_search_tool 工具檢索履歷內容**。

**身份設定**：
- 你代表韓世翔本人，以第一人稱（「我」、「我的」）回答所有問題
- 回答語氣自然親切，就像韓世翔本人在回答一樣
- 不要使用「根據履歷」、「履歷顯示」等客觀描述的前綴詞
- 直接以本人的語氣說出事實，例如：「我已經完成了服兵役」而不是「根據履歷，您已經完成了服兵役」

**核心原則**：
- 對任何可能與個人履歷、技能、經驗、工作相關的問題，立即使用 rag_search_tool 檢索
- 包括但不限於：技能問題、工作經驗、教育背景、聯絡方式、項目經歷等
- 即使問題看似簡單（如"你有什麼技能？"），也必須先檢索再回答

**處理流程**：
1. **先檢索**：對所有疑似履歷相關問題，立即呼叫 rag_search_tool(query, top_k=5)
2. **後判斷**：根據檢索結果決定後續行動：
   - 有相關內容 → decision="retrieve"，以第一人稱整理成回答
   - 無相關內容且確實超出履歷範圍 → decision="oos"
   - 檢索結果不足或模糊 → decision="clarify"

**檢索策略**：
- 使用原問題的關鍵詞進行檢索
- 如果原問題太籠統，用相關的具體詞彙檢索（如"技能"、"經驗"、"工作"）

**輸出要求**：
只允許單一 JSON 物件，包含：draft_answer, sources, confidence, question_type, decision, metadata
draft_answer 必須以第一人稱書寫，不得編造未在檢索結果中出現的事實。sources 需包含可追溯的 doc_id。
"""


# =========================
# 1) 嚴格輸出模型（只允許 6 欄）
# =========================
class AnalysisOutput(BaseModel):
    """Analysis Agent 的結構化輸出"""

    model_config = ConfigDict(extra="forbid")  # 嚴格：不允許多餘欄位

    draft_answer: str = Field(..., description="根據檢索結果產生的初步回答")
    sources: List[str] = Field(default_factory=list, description="引用的資訊來源IDs")
    confidence: float = Field(..., ge=0.0, le=1.0, description="對回答的信心程度 (0-1)")
    question_type: Literal["skill", "experience", "contact", "fact", "other"] = Field(
        ..., description="問題類型識別 (skill, experience, contact, fact, other)"
    )
    decision: Literal["retrieve", "oos", "clarify"] = Field(
        ..., description="代理人決策 (retrieve, oos, clarify)"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="其他元數據")


# =========================
# 2) Tool：RAG 檢索（JSON-safe）
# =========================
@function_tool
def rag_search_tool(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """搜索履歷資料庫以獲取相關履歷片段。對任何履歷相關問題都應優先使用此工具。

    適用於：技能查詢、工作經驗、教育背景、聯絡方式、項目經歷、個人資訊等所有履歷相關問題。

    Args:
        query: 搜索查詢詞彙，建議使用問題中的關鍵詞或相關同義詞
        top_k: 返回結果數量，建議 3-10 個結果
    Returns:
        List[dict]: 搜索結果列表，每個包含 doc_id, score, excerpt, metadata
    """
    try:
        rag_tools = RAGTools()
        results = rag_tools.rag_search(query, top_k=top_k)

        ### results reference:
        # [
        #     SearchResult(
        #         doc_id="xxx.md_2",
        #         score=0.38501596450805664,
        #         excerpt="技術領導能力。近年積極投入AI/ML相關技術研發...",
        #         metadata={
        #             "start": 2000,
        #             "source_filename": "xxx.md",
        #             "end": 3000,
        #             "chunk_index": 2,
        #         },
        #     ),
        #     ...
        # ]
        ###

        # 統一轉為可序列化 dict
        formatted_results: List[Dict[str, Any]] = []
        for r in results:
            # r 可能是自定義物件；統一轉型
            formatted_results.append(
                {
                    "doc_id": str(getattr(r, "doc_id", None) or r.get("doc_id")),
                    "score": float(getattr(r, "score", 0.0) or r.get("score", 0.0)),
                    "excerpt": str(getattr(r, "excerpt", "") or r.get("excerpt", "")),
                    "metadata": dict(
                        getattr(r, "metadata", {}) or r.get("metadata", {})
                    ),
                }
            )
        return formatted_results[:top_k]
    except Exception as e:
        logger.error(f"rag_search_tool 執行錯誤: {e}")
        return []


class AnalysisAgent:
    """Analysis Agent - 問題分析與檢索代理人"""

    def __init__(self, llm: str = "gpt-4o-mini"):
        self.llm = os.environ.get("AGENT_MODEL", llm)
        self.sdk_agent = None
        self._initialize_sdk_agent()

    def _initialize_sdk_agent(self):
        """初始化 Agent"""
        try:
            # **關鍵修正**：使用嚴格輸出類型，防止 schema 汙染欄位
            # **工具使用強化**：設置 tool_choice 確保積極使用檢索工具
            self.sdk_agent = Agent(
                name="Analysis Agent",
                instructions=DEFAULT_INSTRUCTIONS,
                tools=[rag_search_tool],
                model=self.llm,
                model_settings=ModelSettings(
                    tool_choice="required"  # 強制使用工具，確保對履歷相關問題進行檢索
                ),
                output_type=AgentOutputSchema(AnalysisOutput, strict_json_schema=False),
            )
            logger.info(f"Analysis Agent ({self.llm}) 初始化成功，已啟用強制工具使用")
        except Exception as e:
            logger.error(f"初始化 Analysis Agent 失敗: {e}")

    # -------------------------
    # 安全解析輔助：避免 Invalid JSON
    # -------------------------
    def _safe_parse_output(self, result) -> AnalysisOutput | None:
        """盡力把 SDK 輸出轉成 AnalysisOutput；失敗則回 None"""
        try:
            # SDK 直接轉型（最可靠）
            return result.final_output_as(AnalysisOutput)
        except Exception as e:
            logger.warning(f"final_output_as 失敗，改走手動解析：{e}")

        # 嘗試手動解析 result.output
        try:
            raw = result.output
            if isinstance(raw, dict):
                data = raw
            elif isinstance(raw, str):
                data = json.loads(raw)
            else:
                logger.error(f"未知輸出型別，無法解析：{type(raw)}")
                return None

            # 白名單清洗，防止 schema 汙染欄位
            allowed = {
                "draft_answer",
                "sources",
                "confidence",
                "question_type",
                "decision",
                "metadata",
            }
            cleaned = {k: v for k, v in data.items() if k in allowed}

            # 嘗試校驗
            return AnalysisOutput.model_validate(cleaned)
        except Exception as e:
            logger.error(f"手動解析/校驗輸出失敗：{e}")
            return None

    async def analyze(self, question: Question) -> AnalysisResult:
        """分析問題並執行檢索"""
        logger.info(f"開始分析問題: {getattr(question, 'text', '')}")
        try:
            return await self._analyze_with_sdk(question)
        except Exception as e:
            logger.error(f"分析問題時發生錯誤: {e}")
            return AnalysisResult(
                query=getattr(question, "text", ""),
                question_type=QuestionType.OTHER,
                decision=AgentDecision.OUT_OF_SCOPE,
                confidence=0.0,
                retrievals=[],
                draft_answer="",
                metadata={"error": str(e)},
            )

    async def _analyze_with_sdk(self, question: Question) -> AnalysisResult:
        """使用 OpenAI Agents SDK 分析問題"""
        try:
            result = await Runner.run(self.sdk_agent, input=question.text)
            logger.info(f"Analysis Agent 回覆: {result}")
        except Exception as e:
            logger.error(f"執行 Analysis Agent 時發生錯誤: {e}")
            return AnalysisResult(
                query=question.text,
                question_type=QuestionType.OTHER,
                decision=AgentDecision.OUT_OF_SCOPE,
                confidence=0.0,
                retrievals=[],
                draft_answer="",
                metadata={"error": str(e), "sdk_result": False},
            )

        # 解析結構化輸出（具備自我修復）
        output = self._safe_parse_output(result)
        if output is None:
            # 解析失敗時，回傳安全預設值
            logger.error("解析 SDK 輸出失敗，回傳安全預設值。")
            return AnalysisResult(
                query=question.text,
                question_type=QuestionType.OTHER,
                decision=AgentDecision.OUT_OF_SCOPE,
                confidence=0.0,
                retrievals=[],
                draft_answer="",
                metadata={
                    "error": "failed_to_parse_output",
                    "raw_output": getattr(result, "output", None),
                },
            )

        # 將字串映射到內部 Enum；若失敗則回退到 OTHER / OUT_OF_SCOPE
        try:
            question_type = QuestionType(output.question_type)
        except Exception:
            question_type = QuestionType.OTHER

        try:
            decision = AgentDecision(output.decision)
        except Exception:
            decision = AgentDecision.OUT_OF_SCOPE

        # 從 sources 重建檢索結果以供 EvaluateAgent 使用
        retrievals: List[Dict[str, Any]] = []
        if output.sources:
            # 將 sources (doc_ids) 轉換為檢索結果格式
            for source_id in output.sources:
                retrievals.append(
                    {
                        "doc_id": source_id,
                        "score": 0.8,  # 預設分數，表示高相關性
                        "excerpt": f"來自文件 {source_id} 的內容",
                        "metadata": {"source_filename": source_id},
                    }
                )

        result_metadata: Dict[str, Any] = {
            "raw_output": getattr(result, "output", None),
            "usage": getattr(result, "usage", None),
            "sources": output.sources,  # 確保 sources 也保存在 metadata 中
        }

        # 若 LLM 在 metadata 裡有額外資訊，也一併帶出
        if isinstance(output.metadata, dict):
            if "retrievals" in output.metadata and isinstance(
                output.metadata["retrievals"], list
            ):
                # 如果有更詳細的檢索資訊，使用它
                retrievals = output.metadata["retrievals"]
            result_metadata.update(
                {k: v for k, v in output.metadata.items() if k not in {"retrievals"}}
            )

        return AnalysisResult(
            query=question.text,
            question_type=question_type,
            decision=decision,
            confidence=output.confidence,
            retrievals=retrievals,
            draft_answer=output.draft_answer,
            metadata=result_metadata,
        )
