"""Optional adapter to integrate existing Analysis/Evaluate agents with
the OpenAI Agents Python SDK when it's installed.

This adapter is intentionally optional: if the `agents` package is not
available the adapter sets `available = False` and the rest of the code
falls back to the existing in-repo agent classes.
"""

# 以下檔案提供一個可選的 bridge，當 `openai-agents-python` SDK
# 可用時，將現有的 RAG 工具與專案內的 agent 邏輯包裝成 SDK 的
# Agent / Tool 介面。若 SDK 不存在，adapter 會保持不可用並讓
# 專案繼續使用原生的 AnalysisAgent 與 EvaluateAgent。

from typing import Any
import logging

logger = logging.getLogger(__name__)

# 記錄：模組層級的 logger，可被外部配置（例如在主程式或測試時設定 log level）


class OpenAIAgentsAdapter:
    """Adapter that exposes a simple async `run(question_text)` when the
    OpenAI Agents SDK is available.

    It registers a small `rag_search` function tool that calls the
    existing `RAGTools` implementation. The adapter creates two
    Agent instances (Analysis Agent and Evaluate Agent) and wires a
    handoff from analysis -> evaluate.
    """

    def __init__(self, rag_tools: Any):
        # 可用性旗標，預設為不可用；當成功匯入 SDK 並建立 agent 後會設為 True
        self.available = False
        # 若初始化失敗，可將例外存於此方便外部檢查
        self.error = None
        # 注入的 RAGTools 實例（專案既有實作）
        self.rag_tools = rag_tools

        # 直接匯入 OpenAI Agents SDK；此專案已在 pyproject.toml 中新增依賴。
        try:
            from agents import Agent, Runner, function_tool, handoff
            from agents.extensions.handoff_prompt import (
                prompt_with_handoff_instructions,
            )

            # 將匯入的 SDK 成員綁定為物件屬性，方便後續使用
            self.Agent = Agent
            self.Runner = Runner
            self.function_tool = function_tool
            self.handoff = handoff
            self.prompt_with_handoff_instructions = prompt_with_handoff_instructions
        except Exception as e:
            # 若匯入失敗則直接拋出 ImportError，以便開發者在安裝依賴時能看到明確錯誤
            logger.error("Failed to import OpenAI Agents SDK: %s", e)
            raise

        # 將現有的 RAGTools 封裝成 SDK 的 function tool；這樣 agent 可以直接
        # 以 tool 的方式呼叫檢索功能，符合 SDK 的設計模式。
        @self.function_tool
        def rag_search_tool(query: str, top_k: int = 5):
            """Tool wrapper around RAGTools.rag_search returning simple dicts.

            注意：此函式只做同步轉發，並回傳簡化的 dict 結構，方便 SDK 的
            LLM 端使用與顯示。
            """
            results = self.rag_tools.rag_search(query, top_k=top_k)
            # 將 SearchResult 物件轉成字典列表，避免直接傳遞自定義型別
            return [
                {
                    "doc_id": r.doc_id,
                    "score": r.score,
                    "excerpt": r.excerpt,
                    "metadata": r.metadata,
                }
                for r in results
            ]

        # 建立 Evaluate Agent（SDK 版）；目前僅提供簡短的 instructions，
        # 實際評估邏輯仍建議在本專案內部以 EvaluateAgent 實作並保留 fallback。
        evaluate_agent = self.Agent(
            name="Evaluate Agent",
            instructions=(
                "Evaluate the draft answer provided by the analysis agent. "
                "Return a final answer, a list of source ids, a confidence score, "
                "and a status."
            ),
        )

        # 使用 helper 生成包含 handoff 提示的 instruction，讓 Analysis Agent 在需要時
        # 可將工作交給 Evaluate Agent（handoff 在 SDK 內會以工具的方式呈現）。
        analysis_instructions = self.prompt_with_handoff_instructions(
            "Analyze the user's question. Use the tool `rag_search` to retrieve "
            "relevant documents and produce a draft answer. If needed, handoff "
            "to the Evaluate Agent."
        )

        # 建立 Analysis Agent（SDK 版），並將 rag_search_tool 當成工具注入，同時
        # 設定 handoff 使其可將工作轉交給 evaluate_agent。
        analysis_agent = self.Agent(
            name="Analysis Agent",
            instructions=analysis_instructions,
            tools=[rag_search_tool],
            handoffs=[self.handoff(evaluate_agent)],
        )

        # 將建立的 agent 與 tool 存到物件屬性，並標記 adapter 可用
        self.analysis_agent = analysis_agent
        self.evaluate_agent = evaluate_agent
        self.rag_search_tool = rag_search_tool
        self.available = True

    async def run(self, question_text: str):
        """Run the analysis agent via the SDK Runner and return the SDK result.

        The result is returned as-is from the SDK; caller should inspect
        `result.final_output` or other SDK fields.
        """
        # 若 adapter 不可用則拋出錯誤，呼叫端應該要能處理這個情況並回退
        if not self.available:
            raise RuntimeError("OpenAI Agents SDK adapter not available")

        # 使用 Runner 執行 Analysis Agent，Runner 會處理 tool calls 與 handoffs
        result = await self.Runner.run(self.analysis_agent, input=question_text)
        # 直接回傳 SDK 的結果，呼叫方可依需求解析 result.final_output 或其他欄位
        return result
