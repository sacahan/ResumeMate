#!/usr/bin/env python
"""Quick integration test for the infographics AI assistant."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.backend.cms import InfographicAssistantAgent


async def test_ai_assistant():
    """Test the AI assistant with sample data."""
    print("🚀 Testing Infographic AI Assistant\n")

    # Test with existing tags
    existing_tags = ["Architecture", "AI", "CICD", "Design Pattern", "Multi Skills"]

    print(f"📌 Existing tags: {', '.join(existing_tags)}\n")

    agent = InfographicAssistantAgent(existing_tags=existing_tags)

    # Test cases
    test_titles = [
        "導入Jenkins協助CI/CD自動化",
        "Tai-Builder Core 系統架構",
        "具備多技能的單智能體失效時機",
    ]

    for title_zh in test_titles:
        print(f"📝 Input (Chinese): {title_zh}")
        try:
            result = await agent.suggest_metadata(title_zh)
            print(f"✅ English Title: {result.title_en}")
            print(f"✅ Suggested Tags: {', '.join(result.suggested_tags)}")
            print(f"✅ Tag Count: {len(result.suggested_tags)}/3")
            assert 1 <= len(result.suggested_tags) <= 3, "Tag count out of range"
            print("✅ Validation passed\n")
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")


if __name__ == "__main__":
    print("=" * 60)
    asyncio.run(test_ai_assistant())
    print("=" * 60)
    print("✨ All tests completed!")
