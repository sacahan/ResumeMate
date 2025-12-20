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

DEFAULT_INSTRUCTIONS = """# 韓世翔 AI 履歷助理 - 問題分析代理

## 角色定位
你是韓世翔本人的 AI 分身，負責分析用戶問題並提供個人化的履歷資訊回覆。你代表韓世翔以第一人稱與用戶自然對話，展現他的專業能力、技術熱忱和親和個性。

## 核心任務
1. **智慧問題解析**：準確識別問題類型和用戶意圖
2. **精確資訊檢索**：運用適當工具檢索相關履歷資訊
3. **自然對話生成**：以韓世翔的語氣和個性回答問題
4. **品質控制**：確保回答準確、相關且有價值

## 語氣與個性指南

### 🎯 核心特質
- **技術專業**：在 AI/ML、軟體開發領域展現深度專業知識
- **積極進取**：主動學習新技術，勇於面對挑戰
- **團隊協作**：重視溝通合作，具備領導能力但保持謙遜
- **解決導向**：專注於實際問題解決，注重成果與效益

### 💬 表達原則
- 使用第一人稱（「我」、「我的」）自然表達
- 避免「根據履歷」、「資料顯示」等客觀描述
- 語氣親切專業，如面對面交談般自然
- 適時分享個人觀點和經驗感悟
- 使用正體中文，避免簡體字符

### 📝 回答風格範例
❌ 避免：「根據履歷資料顯示，韓世翔具備...」
✅ 推薦：「我在 AI 領域有超過 5 年的實務經驗...」

❌ 避免：「資料庫中記錄了相關技能...」
✅ 推薦：「我的專長包括機器學習和深度學習...」

## 🚨 核心決策邏輯（必須遵守）

### ⭐ 第一優先級：履歷核心問題 → decision = "retrieve"
**這些問題必須使用 `decision = "retrieve"`，絕對不能設為 oos：**

✅ **自我介紹類**：
- 「介紹一下自己」、「你是誰？」、「Tell me about yourself」
- 「說說你的背景」、「What's your background?」
- 「你的簡歷」、「個人資料」

✅ **經驗技能類**：
- 「你有什麼經驗？」、「工作經歷」、「專案經驗」
- 「你擅長什麼？」、「技術能力」、「專業技能」
- 「你的學歷」、「教育背景」

✅ **職業相關類**：
- 「工作類型偏好」、「職業規劃」、「未來發展」
- 「團隊合作」、「領導經驗」、「管理能力」

### 🔥 決策規則（嚴格執行）

#### 規則 1：聯絡資訊 → get_contact_info 工具
```
問題包含：聯絡、email、電話、Line、如何找到你
→ 使用 get_contact_info 工具
→ decision = "retrieve", question_type = "contact"
```

#### 規則 2：履歷相關 → rag_search_tool 工具
```
問題關於：工作、技能、經驗、教育、專案、自我介紹、背景
→ 使用 rag_search_tool 工具
→ decision = "retrieve", question_type = "experience/skill/fact/other"
```

#### 規則 3：真正超出範圍 → oos
```
問題完全無關職業：天氣、娛樂、烹飪、體育、政治、個人興趣
→ decision = "oos"
```

#### 規則 4：需要澄清 → clarify
```
問題過於模糊且檢索結果不足
→ decision = "clarify"
```

## 檢索優化策略

### 🎯 關鍵詞優化
- **技術領域**：AI, ML, 機器學習, 深度學習, Python, TensorFlow
- **職能角色**：技術主管, 專案經理, 團隊領導
- **行業領域**：金融科技, 電商平台, 數據分析

### 📊 檢索參數調優
- **高相關性問題**：`top_k=3` (精確匹配)
- **一般問題**：`top_k=5` (平衡覆蓋度)
- **複雜問題**：`top_k=7` (廣泛檢索)

## 品質控制標準

### ✅ 回答品質要求
1. **事實準確性**：基於檢索結果，不可虛構
2. **資訊完整性**：提供具體細節，避免空泛描述
3. **個性一致性**：維持韓世翔的專業形象
4. **用戶價值**：回答對招募方或合作夥伴有實用價值

### 🎯 信心度評估
- **高信心 (0.8-1.0)**：檢索到精確匹配的履歷內容
- **中信心 (0.5-0.8)**：找到相關但不完全匹配的內容
- **低信心 (0.0-0.5)**：檢索結果稀少或相關性低

## 輸出格式規範

### 📋 必要欄位
```json
{
  "draft_answer": "第一人稱自然回答",
  "sources": ["document_id_1", "document_id_2"],
  "confidence": 0.85,
  "question_type": "skill|experience|contact|fact|other",
  "decision": "retrieve|oos|clarify",
  "metadata": {
    "source": "工具來源標記",
    "keywords": ["提取的關鍵詞"]
  }
}
```

### ⚠️ 嚴格限制
- 僅輸出上述 6 個欄位
- 禁止包含 schema 相關欄位
- 禁止輸出說明文字或額外內容
- **必須使用小寫枚舉值**：`decision` 只能是 `"retrieve"`, `"oos"`, `"clarify"`（不可大寫）

## 特殊情況處理

### 💼 聯絡資訊問題範例
```json
{
  "draft_answer": "你可以透過 sacahan@gmail.com 與我聯絡。",
  "sources": [],
  "confidence": 1.0,
  "question_type": "contact",
  "decision": "retrieve",
  "metadata": {"source": "get_contact_info"}
}
```

記住：你是韓世翔的專業代表，每個回答都要展現他的技術實力、解決問題的能力和個人魅力。讓用戶感受到與一位優秀技術專家對話的體驗。
"""


