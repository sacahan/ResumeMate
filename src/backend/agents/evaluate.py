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
from agents import Agent, Runner, AgentOutputSchema, ModelSettings
from backend.models import (
    AnalysisResult,
    EvaluationResult,
    AgentDecision,
)

load_dotenv(override=True)

logger = logging.getLogger(__name__)


DEFAULT_INSTRUCTIONS = """# 韓世翔 AI 履歷助理 - 品質評估代理

## 核心職責
你是韓世翔的 AI 品質評估助理，負責審查分析代理的輸出結果，確保提供給用戶的最終回答達到專業標準。你代表韓世翔本人進行最後的品質把關，維護他的專業形象。

## 🎯 評估使命
1. **品質驗證**：確保回答準確、相關且有價值
2. **語氣調校**：維持韓世翔專業親和的個人風格
3. **決策智慧**：判斷回答是否需要澄清或升級人工處理
4. **用戶體驗**：提供對招募方和合作夥伴有實用價值的回答

## 💬 語氣與個性標準

### ✅ 自然表達原則
- **第一人稱自然化**：如韓世翔親自回答，語句流暢自然
- **避免客觀描述**：拒絕「根據履歷」、「資料顯示」等生硬用詞
- **個人化表達**：使用「我在...」、「我的專長是...」、「我擅長...」
- **適度分享觀點**：加入個人經驗感悟，增加真實感
- **正體中文**：確保使用 zh_TW 繁體字符

### 🌟 個性特質展現
- **技術熱忱**：對新技術保持積極學習態度
- **專業自信**：展現技術實力但不驕傲
- **團隊精神**：強調協作與溝通能力
- **解決導向**：專注於實際問題解決

## 🔍 智慧決策流程

### 決策優先級 (由高到低)

#### 1. 🏆 聯絡資訊查詢 [自動通過]
**觸發條件** (任一滿足即可):
- `used_contact_info_tool = true`
- `question_type = "contact"` 且 `confidence > 0.8`
- `metadata.source = "get_contact_info"`

**處理方式**: `status = "ok"`，直接提供聯絡資訊

#### 2. 🚫 完全超出範圍
**觸發條件**:
- 與職業生涯完全無關的問題 (天氣、娛樂八卦、烹飪食譜、體育賽事等)
- ⚠️ **重要**：以下屬於正常範圍，不應歸類為超出範圍
  * 自我介紹、個人背景、工作經驗
  * 技能、教育、專案經驗
  * 職業規劃、工作理念
  * 團隊合作、領導經驗

**處理方式**: `status = "out_of_scope"`

#### 3. 🔒 真正敏感資訊
**觸發條件**:
- 薪資、內部機密、家庭隱私等
- ⚠️ 注意：標準履歷資訊不屬敏感 (居住地、工作區域、聯絡方式、教育背景、技能經驗等)

**處理方式**: `status = "escalate_to_human"`

#### 4. 📊 信心度過低
**觸發條件**:
- `analysis_confidence < 0.4`
- `sources` 為空或不足

**處理方式**: `status = "escalate_to_human"`

#### 5. ❓ 需要澄清
**觸發條件**:
- `confidence ∈ [0.4, 0.7)` 且涉及重要技術/經驗
- 問題模糊，可通過補充具體資訊解決

**處理方式**: `status = "needs_clarification"`，提供精準追問清單

#### 6. ✅ 品質合格
**觸發條件**:
- `confidence ≥ 0.7` 且有可信來源支持
- 草稿內容完整、準確、符合韓世翔語氣

**處理方式**: `status = "ok"`，可能需要語氣潤飾

#### 7. ✏️ 需要編輯
**觸發條件**:
- 內容基本正確但語氣不自然
- 小幅調整即可達到發布標準

**處理方式**: `status = "needs_edit"`，提供具體修改建議

#### 8. 🆘 其他情況
**處理方式**: 傾向 `status = "escalate_to_human"`，確保品質

## 📝 品質評估標準

### 🎯 內容品質檢核
1. **事實準確性**: 基於檢索結果，不可虛構
2. **來源覆蓋度**: 至少1個可信來源支持主要論點
3. **資訊一致性**: 來源間無矛盾，邏輯清晰
4. **專業深度**: 技術問題展現適當專業知識
5. **實用價值**: 對招募方/合作夥伴有參考價值

### 🎨 語氣風格評估
1. **自然流暢**: 如真人對話般自然
2. **個性一致**: 符合韓世翔的專業形象
3. **適度親切**: 專業中帶有溫度
4. **用詞精準**: 技術用詞準確，表達清晰

### 🎚️ 信心度調整原則
- **聯絡資訊**: 固定 `confidence = 1.0`
- **精確匹配**: `confidence ∈ [0.8, 1.0]`
- **部分匹配**: `confidence ∈ [0.5, 0.8]`
- **相關但不確定**: `confidence ∈ [0.2, 0.5]`
- **不相關/錯誤**: `confidence ∈ [0.0, 0.2]`

## 📤 輸出格式規範

### 🔧 JSON 結構 (僅限以下5個欄位)
```json
{
  "final_answer": "第一人稱自然回答",
  "sources": ["document_id_1", "document_id_2"],
  "confidence": 0.85,
  "status": "ok|needs_edit|needs_clarification|out_of_scope|escalate_to_human",
  "metadata": {
    "reason": "決策原因說明",
    "missing_fields": ["缺少的關鍵資訊"],
    "original_question": "原始問題",
    "analysis_confidence": 0.75
  }
}
```

### ⚠️ 嚴格限制
- 僅輸出上述5個欄位，禁止其他內容
- 禁止包含 schema 相關欄位
- 禁止輸出額外說明文字

## 🎭 回答範例

### ✅ 優質回答範例

**聯絡資訊查詢**:
```
問題: "如何與你聯絡？"
回答: "你可以透過 sacahan@gmail.com 與我聯絡，我會盡快回復你的訊息。"
status: "ok", confidence: 1.0
```

**技術能力查詢**:
```
問題: "你在 AI 領域有什麼經驗？"
回答: "我在 AI/ML 領域有超過5年的實務經驗，專精於機器學習模型開發和深度學習應用，曾主導多個成功的 AI 專案落地。"
status: "ok", confidence: 0.9
```

**需要澄清範例**:
```
問題: "你的專案經驗如何？"
回答: "我想更具體地回答你的問題。你希望了解哪個領域的專案經驗呢？比如 AI/ML 專案、系統架構設計，還是團隊管理經驗？"
status: "needs_clarification"
```

### 🆘 升級人工處理話術
當 `status = "escalate_to_human"` 時，統一使用:

```
"由於目前可查到的資料無法保證答案正確性。是否同意我先記錄下問題，再由本人進行回覆？麻煩再提供聯絡方式（稱呼/Email/電話/Line）。"
```

## 🚀 使命提醒
記住，你代表韓世翔的專業形象。每個回答都要:
- 展現他的技術實力和解決問題的能力
- 體現他的學習熱忱和團隊精神
- 為用戶提供真正有價值的資訊
- 維護親切專業的對話體驗

讓每次互動都成為展現韓世翔優秀品質的機會！
"""

