"""DifyProcessor — Dify Chatflow 主處理器

取代原先的 ResumeMateProcessor，直接透過 Dify API 處理使用者問題。
"""

from __future__ import annotations

import logging
import time

from ..models import Question, SystemResponse
from .client import DifyClient, DifyClientError
from . import adapter as _adapter

logger = logging.getLogger(__name__)


class DifyProcessor:
    """將使用者問題轉發至 Dify Chatflow，並回傳標準 SystemResponse。"""

    def __init__(self):
        self._client = DifyClient()
        logger.info("DifyProcessor 初始化完成（base=%s）", self._client.api_base)

    async def process_question(
        self, question: Question, conversation_id: str = ""
    ) -> tuple[SystemResponse, str]:
        """處理一則使用者問題。

        Args:
            question: 使用者問題（包含 text 與 language）
            conversation_id: 現有對話 ID；空字串代表開新對話

        Returns:
            - SystemResponse: 標準化回應
            - str: 更新後的 conversation_id（傳回 app.py 的 gr.State）
        """
        start = time.monotonic()
        try:
            dify_resp = await self._client.chat(
                query=question.text,
                conversation_id=conversation_id,
            )
            response, new_conv_id = _adapter.adapt(dify_resp)

            elapsed = time.monotonic() - start
            logger.info(
                "Dify 回應完成 conv=%s  elapsed=%.2fs  conf=%.2f",
                new_conv_id or conversation_id or "<new>",
                elapsed,
                response.confidence,
            )
            return response, new_conv_id

        except DifyClientError as exc:
            elapsed = time.monotonic() - start
            logger.error("Dify API 錯誤 (%.2fs): %s", elapsed, exc)
            return _fallback_response(str(exc)), conversation_id

        except Exception as exc:
            elapsed = time.monotonic() - start
            logger.error(
                "DifyProcessor 未預期錯誤 (%.2fs): %s", elapsed, exc, exc_info=True
            )
            return _fallback_response(str(exc)), conversation_id


def _fallback_response(error_detail: str) -> SystemResponse:
    """當 Dify API 呼叫失敗時回傳友善的錯誤回應。"""
    return SystemResponse(
        answer="抱歉，目前無法取得回應，請稍後再試。",
        sources=[],
        confidence=0.0,
        action=None,
        metadata={"status": "error", "error": error_detail},
    )
