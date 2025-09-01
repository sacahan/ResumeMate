"""ResumeMate 高性能處理器 🚀

協調 Analysis Agent 和 Evaluate Agent 的互動，使用 OpenAI Agents SDK 標準實現
具備性能監控、異步處理、連接池管理等優化特性
"""

import asyncio
import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from backend.models import Question, SystemResponse
from backend.tools.rag import RAGTools
from backend.agents import AnalysisAgent, EvaluateAgent

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """處理性能統計"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_processing_time: float = 0.0
    min_processing_time: float = float("inf")
    max_processing_time: float = 0.0
    analysis_time: float = 0.0
    evaluation_time: float = 0.0
    concurrent_requests: int = 0
    cache_hits: int = 0
    start_time: float = field(default_factory=time.time)
    last_reset_time: float = field(default_factory=time.time)

    def update_timing(
        self,
        processing_time: float,
        analysis_time: float = 0.0,
        evaluation_time: float = 0.0,
    ):
        """更新時間統計"""
        self.total_requests += 1

        # 更新平均處理時間
        prev_avg = self.avg_processing_time
        self.avg_processing_time = (
            prev_avg * (self.total_requests - 1) + processing_time
        ) / self.total_requests

        # 更新最小和最大時間
        self.min_processing_time = min(self.min_processing_time, processing_time)
        self.max_processing_time = max(self.max_processing_time, processing_time)

        # 更新各階段時間
        if analysis_time > 0:
            self.analysis_time = analysis_time
        if evaluation_time > 0:
            self.evaluation_time = evaluation_time

    def success(self):
        """記錄成功請求"""
        self.successful_requests += 1

    def failure(self):
        """記錄失敗請求"""
        self.failed_requests += 1

    def get_success_rate(self) -> float:
        """獲取成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests


