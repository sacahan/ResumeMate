"""ResumeMate Gradio 應用程式

提供 AI 履歷問答介面
"""

import asyncio
import logging
import sys
import os

# 修復 Gradio 環境變數問題
if os.getenv("GRADIO_SERVER_PORT") == "":
    os.environ.pop("GRADIO_SERVER_PORT", None)

# 確保其他 Gradio 環境變數的正確性
gradio_env_vars = ["GRADIO_SERVER_NAME", "GRADIO_SHARE", "GRADIO_DEBUG"]
for var in gradio_env_vars:
    if os.getenv(var) == "":
        os.environ.pop(var, None)

# 添加 src 目錄到 Python 路徑（必須在 gradio 導入之前）
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# 重要：gradio 必須在環境變數修復後才能導入
import gradio as gr  # noqa: E402

from agents import trace  # noqa: E402
from backend.models import Question  # noqa: E402
from backend import ResumeMateProcessor  # noqa: E402
from backend.tools.contact import (  # noqa: E402
    ContactManager,
    generate_contact_request_message,
    is_contact_info_input,
)


# 追蹤功能已啟用標記
TRACING_AVAILABLE = True

# 設定日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 初始化處理器
try:
    processor = ResumeMateProcessor()
    logger.info("ResumeMate 處理器初始化成功")
except Exception as e:
    logger.error(f"初始化處理器失敗: {e}")
    processor = None

# 初始化聯絡資訊管理器
contact_manager = ContactManager()


async def stream_process_question(user_input: str, history: list):
    """
    用於 streaming 輸出的處理函數，支援對話式聯絡資訊收集
    """
    if not processor:
        yield (
            history
            + [{"role": "assistant", "content": "抱歉，系統初始化失敗，請稍後再試。"}],
            gr.update(visible=False),
            gr.update(visible=False),
        )
        return

    if not user_input.strip():
        yield (
            history + [{"role": "assistant", "content": "請輸入您的問題。"}],
            gr.update(visible=False),
            gr.update(visible=False),
        )
        return

    # 檢查是否是聯絡資訊輸入
    if is_contact_info_input(user_input):
        # 從歷史中找到最近的問題
        original_question = None
        for item in reversed(history):
            if item["role"] == "user" and not is_contact_info_input(item["content"]):
                original_question = item["content"]
                break

        # 處理聯絡資訊
        success, message, contact_info = contact_manager.process_contact_input(
            user_input, original_question
        )

        final_history = history + [{"role": "assistant", "content": message}]
        yield (
            final_history,
            gr.update(visible=False),
            gr.update(visible=False),
        )
        return

    try:
        # 先顯示 "正在思考..." 的訊息
        thinking_history = history + [
            {"role": "assistant", "content": "正在思考您的問題..."}
        ]
        yield (
            thinking_history,
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
        )

        question = Question(
            text=user_input.strip(),
            language="zh-TW",
            context=(
                [item["content"] for item in history[-6:] if item["role"] == "user"]
                if history
                else None
            ),
        )

        with trace(
            f"ResumeMate: {user_input[:10]}...",
            metadata={"session_id": str(id(history))},
        ):
            response = await processor.process_question(question)

            answer = response.answer or ""

            # 模擬 streaming 效果 - 逐字顯示
            current_text = ""
            words = answer.split()

            for i, word in enumerate(words):
                current_text += word + " "
                # 每隔幾個字更新一次顯示
                if i % 3 == 0 or i == len(words) - 1:
                    streaming_history = history + [
                        {"role": "assistant", "content": current_text.strip()}
                    ]
                    yield (
                        streaming_history,
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(visible=False),
                    )
                    # 短暫延遲模擬打字效果
                    await asyncio.sleep(0.1)

            # 低信心提示
            if response.confidence < 0.3:
                final_answer = (
                    current_text.strip()
                    + "\n\n💡 提示：此回答的可信度較低，建議使用更詳細的提問。"
                )
                final_history = history + [
                    {"role": "assistant", "content": final_answer}
                ]
                yield (
                    final_history,
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                )

            # 根據 SystemResponse.action 決定 UI 呈現
            action_text = ""
            show_clarify = False

            action = (response.action or "").strip()
            meta = response.metadata or {}

            if action == "請提供更多資訊":
                show_clarify = True
                missing = meta.get("missing_fields") or []
                ex = meta.get("clarify_examples") or []
                bullet_missing = (
                    "、".join(missing) if missing else "必要細節（公司/年份/職稱等）"
                )
                bullet_examples = (
                    "；".join(ex)
                    if ex
                    else "例如：請補充「2023 在 台灣之星 擔任什麼職務與職責？」"
                )
                action_text = (
                    f"🔎 需要補充資訊：請提供 **{bullet_missing}**。{bullet_examples}"
                )

            elif (
                action == "請填寫聯絡表單"
                or str(meta.get("status", "")).lower() == "escalate_to_human"
                or str(meta.get("status", "")).lower() == "out_of_scope"
            ):
                # 直接在對話中顯示聯絡資訊請求
                contact_request_msg = generate_contact_request_message()
                final_answer = current_text.strip() + "\n\n" + contact_request_msg
                final_history = history + [
                    {"role": "assistant", "content": final_answer}
                ]
                yield (
                    final_history,
                    gr.update(visible=False),
                    gr.update(visible=False),
                )
                return

            # 最終回應包含所有 UI 狀態
            final_history = history + [
                {
                    "role": "assistant",
                    "content": (
                        final_answer
                        if response.confidence < 0.3
                        else current_text.strip()
                    ),
                }
            ]
            yield (
                final_history,
                gr.update(value=action_text, visible=bool(action_text)),
                gr.update(visible=show_clarify),
            )

    except Exception as e:
        logging.getLogger(__name__).error(f"處理問題時發生錯誤: {e}")
        error_msg = f"抱歉，處理您的問題時發生錯誤：{str(e)}"
        error_history = history + [{"role": "assistant", "content": error_msg}]
        yield (
            error_history,
            gr.update(visible=False),
            gr.update(visible=False),
        )


