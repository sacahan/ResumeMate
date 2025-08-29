"""Evaluate Agent 實作

使用 OpenAI Agents SDK 標準實現回答評估與品質控制功能。
"""

from __future__ import annotations

import os
import json
from dotenv import load_dotenv
import logging
from typing import List, Dict, Literal, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

# 確保 Runner 已正確引入
from agents import Agent, Runner, AgentOutputSchema
from src.backend.models import (
    AnalysisResult,
    EvaluationResult,
    AgentDecision,
)

load_dotenv(override=True)

logger = logging.getLogger(__name__)


DEFAULT_INSTRUCTIONS = """你是回答品質審查代理。輸入為 analysis_agent 的輸出(JSON)。你的目標：
- 檢查草稿是否足以回覆提問者、來源是否充分且一致。
- 產出「最終回答」與明確狀態；必要時引導澄清或升級人工。

**重要語氣要求**：
- 系統代表韓世翔本人回答問題，final_answer 必須保持第一人稱（「我」、「我的」）
- 不要使用「根據履歷」、「履歷顯示」、「您已經」等客觀描述語句
- 如果 analysis_agent 的 draft_answer 已經是正確的第一人稱，直接使用或稍作潤飾
- 回答語氣應該自然親切，就像韓世翔本人在回答一樣

決策邏輯（優先順序）：
1) **聯絡資訊問題**：若問題是詢問聯絡方式、email等，且 analysis_agent 使用了 get_contact_info 工具，則應 → status="ok"，直接提供聯絡資訊
2) 若題目完全與個人履歷/工作經歷無關（如生活習慣、興趣愛好、非工作相關問題等） → status="escalate_to_human"
3) 若題目與履歷相關但涉及真正敏感資訊或資料庫中沒有的資訊（如薪資、內部機密、家庭狀況等） → status="escalate_to_human"
   重要：以下履歷標準資訊應正常回答，不屬於敏感資訊：居住地點、工作地區、聯絡方式、教育背景、技能經驗、工作經歷等
4) 若 analysis_agent.confidence < 0.4 或 sources 為空或不足 → status="escalate_to_human"
5) 若關鍵資訊不足但可透過補充資訊解決（如缺少公司名稱、時間等可補充的具體資訊） → status="needs_clarification"，提供精準追問清單
6) 若草稿可回覆且來源足夠且一致 → status="ok"
7) 若草稿品質不足但能小幅編輯即可修正 → status="needs_edit" 並給出具體修改建議
8) 其他所有情況 → status="escalate_to_human"

重要：傾向於選擇 escalate_to_human 以確保回答品質。當 status="escalate_to_human" 時，請在 final_answer 使用固定話術。

評估規則（最低門檻）：
- **聯絡資訊特殊處理**：對於聯絡資訊問題，如果 analysis_agent 使用了 get_contact_info 工具，則自動 → status="ok"，無需檢查 sources 或 confidence
- 來源覆蓋度：至少 1 個可信來源，且主要結論均可在來源找到對應片段
- 一致性：來源間不自相矛盾
- 信心閾值：若 analysis_agent.confidence < 0.4 或 sources 為空 → 必須標記為 "escalate_to_human"
- 引用規範：不可杜撰來源；final_answer 中的關鍵事實需能對映 sources
- 履歷標準資訊優先：當 analysis_agent 對居住地點、工作區域、聯絡方式、教育背景等履歷標準資訊有高信心且有來源支持時，應選擇 status="ok"

輸出：只允許單一 JSON，且只包含：
final_answer, sources, confidence, status, metadata
（嚴禁輸出 title/description/properties/required/$schema 等任何 schema 欄位）

status ∈ {ok, needs_edit, needs_clarification, out_of_scope, escalate_to_human}
confidence ∈ [0,1]（可在原 confidence 基礎上調整）
metadata 裡需回填：{ "reason": "...", "missing_fields": [...], "original_question": "...", "analysis_confidence": x.x }

範例判斷：
- 問題「如何聯絡你？」+ analysis_agent 使用 get_contact_info → status="ok"，final_answer="我是韓世翔，可以透過 sacahan@gmail.com 聯絡我。"
- 問題「你的email是什麼？」+ analysis_agent 使用 get_contact_info → status="ok"，final_answer="我的email是 sacahan@gmail.com"
- 問題「你現在住在哪裡？」+ analysis_agent 信心 0.9 + 有來源 → status="ok"，final_answer="我目前住在新北市中和區。"
- 問題「你還需要服兵役嗎？」+ analysis_agent 信心 0.9 + 有來源 → status="ok"，final_answer="我已經完成了服兵役，擔任陸軍少尉預官，在2004年10月到2006年1月期間服役。"
- 問題「你的薪水多少？」→ status="escalate_to_human"，因為涉及真正敏感資訊
- 問題「你喜歡什麼電影？」→ status="escalate_to_human"，因為與履歷無關

當 status="escalate_to_human" 時，請在 final_answer 使用此話術：
「目前儲備的來源資料不足以保證回覆正確性。是否同意我先記錄原問題，由本人進行回覆？請提供聯絡方式（稱呼/Email/電話/Line），稍後再由本人回覆。」
"""