class ResumeMateProcessor:
    """ResumeMate 高性能主處理器 🚀"""

    def __init__(self, max_concurrent_requests: int = 10):
        """初始化高效處理器

        Args:
            max_concurrent_requests: 最大並發請求數
        """
        # 🔧 核心組件初始化
        self.rag_tools = RAGTools()
        self.analysis_agent = AnalysisAgent()
        self.evaluate_agent = EvaluateAgent()

        # 📊 性能監控和統計
        self.stats = ProcessingStats()
        self.max_concurrent_requests = max_concurrent_requests
        self._request_semaphore = asyncio.Semaphore(max_concurrent_requests)

        # 💾 簡單請求緩存 (基於問題的雜湊緩存)
        self._request_cache: Dict[str, Tuple[SystemResponse, float]] = {}
        self.enable_request_cache = True
        self.cache_ttl = 300  # 5 分鐘

        # 🚀 性能優化配置
        self.enable_parallel_processing = True
        self.request_timeout = 30.0  # 30 秒逾時

        logger.info("🎆 ResumeMate 高性能處理器初始化完成")
        logger.info(
            f"⚙️  配置: 最大並發={max_concurrent_requests}, 緩存TTL={self.cache_ttl}s"
        )

    async def process_question(self, question: Question) -> SystemResponse:
        """高效主處理流程 🎯

        具備繁忙控制、緩存機制、性能監控和異步處理優化
        """
        start_time = time.time()
        request_id = f"{hash(question.text)}_{int(start_time * 1000) % 10000}"

        # 📊 更新並發計數器
        self.stats.concurrent_requests += 1

        try:
            async with self._request_semaphore:  # 🚪 繁忙控制
                return await asyncio.wait_for(
                    self._process_question_internal(question, request_id, start_time),
                    timeout=self.request_timeout,
                )
        except asyncio.TimeoutError:
            logger.error(
                f"⏰ 請求逾時 ({self.request_timeout}s): {question.text[:50]}..."
            )
            self.stats.failure()
            return self._create_error_response("請求處理逾時，請稍後再試。")
        except Exception as e:
            logger.error(f"❌ 處理問題時發生錯誤: {e}")
            self.stats.failure()
            return self._create_error_response(f"處理錯誤: {str(e)}")
        finally:
            # 📊 更新統計資訊
            self.stats.concurrent_requests -= 1
            elapsed_time = time.time() - start_time
            self.stats.update_timing(elapsed_time)

    async def _process_question_internal(
        self, question: Question, request_id: str, start_time: float
    ) -> SystemResponse:
        """內部處理邏輯 🔧"""
        logger.info(f"🚀 [{request_id}] 開始處理問題: {question.text[:50]}...")

        # 💾 檢查請求緩存
        if self.enable_request_cache:
            cache_response = self._check_request_cache(question.text)
            if cache_response:
                self.stats.cache_hits += 1
                self.stats.success()
                logger.info(f"✨ [{request_id}] 緩存命中，直接返回")
                return cache_response

        analysis_start = time.time()

        try:
            # 🔍 1) 分析階段 - 使用高效緩存的 Analysis Agent
            analysis = await self.analysis_agent.analyze(question)
            analysis_time = time.time() - analysis_start

            # 1.1 回填 sources（為 Evaluate Agent 提供來源信息）
            analysis.metadata = analysis.metadata or {}
            analysis.metadata.setdefault("sources", self._ensure_sources(analysis))
            analysis.metadata["request_id"] = request_id
            analysis.metadata["analysis_time"] = analysis_time

            logger.info(f"✅ [{request_id}] 分析完成 ({analysis_time:.3f}s)")

            # 🔎 2) 評估階段 - 進行品質檢核與優化
            evaluation_start = time.time()

            if self.enable_parallel_processing:
                # 伵行處理：同時進行評估和性能統計
                evaluation_task = asyncio.create_task(
                    self.evaluate_agent.evaluate(analysis)
                )
                stats_task = asyncio.create_task(
                    self._update_performance_metrics(analysis)
                )

                evaluation, _ = await asyncio.gather(
                    evaluation_task, stats_task, return_exceptions=True
                )

                if isinstance(evaluation, Exception):
                    raise evaluation
            else:
                evaluation = await self.evaluate_agent.evaluate(analysis)

            evaluation_time = time.time() - evaluation_start
            logger.info(f"✅ [{request_id}] 評估完成 ({evaluation_time:.3f}s)")

            # 🎆 3) 格式化最終回覆
            final_response = self._format_system_response(evaluation)

            # 墝加性能元數據
            final_response.metadata.update(
                {
                    "request_id": request_id,
                    "processing_time": time.time() - start_time,
                    "analysis_time": analysis_time,
                    "evaluation_time": evaluation_time,
                    "cached": False,
                }
            )

            # 💾 緩存結果
            if self.enable_request_cache:
                self._cache_response(question.text, final_response)

            self.stats.success()
            self.stats.update_timing(
                time.time() - start_time, analysis_time, evaluation_time
            )

            total_time = time.time() - start_time
            logger.info(f"✨ [{request_id}] 處理完成 ({total_time:.3f}s)")

            return final_response

        except Exception as e:
            logger.error(f"❌ [{request_id}] 處理失敗: {e}")
            self.stats.failure()
            raise

    # 🔧 --------- 工具：把 retrievals/metadata 轉為 reviewer 可用的 sources ----------
    def _ensure_sources(self, analysis) -> List[Dict[str, Any]]:
        sources: List[Dict[str, Any]] = []

        # (A) 從 retrievals 轉成可追溯來源
        try:
            if getattr(analysis, "retrievals", None):
                for r in analysis.retrievals:
                    md = getattr(r, "metadata", {}) or {}
                    sources.append(
                        {
                            "id": getattr(r, "doc_id", getattr(r, "id", None)),
                            "title": md.get("title"),
                            "loc": md.get("loc"),
                            "score": getattr(r, "score", None),
                        }
                    )
        except Exception as e:
            logger.warning(f"轉換 retrievals 為 sources 失敗：{e}")

        # (B) 若 analysis.metadata 已有 sources，合併
        try:
            meta_sources = (analysis.metadata or {}).get("sources", [])
            if isinstance(meta_sources, list):
                # 轉換 sources 為統一格式
                for source in meta_sources:
                    if isinstance(source, str):
                        # 如果是字串 ID，轉為字典格式
                        sources.append(
                            {
                                "id": source,
                                "title": None,
                                "loc": None,
                                "score": 0.8,
                            }
                        )
                    elif isinstance(source, dict):
                        # 如果已經是字典，直接使用
                        sources.append(source)
        except Exception as e:
            logger.warning(f"轉換 metadata sources 失敗：{e}")

        # 去重（以 id+loc）
        seen = set()
        uniq: List[Dict[str, Any]] = []
        for s in sources:
            key = (s.get("id"), s.get("loc"))
            if key in seen:
                continue
            seen.add(key)
            uniq.append(s)

        return uniq[:5]  # 控制上限

    # 🎆 --------- 產出最終 SystemResponse（含動作建議） ----------
    def _format_system_response(self, evaluation) -> SystemResponse:
        """格式化為系統回應"""
        conf = max(0.0, min(1.0, float(getattr(evaluation, "confidence", 0.0))))

        # 允許不同枚舉/字串；統一歸一化
        status_str = str(getattr(evaluation.status, "value", evaluation.status)).lower()
        action = None

        if status_str in ("needs_clarification", "clarify"):
            action = "請提供更多資訊"
        elif status_str in ("out_of_scope", "oos"):
            # out_of_scope 也應該升級到人工處理
            action = "請填寫聯絡表單"
        elif status_str == "escalate_to_human":
            action = "請填寫聯絡表單"

        return SystemResponse(
            answer=evaluation.final_answer,
            sources=evaluation.sources or [],
            confidence=conf,
            action=action,
            metadata={
                "status": status_str,
                **(evaluation.metadata or {}),
            },
        )

    # 💻 --------- 系統資訊與性能監控 ----------
    def _check_request_cache(self, question_text: str) -> Optional[SystemResponse]:
        """檢查請求緩存 💾"""
        question_hash = str(hash(question_text.strip().lower()))

        if question_hash in self._request_cache:
            response, timestamp = self._request_cache[question_hash]
            if time.time() - timestamp < self.cache_ttl:
                # 更新緩存標記
                response.metadata["cached"] = True
                response.metadata["cache_age"] = time.time() - timestamp
                return response
            else:
                # 清理過期緩存
                del self._request_cache[question_hash]

        return None

    def _cache_response(self, question_text: str, response: SystemResponse) -> None:
        """緩存回應結果 💾"""
        question_hash = str(hash(question_text.strip().lower()))
        current_time = time.time()

        # 限制緩存大小
        if len(self._request_cache) >= 100:
            # 清理最老的緩存項目
            oldest_key = min(
                self._request_cache.keys(), key=lambda k: self._request_cache[k][1]
            )
            del self._request_cache[oldest_key]

        self._request_cache[question_hash] = (response, current_time)

    def _create_error_response(self, error_message: str) -> SystemResponse:
        """創建錯誤回應 ❌"""
        return SystemResponse(
            answer=f"抱歉，{error_message}",
            sources=[],
            confidence=0.0,
            action="請稍後再試或聯繫技術支援",
            metadata={
                "error": error_message,
                "timestamp": time.time(),
                "system_status": "error",
            },
        )

    async def _update_performance_metrics(self, analysis) -> None:
        """異步更新性能指標 📈"""
        try:
            # 更新 RAG 統計
            if hasattr(self.rag_tools, "get_performance_stats"):
                rag_stats = self.rag_tools.get_performance_stats()
                logger.debug(
                    f"📈 RAG 性能: 平均{rag_stats.get('avg_response_time', 0):.3f}s, "
                    f"緩存命中率{rag_stats.get('cache_hit_rate', 0):.1%}"
                )
        except Exception as e:
            logger.debug(f"更新性能指標失敗: {e}")

    def clear_cache(self) -> Dict[str, int]:
        """清理所有緩存 🧹"""
        request_cache_size = len(self._request_cache)
        self._request_cache.clear()

        # 清理 RAG 緩存
        rag_cache_cleared = 0
        if hasattr(self.rag_tools, "clear_cache"):
            try:
                rag_cache_info = self.rag_tools.get_performance_stats()
                rag_cache_cleared = rag_cache_info.get("active_cache_size", 0)
                self.rag_tools.clear_cache()
            except Exception as e:
                logger.warning(f"清理 RAG 緩存失敗: {e}")

        logger.info(
            f"緩存已清理: 請求緩存 {request_cache_size} 個, RAG 緩存 {rag_cache_cleared} 個"
        )

        return {
            "request_cache_cleared": request_cache_size,
            "rag_cache_cleared": rag_cache_cleared,
            "total_cleared": request_cache_size + rag_cache_cleared,
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """獲取詳細性能統計 📈"""
        current_time = time.time()
        uptime = current_time - self.stats.start_time

        processor_stats = {
            "processor": {
                "total_requests": self.stats.total_requests,
                "successful_requests": self.stats.successful_requests,
                "failed_requests": self.stats.failed_requests,
                "success_rate": self.stats.get_success_rate(),
                "avg_processing_time": self.stats.avg_processing_time,
                "min_processing_time": self.stats.min_processing_time
                if self.stats.min_processing_time != float("inf")
                else 0.0,
                "max_processing_time": self.stats.max_processing_time,
                "current_concurrent_requests": self.stats.concurrent_requests,
                "cache_hits": self.stats.cache_hits,
                "cache_hit_rate": self.stats.cache_hits
                / max(self.stats.total_requests, 1),
                "uptime_seconds": uptime,
                "requests_per_second": self.stats.total_requests / max(uptime, 1),
            }
        }

        # 墝加 RAG 統計
        try:
            if hasattr(self.rag_tools, "get_performance_stats"):
                processor_stats["rag"] = self.rag_tools.get_performance_stats()
        except Exception as e:
            logger.warning(f"獲取 RAG 統計失敗: {e}")
            processor_stats["rag"] = {"error": str(e)}

        return processor_stats

    def get_system_info(self) -> Dict[str, Any]:
        """獲取系統資訊 💻"""
        db_info = {"document_count": 0, "status": "unknown"}
        if hasattr(self.rag_tools, "collection") and self.rag_tools.collection:
            try:
                count = self.rag_tools.collection.count()
                db_info["document_count"] = count
                db_info["status"] = "connected" if count > 0 else "empty"
            except Exception as e:
                logger.error(f"獲取數據庫資訊時發生錯誤: {e}")
                db_info["status"] = "error"
                db_info["error"] = str(e)

        system_info = {
            "version": "2.0.0",
            "database": db_info,
            "performance": self.get_performance_stats(),
            "configuration": {
                "max_concurrent_requests": self.max_concurrent_requests,
                "request_timeout": self.request_timeout,
                "cache_enabled": self.enable_request_cache,
                "cache_ttl": self.cache_ttl,
                "parallel_processing": self.enable_parallel_processing,
            },
            "cache_status": {
                "request_cache_size": len(self._request_cache),
                "request_cache_limit": 100,
            },
        }

        return system_info

    def reset_stats(self) -> None:
        """重置性能統計 🔄"""
        self.stats = ProcessingStats()
        if hasattr(self.rag_tools, "reset_performance_stats"):
            self.rag_tools.reset_performance_stats()
        logger.info("性能統計已重置")

    async def health_check(self) -> Dict[str, Any]:
        """系統健康檢查 ❤️"""
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {},
        }

        try:
            # 檢查資料庫連接
            if hasattr(self.rag_tools, "collection") and self.rag_tools.collection:
                doc_count = self.rag_tools.collection.count()
                health_status["components"]["database"] = {
                    "status": "healthy" if doc_count > 0 else "warning",
                    "document_count": doc_count,
                }
            else:
                health_status["components"]["database"] = {
                    "status": "unhealthy",
                    "message": "無法連接到資料庫",
                }
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        # 檢查 AI 代理
        try:
            health_status["components"]["ai_agents"] = {
                "analysis_agent": "healthy" if self.analysis_agent else "unhealthy",
                "evaluate_agent": "healthy" if self.evaluate_agent else "unhealthy",
            }
        except Exception as e:
            health_status["components"]["ai_agents"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        # 檢查整體系統狀態
        if self.stats.get_success_rate() < 0.8 and self.stats.total_requests > 10:
            health_status["status"] = "degraded"
            health_status["message"] = (
                f"成功率過低: {self.stats.get_success_rate():.1%}"
            )

        # 檢查並發程度
        if self.stats.concurrent_requests >= self.max_concurrent_requests * 0.9:
            health_status["status"] = "warning"
            health_status["message"] = (
                f"高並發負載: {self.stats.concurrent_requests}/{self.max_concurrent_requests}"
            )

        return health_status
