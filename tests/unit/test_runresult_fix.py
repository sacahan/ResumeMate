#!/usr/bin/env python
"""Test to verify the AI assistant can handle RunResult objects."""

import asyncio
from unittest.mock import MagicMock, patch
from src.backend.infographics import InfographicAssistantAgent


async def test_runresult_handling():
    """Test that the agent correctly handles RunResult output."""
    print("🧪 Testing RunResult handling...\n")

    # Create a mock RunResult object with proper dict output
    mock_suggestion = {"title_en": "Test Title", "suggested_tags": ["Tag1", "Tag2"]}

    mock_runresult = MagicMock()
    mock_runresult.output = mock_suggestion
    # Also try setting final_answer in case it's accessed first
    type(mock_runresult).final_answer = MagicMock(return_value=mock_suggestion)

    agent = InfographicAssistantAgent(existing_tags=["Tag1", "Tag2", "Tag3"])

    # Mock the Runner.run method to return our mock
    with patch("src.backend.infographics.ai_assistant.Runner.run") as mock_runner:
        # Configure mock to return our RunResult
        mock_runner.return_value = mock_runresult

        try:
            result = await agent.suggest_metadata("測試標題")
            print("✅ Successfully processed RunResult")
            print(f"   English title: {result.title_en}")
            print(f"   Suggested tags: {result.suggested_tags}")
            assert result.title_en == "Test Title"
            assert result.suggested_tags == ["Tag1", "Tag2"]
            print("✅ Output parsed correctly!\n")
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")


async def test_dict_output_handling():
    """Test that the agent correctly handles dict output."""
    print("🧪 Testing dict output handling...\n")

    # Create a mock RunResult with dict output
    mock_suggestion = {"title_en": "Dict Title", "suggested_tags": ["AI"]}
    mock_runresult = MagicMock()
    mock_runresult.output = mock_suggestion

    agent = InfographicAssistantAgent()

    with patch("src.backend.infographics.ai_assistant.Runner.run") as mock_runner:
        mock_runner.return_value = mock_runresult

        try:
            result = await agent.suggest_metadata("測試")
            print("✅ Successfully processed dict output")
            print(f"   English title: {result.title_en}")
            print(f"   Suggested tags: {result.suggested_tags}")
            print("✅ Dict output handled correctly!\n")
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("RunResult Output Handling Tests")
    print("=" * 60 + "\n")

    await test_runresult_handling()
    await test_dict_output_handling()

    print("=" * 60)
    print("✨ All RunResult handling tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