# ---------- JSON-safe type
JsonValue = Any


# 嚴格輸出模型（只允許 5 欄）
class EvaluateOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    final_answer: str
    # 使用 dict 以保留 id/title/loc 等追溯欄位
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    status: Literal[
        "ok",
        "needs_edit",
        "needs_clarification",
        "out_of_scope",
        "escalate_to_human",
    ]
    metadata: Dict[str, JsonValue] = Field(default_factory=dict)


class EvaluateAgent:
    """Evaluate Agent - 回答評估與品質控制代理人"""

    def __init__(self, llm: str = "gpt-4o-mini"):
        self.llm = os.environ.get("AGENT_MODEL", llm)
        self.sdk_agent: Optional[Agent] = None
        self._initialize_sdk_agent()

    def _initialize_sdk_agent(self):
        """初始化 Evaluate Agent"""
        try:
            # 使用嚴格 Pydantic 輸出，避免 schema 汙染
            self.sdk_agent = Agent(
                name="Evaluate Agent",
                instructions=DEFAULT_INSTRUCTIONS,
                model=self.llm,
                output_type=AgentOutputSchema(EvaluateOutput, strict_json_schema=False),
            )
            logger.info(f"Evaluate Agent ({self.llm}) 初始化成功")
        except Exception as e:
            logger.error(f"初始化 Evaluate Agent 失敗: {e}")

    # -------------------------
    # 安全解析：即使模型回 schema/雜訊也能修復
    # -------------------------
    def _safe_parse_output(self, result) -> Optional[EvaluateOutput]:
        try:
            return result.final_output_as(EvaluateOutput)
        except Exception as e:
            logger.warning(f"final_output_as 失敗，嘗試手動解析：{e}")

        raw = getattr(result, "output", None)

        try:
            if isinstance(raw, str):
                data = json.loads(raw)
            elif isinstance(raw, dict):
                data = raw
            else:
                logger.error(f"未知輸出型別：{type(raw)}")
                return None

            # 白名單清洗
            allowed = {"final_answer", "sources", "confidence", "status", "metadata"}
            cleaned = {k: v for k, v in data.items() if k in allowed}

            # 某些模型會回 schema-like 結構，嘗試從 example 補值
            if not cleaned and isinstance(data, dict) and "example" in data:
                ex = data["example"]
                if isinstance(ex, dict):
                    cleaned = {k: v for k, v in ex.items() if k in allowed}

            return EvaluateOutput.model_validate(cleaned)
        except Exception as ee:
            logger.error(f"手動解析/校驗輸出失敗：{ee}")
            return None

    async def evaluate(self, analysis: AnalysisResult) -> EvaluationResult:
        """評估分析結果並生成最終回答"""
        logger.info("開始評估分析結果")

        try:
            return await self._evaluate_with_sdk(analysis)
        except Exception as e:
            logger.error(f"評估過程中發生錯誤: {e}")
            return EvaluationResult(
                final_answer="抱歉，系統處理您的問題時發生錯誤，請稍後再試。",
                sources=[],
                confidence=0.0,
                status=self._fallback_status(),
                metadata={"error": str(e)},
            )

    def _fallback_status(self) -> AgentDecision:
        # 優先使用 OUT_OF_SCOPE，否則回傳 enum 第一個值
        if hasattr(AgentDecision, "OUT_OF_SCOPE"):
            return getattr(AgentDecision, "OUT_OF_SCOPE")
        try:
            return list(AgentDecision)[0]
        except Exception:
            # 極端保底：回傳字串（若模型要求 enum，可在上層轉換）
            return AgentDecision  # type: ignore

    def _map_status_to_agent_decision(self, status_str: str) -> AgentDecision:
        """將輸出狀態字串穩健映射到 AgentDecision"""
        s = (status_str or "").strip().lower().replace("-", "_").replace(" ", "_")
        name_map = {
            "oos": "OUT_OF_SCOPE",
            "out_of_scope": "OUT_OF_SCOPE",
            "clarify": "CLARIFY",
            "needs_clarification": "CLARIFY",  # 若有 NEEDS_CLARIFICATION 也會在下方候選命中
            "ok": "RETRIEVE",  # 表示可直接使用；若有 OK 也會試圖命名匹配
            "needs_edit": "NEEDS_EDIT",
            "escalate_to_human": "ESCALATE_TO_HUMAN",
            "retrieve": "RETRIEVE",
        }
        candidates = [
            name_map.get(s),
            s.upper(),
        ]
        # 也嘗試更常見名稱
        candidates.extend(
            [
                "OK",
                "NEEDS_EDIT",
                "NEEDS_CLARIFICATION",
                "OUT_OF_SCOPE",
                "ESCALATE_TO_HUMAN",
                "RETRIEVE",
                "CLARIFY",
            ]
        )
        for c in candidates:
            if not c:
                continue
            if hasattr(AgentDecision, c):
                return getattr(AgentDecision, c)
            # 嘗試以 value 轉換
            try:
                return AgentDecision(c)  # type: ignore
            except Exception:
                pass
        return self._fallback_status()

    async def _evaluate_with_sdk(self, analysis: AnalysisResult) -> EvaluationResult:
        """使用 OpenAI Agents SDK 評估分析結果"""
        # 檢查是否使用了 get_contact_info 工具
        used_contact_info_tool = False
        if analysis.metadata and isinstance(analysis.metadata, dict):
            # 檢查 metadata 中是否有使用工具的資訊
            raw_output = analysis.metadata.get("raw_output")
            if raw_output and isinstance(raw_output, str):
                used_contact_info_tool = "get_contact_info" in raw_output

        # 準備 reviewer 輸入：原問題 + analysis 全量輸出
        analysis_data = {
            "original_question": getattr(analysis, "query", ""),
            "analysis_output": {
                "decision": getattr(analysis.decision, "value", str(analysis.decision)),
                "question_type": getattr(
                    analysis.question_type, "value", str(analysis.question_type)
                ),
                "confidence": analysis.confidence,
                "draft_answer": analysis.draft_answer or "",
                "metadata": analysis.metadata or {},
                "retrievals": [],
                "sources": [],  # 若 analysis 直接輸出了 sources（有些管線會有）
                "used_contact_info_tool": used_contact_info_tool,  # 新增標記
            },
        }

        # 轉載檢索結果（若有）
        try:
            if analysis.retrievals:
                analysis_data["analysis_output"]["retrievals"] = [
                    {
                        "doc_id": getattr(r, "doc_id", getattr(r, "id", None)),
                        "score": getattr(r, "score", None),
                        "excerpt": getattr(r, "excerpt", None),
                        "metadata": getattr(r, "metadata", {}),
                    }
                    for r in analysis.retrievals[:5]
                ]
        except Exception as e:
            logger.warning(f"轉換 retrievals 失敗：{e}")

        # 若 analysis.metadata 內有 sources，帶入
        try:
            meta_sources = (analysis.metadata or {}).get("sources", [])
            if isinstance(meta_sources, list):
                analysis_data["analysis_output"]["sources"] = meta_sources[:5]
        except Exception:
            pass

        # **關鍵修正**：將字典轉換為 JSON 字串，這是 Runner.run() 期望的格式
        input_text = json.dumps(analysis_data, ensure_ascii=False, indent=2)

        # 執行 SDK Agent
        try:
            result = await Runner.run(self.sdk_agent, input=input_text)
            logger.info(f"Evaluate Agent 回覆: {result}")
        except Exception as e:
            logger.error(f"執行 Evaluate Agent 時發生錯誤: {e}")
            return EvaluationResult(
                final_answer="抱歉，評估您的問題時發生錯誤，請稍後再試。",
                sources=[],
                confidence=0.0,
                status=self._fallback_status(),
                metadata={"error": str(e), "sdk_result": False},
            )

        # 解析結構化輸出（具備自我修復）
        output = self._safe_parse_output(result)
        if output is None:
            logger.error("解析 Evaluate 輸出失敗，回傳安全預設值。")
            return EvaluationResult(
                final_answer="無法解析模型輸出。",
                sources=[],
                confidence=0.0,
                status=self._fallback_status(),
                metadata={
                    "error": "failed_to_parse_output",
                    "raw_output": getattr(result, "output", None),
                },
            )

        # 狀態映射為 AgentDecision
        status_enum = self._map_status_to_agent_decision(output.status)

        # metadata 合併（補上 analysis 原始信心與原問題）
        result_metadata: Dict[str, JsonValue] = {}
        if isinstance(output.metadata, dict):
            result_metadata.update(output.metadata)
        result_metadata.setdefault("sdk_result", True)
        result_metadata.setdefault("original_question", getattr(analysis, "query", ""))
        result_metadata.setdefault("analysis_confidence", analysis.confidence)

        # sources 正常化為字串列表（EvaluationResult 期望 List[str]）
        sources = []
        if isinstance(output.sources, list):
            for source in output.sources:
                if isinstance(source, str):
                    sources.append(source)
                elif isinstance(source, dict):
                    # 從字典中提取 id 或其他識別字段
                    source_id = source.get("id") or source.get("doc_id") or str(source)
                    sources.append(source_id)
                else:
                    sources.append(str(source))

        return EvaluationResult(
            final_answer=output.final_answer,
            sources=sources,
            confidence=output.confidence,
            status=status_enum,
            metadata=result_metadata,
        )