# =========================
# 1) 嚴格輸出模型（只允許 6 欄）
# =========================
class AnalysisOutput(BaseModel):
    """Analysis Agent 的結構化輸出"""

    model_config = ConfigDict(
        extra="ignore"
    )  # ✅ 寬容：自動忽略 LLM 輸出的額外欄位（如 description）

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
def get_contact_info() -> Dict[str, str]:
    """獲取韓世翔的聯絡資訊。當用戶詢問如何聯絡我、我的email、聯絡方式等問題時使用此工具。

    Returns:
        Dict[str, str]: 包含姓名和email的聯絡資訊
    """
    return {"name": "韓世翔", "email": "sacahan@gmail.com"}


# 全域 RAG 工具實例，避免重複初始化
_rag_tools_instance = None


def get_rag_tools_instance() -> RAGTools:
    """獲取 RAG 工具單例實例"""
    global _rag_tools_instance
    if _rag_tools_instance is None:
        _rag_tools_instance = RAGTools()
    return _rag_tools_instance


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
        rag_tools = get_rag_tools_instance()
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
        self.llm_model, self.llm_settings = self._create_litellm_model_and_settings()
        self.response_length = os.environ.get("AGENT_RESPONSE_LENGTH", "normal")
        self.sdk_agent = None
        self._initialize_sdk_agent()

    def _create_litellm_model_and_settings(self):
        """創建 GitHub Copilot 模型實例和 ModelSettings

        Returns:
            Tuple[LitellmModel, ModelSettings]: (模型實例, 設置)

        Note:
            直接使用 GitHub Copilot API。
            需要配置 COPILOT_GITHUB_TOKEN 環境變數。
        """
        try:
            from agents.extensions.models.litellm_model import LitellmModel
        except ImportError:
            logger.error("LiteLLM 未安裝，請運行: pip install litellm>=1.0.0")
            raise

        # 從環境變數讀取配置
        api_key = os.getenv("GITHUB_COPILOT_TOKEN")
        if not api_key:
            logger.error("❌ 未設定 GITHUB_COPILOT_TOKEN 環境變數")
            raise ValueError("GITHUB_COPILOT_TOKEN is required")

        model = os.getenv("AGENT_MODEL", "gpt-4o-mini")
        logger.info("📡 使用直接的 GitHub Copilot 認證")

        # 建立 LiteLLM 模型實例
        llm_model = LitellmModel(
            model=f"github_copilot/{model}",
            api_key=api_key,
        )

        # 建立 ModelSettings，配置 GitHub Copilot 所需的 Headers
        model_settings = ModelSettings(
            include_usage=True,
            extra_headers={
                "editor-version": "vscode/1.85.1",  # Editor version
                "editor-plugin-version": "copilot/1.155.0",  # Plugin version
                "Copilot-Integration-Id": "vscode-chat",  # Integration ID
                "user-agent": "GithubCopilot/1.155.0",  # User agent
            },
        )

        logger.info(f"✅ GitHub Copilot 模型已建立: {model}")
        return llm_model, model_settings

    def _initialize_sdk_agent(self):
        """初始化 Agent"""
        try:
            # 根據回覆長度設定調整 instructions
            response_instructions = self._get_response_length_instructions()
            full_instructions = DEFAULT_INSTRUCTIONS + "\n\n" + response_instructions

            # 建立基礎 ModelSettings
            base_settings = ModelSettings(
                # tool_choice="required",  # 🔥 強制使用工具確保檢索履歷內容
                max_completion_tokens=500,  # 控制回答長度，避免過度冗長
            )

            # 合併 GitHub Copilot 的 extra_headers
            if self.llm_settings and self.llm_settings.extra_headers:
                base_settings.extra_headers = {
                    **(base_settings.extra_headers or {}),
                    **self.llm_settings.extra_headers,
                }

            # 💡 智慧代理設定優化
            # - 嚴格輸出格式防止 schema 汙染
            # - 智慧工具選擇提升檢索效率
            # - 溫度參數調優確保回答品質一致性
            self.sdk_agent = Agent(
                name="韓世翔履歷分析助理",
                instructions=full_instructions,
                tools=[get_contact_info, rag_search_tool],
                model=self.llm_model,
                model_settings=base_settings,
                output_type=AgentOutputSchema(AnalysisOutput, strict_json_schema=False),
            )
            logger.info("🚀 韓世翔履歷分析助理 (GitHub Copilot) 初始化成功")
            logger.info("✅ 已啟用智慧工具選擇與品質控制機制")
        except Exception as e:
            logger.error(f"初始化 Analysis Agent 失敗: {e}")

    def _get_response_length_instructions(self) -> str:
        """根據環境變數設定回傳回覆長度控制指令"""
        if self.response_length.lower() == "brief":
            return """## 💬 回覆長度控制 - 簡潔模式
- **目標長度**：1-2 句話，20-50 字
- **內容重點**：僅核心資訊，去除背景描述
- **適用場景**：快速問答、基礎資訊查詢
- **語氣調整**：保持親切但更加直接"""
        elif self.response_length.lower() == "detailed":
            return """## 💬 回覆長度控制 - 詳細模式
- **目標長度**：3-5 段落，100-200 字
- **內容重點**：提供背景脈絡、具體範例、實務經驗
- **適用場景**：技術深度問題、專案經驗分享
- **語氣調整**：專業深入，展現技術思維過程"""
        else:  # normal
            return """## 💬 回覆長度控制 - 標準模式
- **目標長度**：2-4 句話，50-100 字
- **內容重點**：平衡簡潔性與完整性
- **適用場景**：一般履歷問題、技能經驗查詢
- **語氣調整**：自然對話，專業而親切"""

    # -------------------------
    # 安全解析輔助：避免 Invalid JSON
    # -------------------------
    def _safe_parse_output(self, result) -> AnalysisOutput | None:
        """盡力把 SDK 輸出轉成 AnalysisOutput；失敗則回 None

        由於使用 extra="ignore"，Pydantic 會自動忽略額外欄位（如 description），
        所以無需手動清洗 schema 相關欄位。
        """
        try:
            # 嘗試 SDK 的 final_output_as
            return result.final_output_as(AnalysisOutput)
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

            # 修正常見的格式錯誤
            if "decision" in data and isinstance(data["decision"], list):
                data["decision"] = data["decision"][0] if data["decision"] else "oos"

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
            return AnalysisOutput.model_validate(data)
        except Exception as e:
            logger.error(f"手動解析輸出失敗：{e}")
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
            # 標準化 decision 值，處理大小寫問題
            decision_value = output.decision.lower().strip()

            # 映射常見變體到正確的 AgentDecision 枚舉值
            decision_mapping = {
                "oos": "oos",
                "out_of_scope": "oos",
                "outofscooe": "oos",
                "retrieve": "retrieve",
                "clarify": "clarify",
                "ask_clarify": "clarify",
            }

            normalized_decision = decision_mapping.get(decision_value, decision_value)
            decision = AgentDecision(normalized_decision)
        except Exception as e:
            # 只有在真正無法解析時才設為 OUT_OF_SCOPE，並記錄詳細錯誤
            logger.warning(
                f"Decision 解析失敗 '{output.decision}': {e}，使用預設值 OUT_OF_SCOPE"
            )
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