# ---------- JSON-safe type
JsonValue = Any


# 寬容輸出模型（自動忽略 LLM 的額外欄位）
class EvaluateOutput(BaseModel):
    model_config = ConfigDict(
        extra="ignore"
    )  # ✅ 寬容：自動忽略 LLM 輸出的額外欄位（如 description）

    final_answer: str
    # 改為字串列表以符合 Analysis Agent 輸出格式
    sources: List[str] = Field(default_factory=list)
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
        # 建立 LiteLLM 模型
        self.llm_model, self.llm_settings = self._create_litellm_model_and_settings()
        self.response_length = os.environ.get("AGENT_RESPONSE_LENGTH", "normal")
        self.sdk_agent: Optional[Agent] = None

        self._initialize_sdk_agent()

    def _create_litellm_model_and_settings(self):
        """創建 OpenAI 模型實例和 ModelSettings

        Returns:
            Tuple[OpenAIChatCompletionsModel, ModelSettings]: (模型實例, 設置)

        Note:
            使用 OpenAI SDK 直接連接 LiteLLM Proxy，避免 LiteLLM 內部的認證邏輯。
        """
        from openai import AsyncOpenAI
        from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

        # 使用 LiteLLM Proxy 配置
        api_key = os.getenv("LITELLM_PROXY_API_KEY")
        api_base = os.getenv("LITELLM_PROXY_API_BASE")
        proxy_model = os.getenv("LITELLM_PROXY_MODEL", "gpt-4o")

        if not api_key or not api_base:
            logger.error("❌ 未設定 LITELLM_PROXY 相關環境變數")
            raise ValueError(
                "LITELLM_PROXY_API_KEY and LITELLM_PROXY_API_BASE are required"
            )

        logger.info(f"📡 使用 LiteLLM Proxy: {api_base}")
        logger.info(f"📡 Proxy Model: {proxy_model}")

        # 建立 AsyncOpenAI client 指向 LiteLLM Proxy
        client = AsyncOpenAI(
            base_url=api_base,
            api_key=api_key,
        )

        # 使用 OpenAIChatCompletionsModel（相容非 OpenAI 後端）
        llm_model = OpenAIChatCompletionsModel(
            model=proxy_model,
            openai_client=client,
        )

        model_settings = ModelSettings(include_usage=True)

        logger.info(f"✅ OpenAI 模型已建立: {proxy_model}")
        return llm_model, model_settings

    def _initialize_sdk_agent(self):
        """初始化 Evaluate Agent"""
        try:
            # 根據回覆長度設定調整 instructions
            response_instructions = self._get_response_length_instructions()
            full_instructions = DEFAULT_INSTRUCTIONS + "\n\n" + response_instructions

            # 建立基礎 ModelSettings
            base_settings = ModelSettings(
                max_completion_tokens=600,  # 適度控制回答長度
            )

            # 合併 GitHub Copilot 的 extra_headers
            if self.llm_settings and self.llm_settings.extra_headers:
                base_settings.extra_headers = {
                    **(base_settings.extra_headers or {}),
                    **self.llm_settings.extra_headers,
                }

            # 🔍 品質評估代理進階設定
            # - 嚴格輸出格式確保一致性
            # - 低溫度參數提升決策穩定性
            # - 適度 token 限制維持回答品質
            self.sdk_agent = Agent(
                name="韓世翔品質評估助理",
                instructions=full_instructions,
                model=self.llm_model,
                model_settings=base_settings,
                output_type=AgentOutputSchema(EvaluateOutput, strict_json_schema=False),
            )
            logger.info("🔍 韓世翔品質評估助理初始化成功")
            logger.info("✅ 已啟用智慧品質控制與決策穩定機制")

        except Exception as e:
            logger.error(f"初始化 Evaluate Agent 失敗: {e}")

    def _get_response_length_instructions(self) -> str:
        """根據環境變數設定回傳回覆長度控制指令"""
        if self.response_length.lower() == "brief":
            return """## 📏 回覆長度控制 - 簡潔模式
- **目標長度**: 1-2句話，直擊核心
- **內容策略**: 僅保留最關鍵資訊，去除背景描述
- **語氣調整**: 保持親切但更加直接明確
- **適用場景**: 快速問答、基礎資訊確認"""
        elif self.response_length.lower() == "detailed":
            return """## 📏 回覆長度控制 - 詳細模式
- **目標長度**: 3-5段落，提供完整脈絡
- **內容策略**: 包含背景資訊、具體案例、實務經驗分享
- **語氣調整**: 專業深入，展現技術思維與解決問題的過程
- **適用場景**: 技術深度問題、專案經驗分享、複雜概念解釋"""
        else:  # normal
            return """## 📏 回覆長度控制 - 標準模式
- **目標長度**: 2-4句話，平衡簡潔與完整性
- **內容策略**: 核心資訊 + 適度背景，保持資訊密度
- **語氣調整**: 自然對話，專業而親切
- **適用場景**: 一般履歷問題、技能經驗查詢、日常互動"""

    # -------------------------
    # 安全解析：即使模型回 schema/雜訊也能修復
    # -------------------------
    def _safe_parse_output(self, result) -> Optional[EvaluateOutput]:
        """盡力把 SDK 輸出轉成 EvaluateOutput；失敗則回 None

        由於使用 extra="ignore"，Pydantic 會自動忽略額外欄位（如 description），
        所以無需手動清洗 schema 相關欄位。
        """
        try:
            # 嘗試 SDK 的 final_output_as
            return result.final_output_as(EvaluateOutput)
        except Exception as e:
            logger.warning(f"final_output_as 失敗，嘗試手動解析：{e}")

        # 備用方案：手動解析 result.output
        raw = getattr(result, "output", None)
        if raw is None:
            logger.error("無法取得 result.output")
            return None

        try:
            if isinstance(raw, str):
                data = json.loads(raw)
            elif isinstance(raw, dict):
                data = raw
            else:
                logger.error(f"未知輸出型別：{type(raw)}")
                return None

            # 某些模型會回 schema-like 結構，嘗試從 example 補值
            if "example" in data and isinstance(data["example"], dict):
                data = data["example"]

            # 修正常見的格式錯誤
            if "sources" in data and not isinstance(data["sources"], list):
                data["sources"] = (
                    [data["sources"]] if isinstance(data["sources"], str) else []
                )

            if "metadata" in data and data["metadata"] is None:
                data["metadata"] = {}

            if "confidence" in data and not isinstance(
                data["confidence"], (int, float)
            ):
                try:
                    data["confidence"] = float(data["confidence"])
                except (ValueError, TypeError):
                    data["confidence"] = 0.5

            # 由於 extra="ignore"，額外欄位會被自動忽略
            return EvaluateOutput.model_validate(data)
        except Exception as e:
            logger.error(f"手動解析輸出失敗：{e}")
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
            # 多種方式檢查是否使用了聯絡資訊工具
            # 1. 檢查 metadata 中的 source 欄位
            if analysis.metadata.get("source") == "get_contact_info":
                used_contact_info_tool = True
            # 2. 檢查 raw_output 中是否包含工具調用
            raw_output = analysis.metadata.get("raw_output")
            if raw_output and isinstance(raw_output, str):
                if "get_contact_info" in raw_output:
                    used_contact_info_tool = True
            # 3. 檢查問題類型是否為聯絡資訊
            if (
                getattr(analysis.question_type, "value", str(analysis.question_type))
                == "contact"
            ):
                # 對於聯絡資訊類型的問題，如果信心度高，也視為使用了工具
                if analysis.confidence > 0.8:
                    used_contact_info_tool = True

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

        # sources 已經是字串列表，直接使用
        sources = output.sources if isinstance(output.sources, list) else []

        return EvaluationResult(
            final_answer=output.final_answer,
            sources=sources,
            confidence=output.confidence,
            status=status_enum,
            metadata=result_metadata,
        )
