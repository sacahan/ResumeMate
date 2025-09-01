"""
AI 回答品質評估與優化工具

提供多維度的回答品質檢測、優化建議和自動改善機制，
確保韓世翔 AI 履歷助理提供一致且高品質的回答。
"""

import re
import logging
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from openai import OpenAI

logger = logging.getLogger(__name__)


class QualityIssue(Enum):
    """回答品質問題類型"""

    OBJECTIVE_LANGUAGE = "objective_language"  # 客觀描述語言
    LACK_PERSONALITY = "lack_personality"  # 缺乏個性特色
    FACTUAL_INCONSISTENCY = "factual_inconsistency"  # 事實不一致
    TONE_MISMATCH = "tone_mismatch"  # 語氣不符
    LENGTH_INAPPROPRIATE = "length_inappropriate"  # 長度不當
    LACKS_SPECIFICITY = "lacks_specificity"  # 缺乏具體性
    GRAMMAR_ISSUES = "grammar_issues"  # 語法問題


@dataclass
class QualityScore:
    """品質評分結果"""

    overall_score: float  # 總體分數 (0-1)
    personality_score: float  # 個性化分數
    factual_accuracy_score: float  # 事實準確度
    tone_consistency_score: float  # 語氣一致性
    clarity_score: float  # 清晰度分數
    issues: List[QualityIssue]  # 發現的問題
    suggestions: List[str]  # 改善建議
    metadata: Dict[str, Union[str, float]]  # 額外元數據


@dataclass
class OptimizedAnswer:
    """優化後的回答"""

    original_answer: str  # 原始回答
    optimized_answer: str  # 優化後回答
    quality_improvement: float  # 品質提升程度
    changes_made: List[str]  # 執行的改善措施
    confidence: float  # 優化信心度


