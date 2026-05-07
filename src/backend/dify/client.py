"""Dify Chatflow API 非同步客戶端

透過 httpx 呼叫 Dify /v1/chat-messages 端點（blocking 模式）。
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv(override=False)

logger = logging.getLogger(__name__)

# Dify Chatflow 回應的 TypeAlias（避免引入 typing_extensions）
DifyResponse = dict[str, Any]

_DEFAULT_TIMEOUT = 60.0


class DifyClient:
    """Dify Chatflow API 客戶端。"""

    def __init__(
        self,
        api_base: str | None = None,
        api_key: str | None = None,
        user: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
    ):
        api_base_value = api_base or os.getenv("DIFY_API_BASE") or ""
        api_key_value = api_key or os.getenv("DIFY_API_KEY") or ""
        user_value = user or os.getenv("DIFY_USER") or "resumemate-visitor"

        self.api_base = api_base_value.rstrip("/")
        self.api_key = api_key_value
        self.user = user_value
        self.timeout = timeout

        if not self.api_base:
            raise ValueError("DIFY_API_BASE 未設定")
        if not self.api_key:
            raise ValueError("DIFY_API_KEY 未設定")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        query: str,
        conversation_id: str = "",
        inputs: dict[str, Any] | None = None,
    ) -> DifyResponse:
        """送出一則訊息至 Dify Chatflow 並以 blocking 模式等待回應。

        Args:
            query: 使用者的提問文字
            conversation_id: 現有對話 ID；空字串代表開啟新對話
            inputs: 傳入 Chatflow 的額外輸入變數

        Returns:
            Dify API 的完整 JSON 回應字典

        Raises:
            httpx.HTTPStatusError: HTTP 非 2xx 回應
            httpx.TimeoutException: 請求逾時
            DifyClientError: Dify 業務層錯誤
        """
        payload: dict[str, Any] = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": "blocking",
            "user": self.user,
        }
        # Dify 規格：conversation_id 為空字串時不傳入（建立新對話）
        if conversation_id:
            payload["conversation_id"] = conversation_id

        url = f"{self.api_base}/chat-messages"
        logger.debug("Dify 請求 → %s  conv=%s", url, conversation_id or "<new>")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=self._headers(), json=payload)

        if not resp.is_success:
            body = resp.text
            logger.error("Dify API 錯誤 %s: %s", resp.status_code, body)
            raise DifyClientError(
                status_code=resp.status_code,
                message=body,
            )

        data: DifyResponse = resp.json()
        logger.debug(
            "Dify 回應 conv=%s  answer=%s...",
            data.get("conversation_id", "?"),
            str(data.get("answer", ""))[:60],
        )
        return data

    async def get_app_info(self) -> dict[str, Any]:
        """查詢 Dify App 基本資訊（可用來確認 app mode）。"""
        url = f"{self.api_base}/info"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=self._headers())
        resp.raise_for_status()
        return resp.json()


class DifyClientError(Exception):
    """Dify API 業務層錯誤。"""

    def __init__(self, status_code: int, message: str):
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.message = message
