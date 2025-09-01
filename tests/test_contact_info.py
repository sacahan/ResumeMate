#!/usr/bin/env python3
"""測試聯絡資訊功能的簡單腳本"""

import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from backend.models import Question
from backend import ResumeMateProcessor


async def test_contact_questions():
    """測試聯絡資訊相關問題"""
    print("正在初始化 ResumeMateProcessor...")
    processor = ResumeMateProcessor()

    contact_questions = [
        "如何聯絡你？",
        "你的email是什麼？",
        "我可以怎麼聯絡你？",
        "你的聯絡資訊",
        "請提供你的聯絡方式",
    ]

    print("\n開始測試聯絡資訊相關問題:")
    print("=" * 60)

    for i, q_text in enumerate(contact_questions, 1):
        print(f"\n{i}. 測試問題: {q_text}")
        print("-" * 40)

        try:
            question = Question(text=q_text)
            response = await processor.process_question(question)

            print(f"回答: {response.answer}")
            print(f"信心度: {response.confidence:.2f}")
            print(f"狀態: {response.metadata.get('status', 'N/A')}")

            # 檢查是否包含聯絡資訊
            if "韓世翔" in response.answer and "sacahan@gmail.com" in response.answer:
                print("✅ 成功提供聯絡資訊")
            else:
                print("❌ 未提供完整聯絡資訊")

        except Exception as e:
            print(f"❌ 測試失敗: {e}")

        print()


if __name__ == "__main__":
    asyncio.run(test_contact_questions())
