#!/usr/bin/env python
"""Integration test for the complete AI assistant workflow."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.backend.infographics import InfographicAssistantAgent


async def test_complete_workflow():
    """Test the complete AI assistant workflow."""
    print("=" * 60)
    print("AI Assistant Complete Workflow Test")
    print("=" * 60 + "\n")

    # Test with existing tags
    existing_tags = ["Architecture", "AI", "CICD", "Design Pattern", "Multi Skills"]

    print(f"📌 Existing tags: {', '.join(existing_tags)}\n")

    agent = InfographicAssistantAgent(existing_tags=existing_tags)

    # Test cases that should work
    test_titles = [
        "AI 的槓桿效應",
        "導入Jenkins協助CI/CD自動化",
        "系統架構設計",
    ]

    print("🧪 Testing with various Chinese titles:\n")

    for title_zh in test_titles:
        print(f"📝 Input: {title_zh}")
        try:
            result = await agent.suggest_metadata(title_zh)
            print(f"✅ English: {result.title_en}")
            print(f"✅ Tags: {', '.join(result.suggested_tags)}")
            print(f"✅ Tag count: {len(result.suggested_tags)}/3")

            # Validate
            assert 1 <= len(result.suggested_tags) <= 3, "Tag count out of range"
            assert isinstance(result.title_en, str), "English title not a string"
            assert result.title_en.strip(), "English title is empty"
            print("✅ Validation passed\n")

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print(f"❌ Error type: {type(e).__name__}\n")

    print("=" * 60)
    print("✨ Workflow test completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_complete_workflow())
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1)
