"""AI Assistant for infographic title translation and tag suggestion.

Uses OpenAI Agents SDK with LiteLLM to provide intelligent assistance
for translating Chinese titles to English and suggesting appropriate tags.
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

from agents import Agent, AgentOutputSchema, ModelSettings, Runner
from agents.extensions.models.litellm_model import LitellmModel

from .models import TitleTagSuggestion

load_dotenv(override=True)

logger = logging.getLogger(__name__)


class InfographicAssistantAgent:
    """AI assistant for infographic metadata assistance."""

    def __init__(
        self,
        existing_tags: list[str] | None = None,
        model: str | None = None,
        api_key: str | None = None,
    ):
        """Initialize the assistant agent.

        Args:
            existing_tags: List of existing tags to prioritize in suggestions
            model: LLM model name (default: from AGENT_MODEL env var)
            api_key: GitHub Copilot API key (default: from GITHUB_COPILOT_TOKEN env var)
        """
        self.existing_tags = existing_tags or []
        self.llm_model, self.model_settings = self._create_litellm_model_and_settings(
            model=model, api_key=api_key
        )
        self.sdk_agent = self._create_agent()

    def _create_litellm_model_and_settings(
        self, model: str | None = None, api_key: str | None = None
    ) -> tuple[LitellmModel, ModelSettings]:
        """Create LiteLLM model instance and ModelSettings.

        Args:
            model: Model name (default: gpt-4o-mini from env or fallback)
            api_key: GitHub Copilot API key

        Returns:
            Tuple of (LitellmModel, ModelSettings)
        """

        # 使用 LiteLLM Proxy 配置
        api_key = os.getenv("LITELLM_PROXY_API_KEY")
        api_base = os.getenv("LITELLM_PROXY_API_BASE")
        proxy_model = os.getenv("LITELLM_PROXY_MODEL", "github_copilot/gpt-4o")

        # 使用 openai/ 前綴來繞過 LiteLLM 的內建 GitHub Copilot 認證
        # 這樣 LiteLLM 會將請求作為標準 OpenAI 格式發送到 Proxy
        # Proxy 再根據 model name 路由到正確的後端 (GitHub Copilot)
        model = f"openai/{proxy_model}"

        llm_model = LitellmModel(
            model=model,
            api_key=api_key,
            base_url=api_base,
        )

        model_settings = ModelSettings(max_completion_tokens=300, include_usage=True)

        return llm_model, model_settings

    def _create_agent(self) -> Agent:
        """Create the assistant agent.

        Returns:
            Agent instance configured for title translation and tag suggestion
        """
        instructions = self._build_instructions()

        return Agent(
            name="圖表助理",
            instructions=instructions,
            tools=[],  # No tools needed for this task
            model=self.llm_model,
            model_settings=self.model_settings,
            output_type=AgentOutputSchema(TitleTagSuggestion, strict_json_schema=False),
        )

    def _build_instructions(self) -> str:
        """Build the system instructions for the agent.

        Returns:
            System instructions string
        """
        tags_list = (
            ", ".join(self.existing_tags) if self.existing_tags else "無現有標籤"
        )

        return f"""# 圖表元數據助理

## 角色定位
你是專業的圖表整理助理，負責協助使用者將圖表中文標題翻譯為英文，
並根據圖表內容提供適合的分類標籤建議。

## 核心任務
1. **精確翻譯**：將中文標題翻譯成專業、簡潔的英文標題
2. **智慧標籤**：根據中文標題內容推薦 1-3 個適合的分類標籤
3. **優先既有標籤**：優先從現有標籤中選擇，必要時可建議新標籤

## 現有標籤列表（優先使用）
{tags_list}

## 翻譯指南
- 風格：專業、簡潔、易懂
- 保留重點技術名詞或專有名詞
- 避免過度翻譯，直譯往往更好
- 建議長度：3-8 個單詞

## 標籤建議規則
1. **數量**：建議 1-3 個標籤
2. **優先順序**：
   - 優先使用現有標籤列表中的標籤
   - 如有必要，可建議新標籤
3. **格式**：每個標籤大寫，使用英文或 CamelCase
4. **相關性**：只建議與圖表內容相關的標籤

## 回應格式
直接返回 JSON 格式的結果，包含 `title_en` 和 `suggested_tags` 兩個欄位。
不需要任何其他說明文字。

## 範例
輸入中文標題：「導入Jenkins協助CI/CD自動化」
輸出：
{{
  "title_en": "Introducing Jenkins to Enable CI/CD Automation",
  "suggested_tags": ["CICD", "Architecture"]
}}

輸入中文標題：「具備多技能的單智能體失效時機」
輸出：
{{
  "title_en": "When Multi-Skilled Single AI Agent Fails",
  "suggested_tags": ["AI", "Multi Skills", "Design Pattern"]
}}
"""

    async def suggest_metadata(self, title_zh: str) -> TitleTagSuggestion:
        """Generate title and tag suggestions for a Chinese title.

        Args:
            title_zh: Chinese title to process

        Returns:
            TitleTagSuggestion containing English title and tag suggestions

        Raises:
            ValueError: If title_zh is empty or None
            Exception: If Agent execution fails
        """
        if not title_zh or not title_zh.strip():
            raise ValueError("Chinese title cannot be empty")

        try:
            logger.debug(f"Processing title: {title_zh}")

            result = await Runner.run(
                self.sdk_agent,
                input=f"中文標題：{title_zh.strip()}",
            )

            # Log result details for debugging
            logger.debug(f"Result type: {type(result).__name__}")
            logger.debug(f"Result has final_output: {hasattr(result, 'final_output')}")

            # Extract final_output from RunResult
            output = result.final_output

            # Convert to TitleTagSuggestion if needed
            if isinstance(output, TitleTagSuggestion):
                suggestion = output
            elif isinstance(output, dict):
                suggestion = TitleTagSuggestion(**output)
            else:
                raise ValueError(
                    f"Unexpected output type: {type(output).__name__}, "
                    f"expected dict or TitleTagSuggestion. Got: {output}"
                )

            # Validate tag count
            if not (1 <= len(suggestion.suggested_tags) <= 3):
                logger.warning(
                    f"Tag count {len(suggestion.suggested_tags)} out of range 1-3, "
                    f"adjusting to first 3 tags"
                )
                suggestion.suggested_tags = suggestion.suggested_tags[:3]

            logger.info(
                f"Successfully processed title: {title_zh} -> {suggestion.title_en}"
            )
            return suggestion

        except Exception as e:
            logger.error(f"Failed to process title '{title_zh}': {str(e)}")
            raise


async def suggest_infographic_metadata(
    title_zh: str, existing_tags: list[str] | None = None
) -> TitleTagSuggestion | None:
    """Convenience function to get metadata suggestions.

    Args:
        title_zh: Chinese title to process
        existing_tags: List of existing tags to prioritize

    Returns:
        TitleTagSuggestion with suggestions, or None if an error occurs
    """
    try:
        agent = InfographicAssistantAgent(existing_tags=existing_tags)
        return await agent.suggest_metadata(title_zh)
    except Exception as e:
        logger.error(f"Error getting metadata suggestions: {str(e)}")
        return None
