#!/usr/bin/env python3
"""ResumeMate 使用者體驗測試腳本"""

import asyncio
import sys
import os
from typing import List, Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from backend.models import Question
from backend.processor import ResumeMateProcessor


class UXTestRunner:
    """UX測試執行器"""

    def __init__(self):
        self.processor = ResumeMateProcessor()
        self.test_results = []

    async def test_common_questions(self) -> Dict[str, Any]:
        """測試常見問題的使用者體驗"""
        print("📝 測試常見履歷問題...")

        common_questions = [
            ("自我介紹", "介紹一下自己"),
            ("技能查詢", "你有什麼技能？"),
            ("工作經驗", "你的工作經驗如何？"),
            ("專案經歷", "告訴我你做過的專案"),
            ("聯絡方式", "如何聯絡你？"),
            ("教育背景", "你的學歷是什麼？"),
        ]

        results = []
        for category, question in common_questions:
            print(f"  測試 [{category}]: {question}")

            q = Question(text=question)
            response = await self.processor.process_question(q)

            # 評估回答品質
            quality_score = self._evaluate_answer_quality(response.answer)

            result = {
                "category": category,
                "question": question,
                "answer_length": len(response.answer),
                "confidence": response.confidence,
                "quality_score": quality_score,
                "sources_count": len(response.sources),
                "has_action": response.action is not None,
            }

            results.append(result)
            print(
                f"    ✅ 回答長度: {result['answer_length']}, 信心: {result['confidence']:.3f}, 品質: {result['quality_score']:.2f}"
            )

        return {
            "test_name": "common_questions",
            "results": results,
            "avg_confidence": sum(r["confidence"] for r in results) / len(results),
            "avg_quality": sum(r["quality_score"] for r in results) / len(results),
        }

    async def test_edge_cases(self) -> Dict[str, Any]:
        """測試邊界情況"""
        print("🔍 測試邊界情況...")

        edge_cases = [
            ("空問題", ""),
            ("超短問題", "你好"),
            ("重複問題", "你你你是是誰誰？"),
            ("混合語言", "Hello, 你好嗎？ How are you?"),
            ("非履歷相關", "今天天氣如何？"),
            ("模糊問題", "那個那個...嗯..."),
        ]

        results = []
        for category, question in edge_cases:
            print(f"  測試 [{category}]: '{question}'")

            try:
                q = Question(text=question)
                response = await self.processor.process_question(q)

                result = {
                    "category": category,
                    "question": question,
                    "success": True,
                    "answer_length": len(response.answer),
                    "confidence": response.confidence,
                    "has_graceful_handling": self._check_graceful_handling(
                        response.answer
                    ),
                }

                print(f"    ✅ 處理成功, 信心: {result['confidence']:.3f}")

            except Exception as e:
                result = {
                    "category": category,
                    "question": question,
                    "success": False,
                    "error": str(e),
                    "has_graceful_handling": False,
                }
                print(f"    ❌ 處理失敗: {e}")

            results.append(result)

        success_rate = sum(1 for r in results if r["success"]) / len(results)

        return {
            "test_name": "edge_cases",
            "results": results,
            "success_rate": success_rate,
        }

    async def test_response_consistency(self) -> Dict[str, Any]:
        """測試回應一致性"""
        print("🔄 測試回應一致性...")

        test_question = "介紹一下你自己"
        responses = []

        # 多次詢問同一問題
        for i in range(3):
            print(f"  第 {i+1} 次測試...")
            q = Question(text=test_question)
            response = await self.processor.process_question(q)
            responses.append(response)

        # 分析一致性
        confidences = [r.confidence for r in responses]
        answer_lengths = [len(r.answer) for r in responses]

        confidence_variance = self._calculate_variance(confidences)
        length_variance = self._calculate_variance(answer_lengths)

        return {
            "test_name": "response_consistency",
            "responses_count": len(responses),
            "confidence_variance": confidence_variance,
            "length_variance": length_variance,
            "avg_confidence": sum(confidences) / len(confidences),
            "avg_length": sum(answer_lengths) / len(answer_lengths),
        }

    def _evaluate_answer_quality(self, answer: str) -> float:
        """評估回答品質（簡化版本）"""
        score = 0.0

        # 長度檢查 (20%)
        if len(answer) > 100:
            score += 0.2
        elif len(answer) > 50:
            score += 0.1

        # 內容完整性檢查 (30%)
        keywords = ["韓世翔", "技能", "經驗", "專案", "工作", "Python", "AI"]
        found_keywords = sum(1 for kw in keywords if kw in answer)
        score += (found_keywords / len(keywords)) * 0.3

        # 專業性檢查 (25%)
        professional_terms = ["開發", "技術", "系統", "設計", "實作", "優化"]
        found_terms = sum(1 for term in professional_terms if term in answer)
        score += (found_terms / len(professional_terms)) * 0.25

        # 結構性檢查 (25%)
        if "。" in answer or "，" in answer:  # 有標點符號
            score += 0.15
        if len(answer.split()) > 10:  # 有足夠的詞彙
            score += 0.1

        return min(score, 1.0)

    def _check_graceful_handling(self, answer: str) -> bool:
        """檢查是否有優雅的錯誤處理"""
        graceful_indicators = ["很抱歉", "無法", "不清楚", "請", "可以", "建議", "幫助"]
        return any(indicator in answer for indicator in graceful_indicators)

    def _calculate_variance(self, values: List[float]) -> float:
        """計算變異數"""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance

    async def run_all_tests(self):
        """執行所有UX測試"""
        print("🚀 ResumeMate UX 測試開始")
        print("=" * 60)

        print("正在初始化...")

        # 執行各項測試
        common_test = await self.test_common_questions()
        print()

        edge_test = await self.test_edge_cases()
        print()

        consistency_test = await self.test_response_consistency()
        print()

        # 整合結果
        print("📊 UX 測試報告")
        print("=" * 60)

        print("📝 常見問題測試:")
        print(f"  平均信心分數: {common_test['avg_confidence']:.3f}")
        print(f"  平均品質分數: {common_test['avg_quality']:.3f}")

        print("\n🔍 邊界情況測試:")
        print(f"  成功處理率: {edge_test['success_rate']*100:.1f}%")

        print("\n🔄 回應一致性測試:")
        print(f"  信心分數變異數: {consistency_test['confidence_variance']:.4f}")
        print(f"  回答長度變異數: {consistency_test['length_variance']:.1f}")

        # 整體評級
        overall_score = (
            common_test["avg_confidence"] * 0.4
            + common_test["avg_quality"] * 0.3
            + edge_test["success_rate"] * 0.2
            + (1 - min(consistency_test["confidence_variance"], 1.0)) * 0.1
        )

        if overall_score >= 0.8:
            grade = "🏆 優秀"
        elif overall_score >= 0.7:
            grade = "✅ 良好"
        elif overall_score >= 0.6:
            grade = "⚠️ 普通"
        else:
            grade = "❌ 需要改善"

        print(f"\n🎯 整體UX評級: {grade}")
        print(f"   綜合分數: {overall_score:.3f}")

        print("\n✅ UX測試完成")

        return {
            "common_questions": common_test,
            "edge_cases": edge_test,
            "consistency": consistency_test,
            "overall_score": overall_score,
            "grade": grade,
        }


async def main():
    """主函數"""
    tester = UXTestRunner()
    results = await tester.run_all_tests()
    return results


if __name__ == "__main__":
    asyncio.run(main())
