"""Usage examples for the Infographic AI Assistant."""

import asyncio
from src.backend.cms import InfographicAssistantAgent


async def example_basic_usage():
    """基本使用示例."""
    print("=" * 60)
    print("範例 1: 基本使用")
    print("=" * 60)

    # 建立 AI 代理
    existing_tags = ["Architecture", "AI", "CICD", "Design Pattern"]
    agent = InfographicAssistantAgent(existing_tags=existing_tags)

    # 取得建議
    result = await agent.suggest_metadata("導入Jenkins協助CI/CD自動化")

    print("輸入中文標題: 導入Jenkins協助CI/CD自動化")
    print(f"推薦英文標題: {result.title_en}")
    print(f"推薦標籤: {', '.join(result.suggested_tags)}")
    print()


async def example_with_custom_tags():
    """使用自訂標籤的範例."""
    print("=" * 60)
    print("範例 2: 使用自訂標籤列表")
    print("=" * 60)

    # 使用自訂標籤初始化代理
    custom_tags = ["Machine Learning", "Backend", "DevOps", "Microservices"]
    agent = InfographicAssistantAgent(existing_tags=custom_tags)

    title_zh = "實現高效能微服務架構"
    result = await agent.suggest_metadata(title_zh)

    print(f"自訂標籤列表: {', '.join(custom_tags)}")
    print(f"輸入中文標題: {title_zh}")
    print(f"推薦英文標題: {result.title_en}")
    print(f"推薦標籤: {', '.join(result.suggested_tags)}")
    print()


async def example_error_handling():
    """錯誤處理示例."""
    print("=" * 60)
    print("範例 3: 錯誤處理")
    print("=" * 60)

    agent = InfographicAssistantAgent()

    # 嘗試用空標題
    test_cases = ["", "   ", None]

    for test_input in test_cases:
        try:
            result = await agent.suggest_metadata(test_input)
            print(f"成功: {result}")
        except ValueError as e:
            print(f"✅ 預期錯誤 (輸入: {repr(test_input)}): {str(e)}")
    print()


async def example_multiple_titles():
    """批量處理多個標題的範例."""
    print("=" * 60)
    print("範例 4: 批量處理")
    print("=" * 60)

    agent = InfographicAssistantAgent(
        existing_tags=["Architecture", "AI", "CICD", "Design Pattern"]
    )

    titles = [
        "導入Jenkins協助CI/CD自動化",
        "Tai-Builder Core 系統架構",
        "具備多技能的單智能體失效時機",
    ]

    for title_zh in titles:
        try:
            result = await agent.suggest_metadata(title_zh)
            print(f"\n📝 {title_zh}")
            print(f"   → 英文: {result.title_en}")
            print(f"   → 標籤: {', '.join(result.suggested_tags)}")
        except Exception as e:
            print(f"\n❌ {title_zh}: {str(e)}")

    print()


async def main():
    """Run all examples."""
    try:
        await example_basic_usage()
        await example_with_custom_tags()
        await example_error_handling()
        await example_multiple_titles()

        print("=" * 60)
        print("✨ 所有範例完成！")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 執行範例時出錯: {str(e)}")
        print("\n💡 提示: 確保已設置 GITHUB_COPILOT_TOKEN 環境變數")


if __name__ == "__main__":
    asyncio.run(main())