def get_system_status() -> str:
    """取得系統狀態"""
    if not processor:
        return "❌ 系統未初始化"

    try:
        info = processor.get_system_info()

        # 添加追蹤狀態
        tracing_status = "✅ 已啟用" if TRACING_AVAILABLE else "❌ 未啟用"

        status_text = f"""
**系統狀態**: ✅ 正常運行
**版本**: {info["version"]}
**資料庫**: {info["database"]["document_count"]} 個文件
**代理人**: Analysis Agent ✅, Evaluate Agent ✅
**追蹤功能**: {tracing_status}
        """
        return status_text.strip()
    except Exception as e:
        return f"❌ 系統狀態檢查失敗: {e}"


def create_gradio_interface():
    """
    Create the Gradio interface for the application.
    """

    custom_css = """
    .gradio-container { max-width: 800px !important; margin: auto !important; }
    .chat-message { border-radius: 10px !important; padding: 10px !important; margin: 5px 0 !important; }

    /* 針對 Gradio 4.0+ 的 Chatbot 組件樣式 */
    .message-wrap {
        margin-bottom: 1rem !important;
    }

    /* 用戶消息靠右對齊 */
    .message-wrap[data-testid*="user"] .message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        max-width: 80% !important;
        border-radius: 18px 18px 4px 18px !important;
    }

    /* AI 回覆靠左對齊 */
    .message-wrap[data-testid*="bot"] .message,
    .message-wrap[data-testid*="assistant"] .message {
        background: #f1f3f4 !important;
        color: #333 !important;
        margin-left: 0 !important;
        margin-right: auto !important;
        max-width: 80% !important;
        border-radius: 18px 18px 18px 4px !important;
    }

    /* 深色主題支援 */
    .dark .message-wrap[data-testid*="bot"] .message,
    .dark .message-wrap[data-testid*="assistant"] .message {
        background: #374151 !important;
        color: #f9fafb !important;
    }

    /* 訊息內容樣式優化 */
    .message p {
        margin-bottom: 0.5rem !important;
    }

    .message p:last-child {
        margin-bottom: 0 !important;
    }

    /* 載入狀態樣式 */
    .message-wrap.generating .message {
        opacity: 0.8 !important;
        animation: pulse 1.5s ease-in-out infinite !important;
    }

    @keyframes pulse {
        0%, 100% { opacity: 0.8; }
        50% { opacity: 1; }
    }

    /* 按鈕載入狀態 */
    .btn-loading {
        opacity: 0.6 !important;
        cursor: not-allowed !important;
    }
    """

    with gr.Blocks(
        title="ResumeMate - AI 履歷助手", css=custom_css, theme=gr.themes.Soft()
    ) as app:
        gr.Markdown(
            """
        # 🤖 ResumeMate - AI 履歷助手
        這是一個由 RAG 技術驅動的 AI 代理人展示。您可以詢問關於我的技能、經驗、教育、聯絡資訊等問題。
        """
        )

        chatbot = gr.Chatbot(
            label="對話",
            height=400,
            placeholder="目前還沒有對話記錄...",
            type="messages",
        )

        # --- Action Bar（依 action 顯示） ---
        action_md = gr.Markdown(visible=False)

        with gr.Row():
            user_input = gr.Textbox(
                label="您的問題", placeholder="例如：你有什麼程式設計經驗？", scale=4
            )
            send_btn = gr.Button("發送", variant="primary", scale=1)

        # 範例
        with gr.Row():
            gr.Examples(
                examples=[
                    "先介紹一下自己",
                    "你有什麼技能？",
                    "你的工作經驗如何？",
                    "你的教育背景是什麼？",
                    "如何聯絡你？",
                ],
                inputs=user_input,
                label="範例問題",
            )

        # --- Clarify 區塊（需要補充資訊時顯示） ---
        with gr.Accordion(
            "補充資訊（當系統需要更多資訊時顯示）", open=True, visible=False
        ) as clarify_row:
            clarify_input = gr.Textbox(
                label="請補充資訊後直接送出",
                placeholder="例如：公司名稱、年份、職稱、專案名稱...",
            )
            clarify_submit = gr.Button("送出補充")

        # 系統狀態
        with gr.Accordion("系統狀態", open=False, visible=False):
            status_display = gr.Markdown(get_system_status())
            refresh_btn = gr.Button("刷新狀態")

        # --- 事件處理（支援 streaming） ---
        async def handle_user_input_with_streaming(user_text, history):
            """處理用戶輸入的包裝函數，支援 streaming"""
            # 先立即顯示用戶消息並隱藏所有 action UI，同時禁用按鈕
            if user_text.strip():
                updated_history = history + [{"role": "user", "content": user_text}]
                # 第一次 yield：清空輸入框、顯示用戶消息、隱藏 action UI、禁用按鈕
                yield (
                    "",  # 清空輸入框
                    updated_history,  # 更新對話歷史
                    gr.update(visible=False),  # action_md
                    gr.update(visible=False),  # clarify_row
                    gr.update(interactive=False, value="處理中..."),  # 禁用發送按鈕
                )

                # 然後啟動 streaming 處理，傳入完整的對話歷史（包含用戶問題）
                last_result = None
                async for result in stream_process_question(user_text, updated_history):
                    last_result = result
                    if len(result) == 3:
                        # streaming 過程中保持按鈕禁用狀態
                        yield (
                            "",  # 保持輸入框清空
                            result[0],  # 對話歷史
                            result[1],  # action_md
                            result[2],  # clarify_row
                            gr.update(
                                interactive=False, value="處理中..."
                            ),  # 按鈕仍禁用
                        )
                    else:
                        yield (
                            "",
                            result[0],
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(interactive=False, value="處理中..."),
                        )

                # 最後啟用按鈕
                if last_result and len(last_result) == 3:
                    yield (
                        "",
                        last_result[0],
                        last_result[1],
                        last_result[2],
                        gr.update(interactive=True, value="發送"),  # 恢復按鈕
                    )
                elif last_result:
                    yield (
                        "",
                        last_result[0],
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(interactive=True, value="發送"),
                    )
            else:
                # 空輸入的情況
                async for result in stream_process_question(user_text, history):
                    if len(result) == 3:
                        yield (
                            "",
                            result[0],
                            result[1],
                            result[2],
                            gr.update(interactive=True, value="發送"),
                        )
                    else:
                        yield (
                            "",
                            result[0],
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(interactive=True, value="發送"),
                        )

        send_btn.click(
            fn=handle_user_input_with_streaming,
            inputs=[user_input, chatbot],
            outputs=[
                user_input,
                chatbot,
                action_md,
                clarify_row,
                send_btn,
            ],
        )
        user_input.submit(
            fn=handle_user_input_with_streaming,
            inputs=[user_input, chatbot],
            outputs=[
                user_input,
                chatbot,
                action_md,
                clarify_row,
                send_btn,
            ],
        )

        async def handle_clarify_with_streaming(clarify_text, history):
            """處理補充資訊的包裝函數"""
            # 先立即顯示用戶補充的消息並隱藏所有 action UI，同時禁用按鈕
            if clarify_text.strip():
                updated_history = history + [{"role": "user", "content": clarify_text}]
                # 第一次 yield：清空輸入框、顯示用戶消息、隱藏 action UI、禁用按鈕
                yield (
                    "",  # 清空 clarify_input
                    updated_history,  # 更新對話歷史
                    gr.update(visible=False),  # action_md
                    gr.update(visible=False),  # clarify_row
                    gr.update(
                        interactive=False, value="處理中..."
                    ),  # 禁用 clarify 按鈕
                )

                # 然後啟動 streaming 處理，傳入完整的對話歷史（包含補充資訊）
                last_result = None
                async for result in stream_process_question(
                    clarify_text, updated_history
                ):
                    last_result = result
                    if len(result) == 3:
                        # streaming 過程中保持按鈕禁用狀態
                        yield (
                            "",  # 保持輸入框清空
                            result[0],  # 對話歷史
                            result[1],  # action_md
                            result[2],  # clarify_row
                            gr.update(
                                interactive=False, value="處理中..."
                            ),  # 按鈕仍禁用
                        )
                    else:
                        yield (
                            "",
                            result[0],
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(interactive=False, value="處理中..."),
                        )

                # 最後啟用按鈕
                if last_result and len(last_result) == 3:
                    yield (
                        "",
                        last_result[0],
                        last_result[1],
                        last_result[2],
                        gr.update(
                            interactive=True, value="送出補充"
                        ),  # 恢復 clarify 按鈕
                    )
                elif last_result:
                    yield (
                        "",
                        last_result[0],
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(interactive=True, value="送出補充"),
                    )
            else:
                # 空輸入的情況
                async for result in stream_process_question(clarify_text, history):
                    if len(result) == 3:
                        yield (
                            "",
                            result[0],
                            result[1],
                            result[2],
                            gr.update(interactive=True, value="送出補充"),
                        )
                    else:
                        yield (
                            "",
                            result[0],
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(interactive=True, value="送出補充"),
                        )

        clarify_submit.click(
            fn=handle_clarify_with_streaming,
            inputs=[clarify_input, chatbot],
            outputs=[
                clarify_input,
                chatbot,
                action_md,
                clarify_row,
                clarify_submit,
            ],
        )

        refresh_btn.click(fn=get_system_status, outputs=status_display)

    return app


def main():
    """主函數"""
    logger.info("啟動 ResumeMate Gradio 應用程式")

    app = create_gradio_interface()

    # 啟動應用程式
    app.launch(server_name="0.0.0.0", server_port=7860, share=False, debug=True)


if __name__ == "__main__":
    main()
