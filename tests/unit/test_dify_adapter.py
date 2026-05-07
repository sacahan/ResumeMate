"""DifyAdapter 單元測試 — 驗證各種 Dify 回應的 SystemResponse 映射。"""

import pytest
from src.backend.dify.adapter import adapt, _derive_action, _extract_sources


# ---------------------------------------------------------------------------
# adapt() 核心映射測試
# ---------------------------------------------------------------------------


def test_adapt_basic_response():
    """正常回應應正確映射 answer、conversation_id 與預設 confidence。"""
    dify_resp = {
        "answer": "我是一名後端工程師",
        "conversation_id": "conv-abc-123",
        "metadata": {},
    }
    response, conv_id = adapt(dify_resp)

    assert response.answer == "我是一名後端工程師"
    assert conv_id == "conv-abc-123"
    assert response.confidence == 0.85
    assert response.action is None
    assert response.sources == []


def test_adapt_with_retriever_resources():
    """含 retriever_resources 的回應應提取 sources 清單。"""
    dify_resp = {
        "answer": "相關工作經歷如下...",
        "conversation_id": "conv-src-456",
        "metadata": {
            "retriever_resources": [
                {"document_name": "resume-zh.json", "score": 0.9},
                {"document_name": "resume-en.json", "score": 0.8},
                {"document_name": "resume-zh.json", "score": 0.75},  # 重複應去重
            ]
        },
    }
    response, _ = adapt(dify_resp)

    assert "resume-zh.json" in response.sources
    assert "resume-en.json" in response.sources
    assert len(response.sources) == 2  # 去重後


def test_adapt_action_clarify():
    """outputs.status 為 needs_clarification 時 action 應為「請提供更多資訊」。"""
    dify_resp = {
        "answer": "請問您想了解哪方面的技能？",
        "conversation_id": "conv-clarify",
        "outputs": {"status": "needs_clarification"},
        "metadata": {},
    }
    response, _ = adapt(dify_resp)
    assert response.action == "請提供更多資訊"


def test_adapt_action_escalate():
    """outputs.status 為 escalate_to_human 時 action 應為「請填寫聯絡表單」。"""
    dify_resp = {
        "answer": "這個問題超出我的回答範圍...",
        "conversation_id": "conv-escalate",
        "outputs": {"status": "escalate_to_human"},
        "metadata": {},
    }
    response, _ = adapt(dify_resp)
    assert response.action == "請填寫聯絡表單"


def test_adapt_action_ok_status():
    """outputs.status 為 ok（正常回答）時 action 應為 None。"""
    dify_resp = {
        "answer": "正常回答",
        "conversation_id": "conv-ok",
        "outputs": {"status": "ok"},
        "metadata": {},
    }
    response, _ = adapt(dify_resp)
    assert response.action is None


def test_adapt_missing_answer_returns_empty_string():
    """Dify 回應缺少 answer 欄位時不應拋出例外，answer 應為空字串。"""
    dify_resp = {"conversation_id": "conv-empty", "metadata": {}}
    response, conv_id = adapt(dify_resp)
    assert response.answer == ""
    assert conv_id == "conv-empty"


def test_adapt_missing_conversation_id_returns_empty_string():
    """Dify 回應缺少 conversation_id 時應回傳空字串。"""
    dify_resp = {"answer": "回答", "metadata": {}}
    response, conv_id = adapt(dify_resp)
    assert conv_id == ""


def test_adapt_sources_capped_at_five():
    """來源清單應最多回傳 5 個不重複項目。"""
    resources = [{"document_name": f"doc-{i}.pdf"} for i in range(8)]
    dify_resp = {
        "answer": "答案",
        "conversation_id": "conv-sources",
        "metadata": {"retriever_resources": resources},
    }
    response, _ = adapt(dify_resp)
    assert len(response.sources) <= 5


# ---------------------------------------------------------------------------
# _derive_action() 獨立測試
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status,expected",
    [
        ("needs_clarification", "請提供更多資訊"),
        ("clarify", "請提供更多資訊"),
        ("out_of_scope", "請填寫聯絡表單"),
        ("oos", "請填寫聯絡表單"),
        ("escalate_to_human", "請填寫聯絡表單"),
        ("ok", None),
        ("", None),
        ("unknown_value", None),
    ],
)
def test_derive_action_mapping(status, expected):
    """_derive_action 應將已知 status 映射為正確的 action 字串。"""
    assert _derive_action(status) == expected


# ---------------------------------------------------------------------------
# _extract_sources() 獨立測試
# ---------------------------------------------------------------------------


def test_extract_sources_empty_metadata():
    """無 metadata 時應回傳空清單。"""
    assert _extract_sources({}) == []


def test_extract_sources_uses_dataset_name_fallback():
    """當 document_name 不存在時應回退使用 dataset_name。"""
    dify_resp = {
        "metadata": {
            "retriever_resources": [{"dataset_name": "resume-dataset", "score": 0.9}]
        }
    }
    sources = _extract_sources(dify_resp)
    assert "resume-dataset" in sources
