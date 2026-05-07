#!/usr/bin/env python3
"""ResumeMate 效能測試腳本"""

import asyncio
import time
import statistics
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from src.backend.models import Question
from src.backend.processor import ResumeMateProcessor


async def measure_response_time(processor, question_text):
    """測量單一問題的回應時間"""
    start_time = time.time()

    question = Question(text=question_text)
    response = await processor.process_question(question)

    end_time = time.time()
    response_time = end_time - start_time

    return {
        "question": question_text,
        "response_time": response_time,
        "answer_length": len(response.answer),
        "confidence": response.confidence,
        "sources_count": len(response.sources),
    }


async def run_performance_tests():
    """執行效能測試"""
    print("🚀 ResumeMate 效能測試開始")
    print("=" * 60)

    # 初始化處理器
    print("正在初始化處理器...")
    processor = ResumeMateProcessor()

    # 測試問題集
    test_questions = [
        "介紹一下自己",
        "你有什麼技能？",
        "你的工作經驗如何？",
        "告訴我你的專案經歷",
        "你會什麼程式語言？",
        "如何聯絡你？",
        "你的教育背景是什麼？",
        "你有什麼專業能力？",
        "描述一下你的職業規劃",
        "你最擅長什麼技術？",
    ]

    print(f"測試問題數量: {len(test_questions)}")
    print("開始測試...\n")

    # 執行測試
    results = []
    for i, question in enumerate(test_questions, 1):
        print(f"[{i}/{len(test_questions)}] 測試: {question}")

        try:
            result = await measure_response_time(processor, question)
            results.append(result)

            print(f"  ⏱️  回應時間: {result['response_time']:.2f}s")
            print(f"  📝 回答長度: {result['answer_length']} 字元")
            print(f"  🎯 信心分數: {result['confidence']:.3f}")
            print(f"  📚 來源數量: {result['sources_count']}")
            print()

        except Exception as e:
            print(f"  ❌ 測試失敗: {e}")
            print()
            continue

    # 統計分析
    if results:
        response_times = [r["response_time"] for r in results]
        answer_lengths = [r["answer_length"] for r in results]
        confidences = [r["confidence"] for r in results]

        print("\n📊 效能統計報告")
        print("=" * 60)
        print(f"成功測試數量: {len(results)}/{len(test_questions)}")
        print(f"成功率: {len(results)/len(test_questions)*100:.1f}%")
        print("\n⏱️  回應時間統計:")
        print(f"  平均: {statistics.mean(response_times):.2f}s")
        print(f"  中位數: {statistics.median(response_times):.2f}s")
        print(f"  最短: {min(response_times):.2f}s")
        print(f"  最長: {max(response_times):.2f}s")
        print(f"  標準差: {statistics.stdev(response_times):.2f}s")

        print("\n📝 回答品質統計:")
        print(f"  平均回答長度: {statistics.mean(answer_lengths):.0f} 字元")
        print(f"  平均信心分數: {statistics.mean(confidences):.3f}")

        # 效能分級
        avg_time = statistics.mean(response_times)
        if avg_time < 3.0:
            grade = "🏆 優秀"
        elif avg_time < 5.0:
            grade = "✅ 良好"
        elif avg_time < 8.0:
            grade = "⚠️ 普通"
        else:
            grade = "❌ 需要改善"

        print(f"\n🎯 整體效能評級: {grade}")
        print(f"   平均回應時間: {avg_time:.2f}s")

        # 檢查是否有異常慢的回應
        slow_threshold = avg_time + 2 * statistics.stdev(response_times)
        slow_queries = [r for r in results if r["response_time"] > slow_threshold]

        if slow_queries:
            print(f"\n⚠️  異常慢回應 (>{slow_threshold:.2f}s):")
            for query in slow_queries:
                print(f"  - {query['question']}: {query['response_time']:.2f}s")

    print("\n✅ 效能測試完成")


if __name__ == "__main__":
    asyncio.run(run_performance_tests())
