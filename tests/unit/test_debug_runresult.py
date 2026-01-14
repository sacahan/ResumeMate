#!/usr/bin/env python
"""Test with detailed debugging to identify RunResult structure."""

import asyncio
import logging
from unittest.mock import MagicMock, patch
from src.backend.infographics import InfographicAssistantAgent

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)


async def test_with_debug():
    """Test with detailed debug output."""
    print("=" * 60)
    print("Detailed RunResult Structure Test")
    print("=" * 60 + "\n")

    # Create a realistic mock RunResult
    mock_result = MagicMock()
    mock_result.__class__.__name__ = "RunResult"

    # Set the output attribute to contain the actual data
    mock_result.output = {
        "title_en": "AI Leverage Effect",
        "suggested_tags": ["AI", "Design Pattern"],
    }

    agent = InfographicAssistantAgent(existing_tags=["AI", "Architecture"])

    with patch("src.backend.infographics.ai_assistant.Runner.run") as mock_runner:
        mock_runner.return_value = mock_result

        try:
            print("📝 Testing with Chinese title: 'AI 的槓桿效應'\n")
            result = await agent.suggest_metadata("AI 的槓桿效應")

            print("✅ SUCCESS!")
            print(f"   English title: {result.title_en}")
            print(f"   Suggested tags: {result.suggested_tags}")
            print(f"   Type: {type(result).__name__}\n")

            assert result.title_en == "AI Leverage Effect"
            assert result.suggested_tags == ["AI", "Design Pattern"]
            print("✅ All assertions passed!\n")

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            print(f"   Error type: {type(e).__name__}\n")
            import traceback

            traceback.print_exc()

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_with_debug())
