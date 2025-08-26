"""簡單的整合測試"""

import sys
import asyncio

sys.path.append("src")

from backend.models import Question
from backend.processor import ResumeMateProcessor


async def test_processor():
    """測試完整的處理流程"""
    processor = ResumeMateProcessor()

    test_questions = [
        "你好",
        "你有什麼技能？",
        "你的工作經驗如何？",
        "如何聯絡你？",
        "今天天氣如何？",
    ]

    for q_text in test_questions:
        print(f"\n🔍 問題: {q_text}")
        print("-" * 50)

        question = Question(text=q_text)
        response = await processor.process_question(question)

        print(f"📝 回答: {response.answer[:200]}...")
        print(f"🎯 信心分數: {response.confidence:.3f}")
        print(f"📚 來源數量: {len(response.sources)}")
        if response.action:
            print(f"🔧 建議動作: {response.action}")


if __name__ == "__main__":
    asyncio.run(test_processor())
