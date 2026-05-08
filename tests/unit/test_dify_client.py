"""DifyClient 單元測試 — 使用 httpx mock 驗證 API 呼叫格式。"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def client():
    """建立 DifyClient 並注入測試用環境變數。"""
    with patch.dict(
        "os.environ",
        {
            "DIFY_API_BASE": "https://dify.example.com/v1",
            "DIFY_API_KEY": "app-test-key",
            "DIFY_USER": "test-user",
        },
    ):
        from src.backend.dify.client import DifyClient

        return DifyClient()


@pytest.mark.asyncio
async def test_chat_new_conversation(client):
    """新對話（空 conversation_id）不應在 payload 中傳入 conversation_id。"""
    mock_response_data = {
        "answer": "這是測試回答",
        "conversation_id": "conv-new-123",
        "metadata": {},
    }
    mock_resp = MagicMock()
    mock_resp.is_success = True
    mock_resp.json.return_value = mock_response_data

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        result = await client.chat("你好", conversation_id="")

    assert result["answer"] == "這是測試回答"
    assert result["conversation_id"] == "conv-new-123"

    call_kwargs = mock_client.post.call_args
    payload = call_kwargs.kwargs.get("json") or call_kwargs.args[1]
    assert "conversation_id" not in payload, "新對話不應傳入 conversation_id"
    assert payload["response_mode"] == "blocking"
    assert payload["query"] == "你好"
    assert payload["user"] == "test-user"
    assert payload["inputs"]["answer_size"] == "適中"


@pytest.mark.asyncio
async def test_chat_existing_conversation(client):
    """續接對話應在 payload 中傳入 conversation_id。"""
    mock_resp = MagicMock()
    mock_resp.is_success = True
    mock_resp.json.return_value = {
        "answer": "續接回答",
        "conversation_id": "conv-existing-456",
        "metadata": {},
    }

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        await client.chat("繼續問", conversation_id="conv-existing-456")

    call_kwargs = mock_client.post.call_args
    payload = call_kwargs.kwargs.get("json") or call_kwargs.args[1]
    assert payload["conversation_id"] == "conv-existing-456"
    assert payload["inputs"]["answer_size"] == "適中"


@pytest.mark.asyncio
async def test_chat_preserves_custom_inputs(client):
    """自訂 inputs 應保留，並自動補上 answer_size。"""
    mock_resp = MagicMock()
    mock_resp.is_success = True
    mock_resp.json.return_value = {
        "answer": "含自訂輸入的回答",
        "conversation_id": "conv-custom-789",
        "metadata": {},
    }

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        await client.chat("你好", inputs={"language": "zh-TW"})

    call_kwargs = mock_client.post.call_args
    payload = call_kwargs.kwargs.get("json") or call_kwargs.args[1]
    assert payload["inputs"] == {"language": "zh-TW", "answer_size": "適中"}


@pytest.mark.asyncio
async def test_chat_allows_overriding_answer_size(client):
    """呼叫端顯式提供 answer_size 時應優先採用。"""
    mock_resp = MagicMock()
    mock_resp.is_success = True
    mock_resp.json.return_value = {
        "answer": "短回答",
        "conversation_id": "conv-brief-999",
        "metadata": {},
    }

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        await client.chat("你好", inputs={"answer_size": "brief"})

    call_kwargs = mock_client.post.call_args
    payload = call_kwargs.kwargs.get("json") or call_kwargs.args[1]
    assert payload["inputs"]["answer_size"] == "簡短"


def test_client_maps_legacy_env_answer_size_values():
    """舊的英文長度設定應轉為 Dify 下拉選項值。"""
    with patch.dict(
        "os.environ",
        {
            "DIFY_API_BASE": "https://dify.example.com/v1",
            "DIFY_API_KEY": "app-test-key",
            "AGENT_RESPONSE_LENGTH": "detailed",
        },
    ):
        from src.backend.dify.client import DifyClient

        client = DifyClient()

    assert client.answer_size == "詳細"


@pytest.mark.asyncio
async def test_chat_raises_on_http_error(client):
    """HTTP 非 2xx 回應應拋出 DifyClientError。"""
    from src.backend.dify.client import DifyClientError

    mock_resp = MagicMock()
    mock_resp.is_success = False
    mock_resp.status_code = 401
    mock_resp.text = "Unauthorized"

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        with pytest.raises(DifyClientError) as exc_info:
            await client.chat("問題")

    assert exc_info.value.status_code == 401


def test_client_raises_without_api_base():
    """未設定 DIFY_API_BASE 應拋出 ValueError。"""
    with patch.dict("os.environ", {"DIFY_API_BASE": "", "DIFY_API_KEY": "key"}):
        from importlib import reload
        import src.backend.dify.client as m

        reload(m)
        with pytest.raises(ValueError, match="DIFY_API_BASE"):
            m.DifyClient()


def test_client_raises_without_api_key():
    """未設定 DIFY_API_KEY 應拋出 ValueError。"""
    with patch.dict(
        "os.environ",
        {"DIFY_API_BASE": "https://dify.example.com/v1", "DIFY_API_KEY": ""},
    ):
        from importlib import reload
        import src.backend.dify.client as m

        reload(m)
        with pytest.raises(ValueError, match="DIFY_API_KEY"):
            m.DifyClient()