class AnswerQualityAnalyzer:
    """韓世翔 AI 回答品質分析器"""

    def __init__(self, openai_client: Optional[OpenAI] = None):
        """
        初始化品質分析器

        Args:
            openai_client: OpenAI 客戶端，如果為 None 會自動創建
        """
        self.openai_client = openai_client or OpenAI()

        # 韓世翔個性關鍵詞
        self.personality_keywords = {
            "positive": ["積極", "熱忱", "學習", "挑戰", "創新", "解決", "優化"],
            "professional": ["專業", "經驗", "技術", "實務", "專案", "團隊", "協作"],
            "personal": ["我", "我的", "我在", "我擅長", "我認為", "我曾經"],
        }

        # 避免的客觀描述詞彙
        self.objective_phrases = [
            "根據履歷",
            "履歷顯示",
            "資料顯示",
            "文件記錄",
            "資料庫中",
            "根據資料",
            "檔案顯示",
            "記錄顯示",
            "數據表明",
        ]

        # 品質評估提示詞
        self.quality_prompt_template = """
請評估以下AI回答的品質，特別關注是否符合韓世翔的個人特色：

問題：{question}
回答：{answer}

評估標準：
1. 個性化程度 (0-10)：是否以第一人稱自然表達，展現韓世翔的技術熱忱和專業特質
2. 事實準確度 (0-10)：內容是否基於提供的履歷資訊，無虛構成分
3. 語氣一致性 (0-10)：是否保持專業親切的語氣，符合韓世翔風格
4. 清晰度 (0-10)：表達是否清晰具體，對招募方有實用價值

請回傳JSON格式：
{{
  "personality_score": 分數,
  "factual_accuracy_score": 分數,
  "tone_consistency_score": 分數,
  "clarity_score": 分數,
  "issues": ["發現的問題"],
  "suggestions": ["具體改善建議"]
}}
"""

        # 回答優化提示詞
        self.optimization_prompt_template = """
請優化以下AI回答，使其更符合韓世翔的個人特色：

原始問題：{question}
原始回答：{answer}
品質問題：{issues}
改善建議：{suggestions}

優化要求：
1. 保持第一人稱自然表達，如韓世翔親自回答
2. 展現技術專業性和學習熱忱
3. 語氣親切專業，避免生硬的客觀描述
4. 內容具體有用，對招募方有參考價值
5. 長度適中，重點突出

請回傳優化後的回答（純文字，不要JSON格式）：
"""

    def analyze_quality(self, answer: str, question: str = "") -> QualityScore:
        """
        分析回答品質

        Args:
            answer: 要分析的回答
            question: 原始問題（可選，用於更準確的評估）

        Returns:
            QualityScore: 品質評估結果
        """
        if not answer or not answer.strip():
            return QualityScore(
                overall_score=0.0,
                personality_score=0.0,
                factual_accuracy_score=0.0,
                tone_consistency_score=0.0,
                clarity_score=0.0,
                issues=[QualityIssue.LACKS_SPECIFICITY],
                suggestions=["回答不能為空"],
                metadata={"length": 0},
            )

        try:
            # 使用規則引擎進行初步檢測
            rule_based_score = self._rule_based_analysis(answer, question)

            # 使用 LLM 進行深度品質評估
            llm_score = self._llm_quality_assessment(answer, question)

            # 合併兩種評估結果
            combined_score = self._combine_scores(rule_based_score, llm_score)

            logger.info(f"回答品質分析完成，總分：{combined_score.overall_score:.2f}")
            return combined_score

        except Exception as e:
            logger.error(f"品質分析失敗：{e}")
            # 返回基礎評估結果
            return self._fallback_analysis(answer)

    def _rule_based_analysis(self, answer: str, question: str) -> QualityScore:
        """基於規則的快速品質檢測"""
        issues = []
        suggestions = []

        # 檢測客觀描述語言
        objective_count = sum(
            1 for phrase in self.objective_phrases if phrase in answer
        )
        if objective_count > 0:
            issues.append(QualityIssue.OBJECTIVE_LANGUAGE)
            suggestions.append(f"避免使用客觀描述，發現 {objective_count} 處")

        # 檢測第一人稱使用
        first_person_count = len(re.findall(r"我[的在擅長認為曾經]?", answer))
        personality_score = min(1.0, first_person_count / 3.0)  # 期望至少3次第一人稱

        if first_person_count == 0:
            issues.append(QualityIssue.LACK_PERSONALITY)
            suggestions.append("增加第一人稱表達，如「我」、「我的經驗」等")

        # 檢測長度適當性
        length = len(answer)
        if length < 20:
            issues.append(QualityIssue.LENGTH_INAPPROPRIATE)
            suggestions.append("回答過短，需要提供更多具體資訊")
        elif length > 300:
            issues.append(QualityIssue.LENGTH_INAPPROPRIATE)
            suggestions.append("回答過長，建議精簡至重點")

        # 計算各項分數
        tone_score = 1.0 - (objective_count * 0.2)  # 客觀描述降低語氣分數
        clarity_score = 0.8 if 50 <= length <= 200 else 0.6
        factual_score = 0.8  # 規則無法判斷事實準確性，給予中等分數

        overall_score = (
            personality_score + tone_score + clarity_score + factual_score
        ) / 4

        return QualityScore(
            overall_score=overall_score,
            personality_score=personality_score,
            factual_accuracy_score=factual_score,
            tone_consistency_score=tone_score,
            clarity_score=clarity_score,
            issues=issues,
            suggestions=suggestions,
            metadata={
                "method": "rule_based",
                "length": length,
                "first_person_count": first_person_count,
                "objective_phrases": objective_count,
            },
        )

    def _llm_quality_assessment(self, answer: str, question: str) -> QualityScore:
        """使用 LLM 進行深度品質評估"""
        try:
            prompt = self.quality_prompt_template.format(
                question=question or "未提供問題", answer=answer
            )

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )

            result = response.choices[0].message.content

            # 解析 JSON 回應
            import json

            quality_data = json.loads(result)

            # 轉換分數到 0-1 範圍
            personality_score = quality_data.get("personality_score", 5) / 10.0
            factual_score = quality_data.get("factual_accuracy_score", 5) / 10.0
            tone_score = quality_data.get("tone_consistency_score", 5) / 10.0
            clarity_score = quality_data.get("clarity_score", 5) / 10.0

            overall_score = (
                personality_score + factual_score + tone_score + clarity_score
            ) / 4

            # 轉換問題類型
            issue_mapping = {
                "客觀描述語言": QualityIssue.OBJECTIVE_LANGUAGE,
                "缺乏個性": QualityIssue.LACK_PERSONALITY,
                "語氣不符": QualityIssue.TONE_MISMATCH,
                "事實問題": QualityIssue.FACTUAL_INCONSISTENCY,
                "不夠具體": QualityIssue.LACKS_SPECIFICITY,
            }

            issues = []
            for issue_text in quality_data.get("issues", []):
                for key, value in issue_mapping.items():
                    if key in issue_text:
                        issues.append(value)
                        break

            return QualityScore(
                overall_score=overall_score,
                personality_score=personality_score,
                factual_accuracy_score=factual_score,
                tone_consistency_score=tone_score,
                clarity_score=clarity_score,
                issues=issues,
                suggestions=quality_data.get("suggestions", []),
                metadata={
                    "method": "llm_based",
                    "model": "gpt-4o-mini",
                    "raw_response": result,
                },
            )

        except Exception as e:
            logger.warning(f"LLM 品質評估失敗，使用後備方案：{e}")
            return self._fallback_analysis(answer)

    def _combine_scores(
        self, rule_score: QualityScore, llm_score: QualityScore
    ) -> QualityScore:
        """合併規則引擎和 LLM 的評估結果"""
        # 加權平均（LLM 權重稍高）
        rule_weight = 0.3
        llm_weight = 0.7

        combined_overall = (
            rule_score.overall_score * rule_weight
            + llm_score.overall_score * llm_weight
        )

        combined_personality = (
            rule_score.personality_score * rule_weight
            + llm_score.personality_score * llm_weight
        )

        combined_factual = (
            rule_score.factual_accuracy_score * rule_weight
            + llm_score.factual_accuracy_score * llm_weight
        )

        combined_tone = (
            rule_score.tone_consistency_score * rule_weight
            + llm_score.tone_consistency_score * llm_weight
        )

        combined_clarity = (
            rule_score.clarity_score * rule_weight
            + llm_score.clarity_score * llm_weight
        )

        # 合併問題和建議
        combined_issues = list(set(rule_score.issues + llm_score.issues))
        combined_suggestions = rule_score.suggestions + llm_score.suggestions

        # 合併元數據
        combined_metadata = {**rule_score.metadata, **llm_score.metadata}
        combined_metadata["combination_method"] = "weighted_average"
        combined_metadata["rule_weight"] = rule_weight
        combined_metadata["llm_weight"] = llm_weight

        return QualityScore(
            overall_score=combined_overall,
            personality_score=combined_personality,
            factual_accuracy_score=combined_factual,
            tone_consistency_score=combined_tone,
            clarity_score=combined_clarity,
            issues=combined_issues,
            suggestions=combined_suggestions,
            metadata=combined_metadata,
        )

    def _fallback_analysis(self, answer: str) -> QualityScore:
        """後備品質分析（當主要分析失敗時使用）"""
        length = len(answer)

        # 基本分數估算
        base_score = 0.6
        if 50 <= length <= 200:
            base_score += 0.1
        if "我" in answer:
            base_score += 0.1
        if any(phrase in answer for phrase in self.objective_phrases):
            base_score -= 0.2

        base_score = max(0.0, min(1.0, base_score))

        return QualityScore(
            overall_score=base_score,
            personality_score=base_score,
            factual_accuracy_score=base_score,
            tone_consistency_score=base_score,
            clarity_score=base_score,
            issues=[QualityIssue.TONE_MISMATCH] if base_score < 0.7 else [],
            suggestions=["建議人工檢查回答品質"],
            metadata={
                "method": "fallback",
                "length": length,
                "estimated_score": base_score,
            },
        )

    def optimize_answer(
        self,
        answer: str,
        question: str = "",
        quality_score: Optional[QualityScore] = None,
    ) -> OptimizedAnswer:
        """
        優化回答品質

        Args:
            answer: 原始回答
            question: 原始問題
            quality_score: 品質評估結果（如果已有）

        Returns:
            OptimizedAnswer: 優化後的回答
        """
        if not quality_score:
            quality_score = self.analyze_quality(answer, question)

        # 如果品質已經很高，直接返回
        if quality_score.overall_score >= 0.85:
            return OptimizedAnswer(
                original_answer=answer,
                optimized_answer=answer,
                quality_improvement=0.0,
                changes_made=["無需優化，品質已達標準"],
                confidence=0.9,
            )

        try:
            # 準備優化提示詞
            issues_text = ", ".join([issue.value for issue in quality_score.issues])
            suggestions_text = "; ".join(quality_score.suggestions[:3])  # 限制建議數量

            prompt = self.optimization_prompt_template.format(
                question=question or "未提供問題",
                answer=answer,
                issues=issues_text or "無特定問題",
                suggestions=suggestions_text or "一般性改善",
            )

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=300,
            )

            optimized_answer = response.choices[0].message.content.strip()

            # 評估優化後的品質
            new_quality_score = self.analyze_quality(optimized_answer, question)
            improvement = new_quality_score.overall_score - quality_score.overall_score

            # 分析所做的改變
            changes_made = self._analyze_changes(
                answer, optimized_answer, quality_score.issues
            )

            return OptimizedAnswer(
                original_answer=answer,
                optimized_answer=optimized_answer,
                quality_improvement=improvement,
                changes_made=changes_made,
                confidence=min(0.9, new_quality_score.overall_score),
            )

        except Exception as e:
            logger.error(f"回答優化失敗：{e}")
            return OptimizedAnswer(
                original_answer=answer,
                optimized_answer=answer,
                quality_improvement=0.0,
                changes_made=[f"優化失敗：{str(e)}"],
                confidence=0.3,
            )

    def _analyze_changes(
        self, original: str, optimized: str, issues: List[QualityIssue]
    ) -> List[str]:
        """分析優化過程中做出的改變"""
        changes = []

        # 檢查長度變化
        len_diff = len(optimized) - len(original)
        if abs(len_diff) > 10:
            if len_diff > 0:
                changes.append(f"擴展內容 (+{len_diff} 字符)")
            else:
                changes.append(f"精簡內容 ({len_diff} 字符)")

        # 檢查第一人稱使用變化
        original_first_person = len(re.findall(r"我[的在擅長認為曾經]?", original))
        optimized_first_person = len(re.findall(r"我[的在擅長認為曾經]?", optimized))

        if optimized_first_person > original_first_person:
            changes.append("增加第一人稱表達")

        # 檢查客觀描述詞彙的移除
        original_objective = sum(
            1 for phrase in self.objective_phrases if phrase in original
        )
        optimized_objective = sum(
            1 for phrase in self.objective_phrases if phrase in optimized
        )

        if optimized_objective < original_objective:
            changes.append("移除客觀描述語言")

        # 根據原始問題類型推斷改變
        if (
            QualityIssue.LACK_PERSONALITY in issues
            and optimized_first_person > original_first_person
        ):
            changes.append("增強個人特色表達")

        if QualityIssue.TONE_MISMATCH in issues:
            changes.append("調整語氣風格")

        if QualityIssue.LACKS_SPECIFICITY in issues:
            changes.append("增加具體細節")

        return changes if changes else ["進行語言潤飾"]


