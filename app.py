"""ResumeMate Gradio 應用程式

提供 AI 履歷問答介面
"""

import asyncio
import logging
import gradio as gr
import sys
import os
from datetime import datetime

# 添加 src 目錄到 Python 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from agents import trace
from backend.models import Question
from backend import ResumeMateProcessor


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


async def stream_process_question(user_input: str, history: list):
    """
    用於 streaming 輸出的處理函數
    """
    if not processor:
        yield (
            history
            + [{"role": "assistant", "content": "抱歉，系統初始化失敗，請稍後再試。"}],
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
        )
        return

    if not user_input.strip():
        yield (
            history + [{"role": "assistant", "content": "請輸入您的問題。"}],
            gr.update(visible=False),
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
            show_contact = False
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
                show_contact = True
                action_text = (
                    "📨 需要人工協助：目前儲備的來源資料不足以保證回覆正確性。是否同意我先記錄原問題並轉交本人回覆？"
                    "請提供一種稱呼與聯絡方式（Email/電話/Line/Telegram 任一），我會儘速回覆。"
                )

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
                gr.update(visible=show_contact),
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
        歡迎使用！可詢問：技能、經驗、教育、聯絡資訊。
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

        # --- Contact 區塊（人工接手/填表） ---
        with gr.Accordion(
            "聯絡方式（需要人工協助時顯示）", open=True, visible=False
        ) as contact_row:
            with gr.Row():
                email = gr.Textbox(label="Email", placeholder="you@example.com")
                phone = gr.Textbox(label="電話", placeholder="09xx-xxx-xxx")
            with gr.Row():
                line_id = gr.Textbox(label="Line ID", placeholder="可擇一提供")
                telegram = gr.Textbox(label="Telegram", placeholder="@handle")
            contact_submit = gr.Button("送出聯絡資訊")

        # 系統狀態
        with gr.Accordion("系統狀態", open=False):
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
                    gr.update(visible=False),  # contact_row
                    gr.update(visible=False),  # clarify_row
                    gr.update(interactive=False, value="處理中..."),  # 禁用發送按鈕
                )

                # 然後啟動 streaming 處理，傳入完整的對話歷史（包含用戶問題）
                last_result = None
                async for result in stream_process_question(user_text, updated_history):
                    last_result = result
                    if len(result) == 4:
                        # streaming 過程中保持按鈕禁用狀態
                        yield (
                            "",  # 保持輸入框清空
                            result[0],  # 對話歷史
                            result[1],  # action_md
                            result[2],  # contact_row
                            result[3],  # clarify_row
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
                            gr.update(visible=False),
                            gr.update(interactive=False, value="處理中..."),
                        )

                # 最後啟用按鈕
                if last_result and len(last_result) == 4:
                    yield (
                        "",
                        last_result[0],
                        last_result[1],
                        last_result[2],
                        last_result[3],
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
                    if len(result) == 4:
                        yield (
                            "",
                            result[0],
                            result[1],
                            result[2],
                            result[3],
                            gr.update(interactive=True, value="發送"),
                        )
                    else:
                        yield (
                            "",
                            result[0],
                            gr.update(visible=False),
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
                contact_row,
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
                contact_row,
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
                    gr.update(visible=False),  # contact_row
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
                    if len(result) == 4:
                        # streaming 過程中保持按鈕禁用狀態
                        yield (
                            "",  # 保持輸入框清空
                            result[0],  # 對話歷史
                            result[1],  # action_md
                            result[2],  # contact_row
                            result[3],  # clarify_row
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
                            gr.update(visible=False),
                            gr.update(interactive=False, value="處理中..."),
                        )

                # 最後啟用按鈕
                if last_result and len(last_result) == 4:
                    yield (
                        "",
                        last_result[0],
                        last_result[1],
                        last_result[2],
                        last_result[3],
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
                    if len(result) == 4:
                        yield (
                            "",
                            result[0],
                            result[1],
                            result[2],
                            result[3],
                            gr.update(interactive=True, value="送出補充"),
                        )
                    else:
                        yield (
                            "",
                            result[0],
                            gr.update(visible=False),
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
                contact_row,
                clarify_row,
                clarify_submit,
            ],
        )

        # 聯絡資訊送出（將確認訊息寫回聊天，並可隱藏表單）
        def handle_contact_submit(email_v, phone_v, line_v, tg_v, history):
            ack = "👍 已收到您的聯絡方式："
            items = []
            if email_v:
                items.append(f"Email: {email_v}")
            if phone_v:
                items.append(f"電話: {phone_v}")
            if line_v:
                items.append(f"Line: {line_v}")
            if tg_v:
                items.append(f"Telegram: {tg_v}")
            ack += "；".join(items) if items else "（未填寫）"
            history = history + [{"role": "assistant", "content": ack}]

            # 若 ./contact/list.txt 不存在應該自行建立
            if not os.path.exists("./contact/list.txt"):
                os.makedirs(os.path.dirname("./contact/list.txt"), exist_ok=True)

            with open("./contact/list.txt", "a") as f:
                f.write(f"寫入時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Email: {email_v}\n")
                f.write(f"電話: {phone_v}\n")
                f.write(f"Line: {line_v}\n")
                f.write(f"Telegram: {tg_v}\n")
                f.write("\n")

            return (
                history,
                gr.update(value="✅ 已登記聯絡方式，我們會儘速回覆。", visible=True),
                gr.update(visible=False),
            )

        contact_submit.click(
            fn=handle_contact_submit,
            inputs=[email, phone, line_id, telegram, chatbot],
            outputs=[chatbot, action_md, contact_row],
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
