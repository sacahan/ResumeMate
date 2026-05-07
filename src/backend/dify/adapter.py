"""Dify Chatflow 回應轉接器

將 Dify /v1/chat-messages 的 JSON 回應映射為 SystemResponse。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from ..models import SystemResponse

logger = logging.getLogger(__name__)

# Dify 不原生提供信心分數；固定為合理預設值以避免觸發低信心提示
_DEFAULT_CONFIDENCE = 0.85


def adapt(dify_response: dict[str, Any]) -> tuple[SystemResponse, str]:
    """將 Dify Chatflow 回應轉換為 (SystemResponse, conversation_id)。

    Args:
        dify_response: Dify /v1/chat-messages blocking 模式的完整回應字典

    Returns:
        - SystemResponse: 標準化的系統回應
        - str: Dify 返回的 conversation_id（供下一輪使用）
    """
    answer = dify_response.get("answer") or ""
    conversation_id = dify_response.get("conversation_id") or ""

    sources = _extract_sources(dify_response)
    action, status, metadata = _extract_structured_output(dify_response, answer)

    response = SystemResponse(
        answer=answer,
        sources=sources,
        confidence=_DEFAULT_CONFIDENCE,
        action=action,
        metadata={"status": status, **metadata},
    )
    return response, conversation_id


def _extract_sources(dify_response: dict[str, Any]) -> list[str]:
    """從 Dify metadata.retriever_resources 提取來源文件名稱。"""
    resources = dify_response.get("metadata", {}).get("retriever_resources") or []
    seen: set[str] = set()
    sources: list[str] = []
    for r in resources:
        name = r.get("document_name") or r.get("dataset_name") or ""
        if name and name not in seen:
            seen.add(name)
            sources.append(name)
    return sources[:5]


def _extract_structured_output(
    dify_response: dict[str, Any], answer: str
) -> tuple[Optional[str], str, dict[str, Any]]:
    """從 Dify 回應中推導出 action、status 與額外 metadata。

    若 Dify End 節點有輸出 `outputs` 結構化欄位，優先使用；
    否則 action 為 None（正常回答流程）。

    Returns:
        - action: SystemResponse.action 字串或 None
        - status: metadata["status"] 字串
        - extra_metadata: 其他額外 metadata 字典
    """
    # 嘗試從 outputs 取得結構化欄位（Dify Chatflow 需在 End 節點設定輸出變數）
    outputs: dict[str, Any] = dify_response.get("outputs") or {}
    status_raw = str(outputs.get("status") or "ok").lower()
    missing_fields: list[str] = outputs.get("missing_fields") or []
    clarify_examples: list[str] = outputs.get("clarify_examples") or []

    action = _derive_action(status_raw)

    extra: dict[str, Any] = {}
    if missing_fields:
        extra["missing_fields"] = missing_fields
    if clarify_examples:
        extra["clarify_examples"] = clarify_examples

    return action, status_raw, extra


def _derive_action(status: str) -> Optional[str]:
    """將 Dify status 字串對應至 SystemResponse.action 的中文指令。"""
    if status in ("needs_clarification", "clarify"):
        return "請提供更多資訊"
    if status in ("out_of_scope", "oos", "escalate_to_human"):
        return "請填寫聯絡表單"
    return None