class BatchQualityProcessor:
    """批量品質處理器"""

    def __init__(self, analyzer: Optional[AnswerQualityAnalyzer] = None):
        self.analyzer = analyzer or AnswerQualityAnalyzer()

    def process_batch(
        self, qa_pairs: List[Dict[str, str]], optimize: bool = True
    ) -> List[Dict]:
        """
        批量處理問答對的品質評估和優化

        Args:
            qa_pairs: 問答對列表，格式 [{"question": "...", "answer": "..."}]
            optimize: 是否執行優化

        Returns:
            List[Dict]: 處理結果列表
        """
        results = []

        for i, qa_pair in enumerate(qa_pairs):
            try:
                question = qa_pair.get("question", "")
                answer = qa_pair.get("answer", "")

                if not answer:
                    logger.warning(f"第 {i+1} 個問答對缺少回答，跳過")
                    continue

                # 品質分析
                quality_score = self.analyzer.analyze_quality(answer, question)

                result = {
                    "index": i,
                    "question": question,
                    "original_answer": answer,
                    "quality_score": quality_score,
                }

                # 執行優化（如果需要）
                if optimize and quality_score.overall_score < 0.8:
                    optimized = self.analyzer.optimize_answer(
                        answer, question, quality_score
                    )
                    result["optimized"] = optimized

                results.append(result)

            except Exception as e:
                logger.error(f"處理第 {i+1} 個問答對時發生錯誤：{e}")
                results.append(
                    {
                        "index": i,
                        "error": str(e),
                        "question": qa_pair.get("question", ""),
                        "original_answer": qa_pair.get("answer", ""),
                    }
                )

        return results


# 便利函數
def analyze_answer_quality(answer: str, question: str = "") -> QualityScore:
    """
    快速品質分析函數

    Args:
        answer: 回答內容
        question: 問題內容（可選）

    Returns:
        QualityScore: 品質評估結果
    """
    analyzer = AnswerQualityAnalyzer()
    return analyzer.analyze_quality(answer, question)


def optimize_answer_quality(answer: str, question: str = "") -> OptimizedAnswer:
    """
    快速回答優化函數

    Args:
        answer: 原始回答
        question: 問題內容（可選）

    Returns:
        OptimizedAnswer: 優化結果
    """
    analyzer = AnswerQualityAnalyzer()
    return analyzer.optimize_answer(answer, question)
