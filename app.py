"""ResumeMate Gradio 應用程式

提供 AI 履歷問答介面
"""

import logging
import sys
import os
from typing import Any

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

from src.backend.models import Question  # noqa: E402
from src.backend.dify import DifyProcessor  # noqa: E402
from src.backend.tools.contact import (  # noqa: E402
    ContactManager,
    generate_contact_request_message,
    is_contact_info_input,
)

# 設定日誌
from src.backend.logging_config import configure_logging  # noqa: E402

# 從環境變數讀取日誌配置
LOG_CONSOLE_LEVEL = os.getenv("LOG_CONSOLE_LEVEL", "INFO")
LOG_FILE_LEVEL = os.getenv("LOG_FILE_LEVEL", "DEBUG")
LOG_FILE = os.getenv("LOG_FILE", "logs/resumemate.log")

configure_logging(
    console_level=LOG_CONSOLE_LEVEL,
    file_level=LOG_FILE_LEVEL,
    log_file=LOG_FILE,
)

logger = logging.getLogger(__name__)

# 初始化處理器
processor: DifyProcessor | None
try:
    processor = DifyProcessor()
    logger.info("DifyProcessor 初始化成功")
except Exception as e:
    logger.error(f"初始化處理器失敗: {e}")
    processor = None

# 初始化聯絡資訊管理器
contact_manager = ContactManager()

# 語言配置 - 僅中文
TEXTS = {
    "title": "🤖 ResumeMate - AI 履歷助手",
    "description": "這是一個由 Dify Chatflow 驅動的 AI 履歷助手。您可以詢問關於我的技能、經驗、教育、聯絡資訊等問題。",
    "chat_label": "對話",
    "chat_placeholder": "目前還沒有對話記錄...",
    "input_label": "您的問題",
    "input_placeholder": "例如：你的工作經驗？",
    "send_button": "發送",
    "examples_label": "範例問題",
    "examples": [
        "介紹一下自己",
        "你的學經歷？",
        "你擅長的技術？",
        "偏好的工作類型？",
        "如何聯絡你？",
    ],
    "thinking": "正在思考您的問題...",
    "processing": "處理中...",
    "clarify_title": "補充資訊（當系統需要更多資訊時顯示）",
    "clarify_label": "請補充資訊後直接送出",
    "clarify_placeholder": "例如：公司名稱、年份、職稱、專案名稱...",
    "clarify_submit": "送出補充",
    "status_title": "系統狀態",
    "refresh_button": "刷新狀態",
    "low_confidence_hint": "\n\n💡 提示：此回答的可信度較低，建議使用更詳細的提問。",
    "system_error": "抱歉，系統初始化失敗，請稍後再試。",
    "empty_input": "請輸入您的問題。",
    "processing_error": "抱歉，處理您的問題時發生錯誤：",
}


async def stream_process_question(user_input: str, history: list, conv_id: str = ""):
    """
    用於 streaming 輸出的處理函數，支援對話式聯絡資訊收集。
    最終 yield 為 4-tuple (history, action_md, clarify_row, new_conv_id)。
    """
    texts = TEXTS

    if not processor:
        yield (
            history + [{"role": "assistant", "content": texts["system_error"]}],
            gr.update(visible=False),
            gr.update(visible=False),
            conv_id,
        )
        return

    if not user_input.strip():
        yield (
            history + [{"role": "assistant", "content": texts["empty_input"]}],
            gr.update(visible=False),
            gr.update(visible=False),
            conv_id,
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
        _, message, _ = contact_manager.process_contact_input(
            user_input, original_question
        )

        final_history = history + [{"role": "assistant", "content": message}]
        yield (
            final_history,
            gr.update(visible=False),
            gr.update(visible=False),
            conv_id,
        )
        return

    try:
        # 先顯示 "正在思考..." 的訊息
        thinking_history = history + [
            {"role": "assistant", "content": texts["thinking"]}
        ]
        yield (
            thinking_history,
            gr.update(visible=False),
            gr.update(visible=False),
            conv_id,
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

        response, new_conv_id = await processor.process_question(question, conv_id)

        answer = response.answer or ""

        # 先顯示回答文字
        current_text = answer.strip()
        streaming_history = history + [{"role": "assistant", "content": current_text}]
        yield (
            streaming_history,
            gr.update(visible=False),
            gr.update(visible=False),
            conv_id,
        )

        # 低信心提示
        if response.confidence < 0.3:
            final_answer = current_text.strip() + str(texts["low_confidence_hint"])
            final_history = history + [{"role": "assistant", "content": final_answer}]
            yield (
                final_history,
                gr.update(visible=False),
                gr.update(visible=False),
                conv_id,
            )

        # 根據 SystemResponse.action 決定 UI 呈現
        action_text = ""
        show_clarify = False

        action = (response.action or "").strip()
        meta = response.metadata or {}

        if action == "請提供更多資訊":
            show_clarify = True
            missing_raw = meta.get("missing_fields") or []
            clarify_examples_raw = meta.get("clarify_examples") or []
            missing = [str(item) for item in missing_raw]
            clarify_examples = [str(item) for item in clarify_examples_raw]
            bullet_missing = (
                "、".join(missing) if missing else "必要細節（公司/年份/職稱等）"
            )
            bullet_examples = (
                "；".join(clarify_examples)
                if clarify_examples
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
            final_history = history + [{"role": "assistant", "content": final_answer}]
            # 最終 yield 含 new_conv_id
            yield (
                final_history,
                gr.update(visible=False),
                gr.update(visible=False),
                new_conv_id,
            )
            return

        # 最終回應包含所有 UI 狀態與更新後的 conversation_id
        final_history = history + [
            {
                "role": "assistant",
                "content": (
                    final_answer if response.confidence < 0.3 else current_text.strip()
                ),
            }
        ]
        yield (
            final_history,
            gr.update(value=action_text, visible=bool(action_text)),
            gr.update(visible=show_clarify),
            new_conv_id,
        )

    except Exception as e:
        logging.getLogger(__name__).error(f"處理問題時發生錯誤: {e}")
        error_msg = f"{texts['processing_error']}{str(e)}"
        error_history = history + [{"role": "assistant", "content": error_msg}]
        yield (
            error_history,
            gr.update(visible=False),
            gr.update(visible=False),
            conv_id,
        )


def get_system_status() -> str:
    """取得系統狀態"""
    if not processor:
        return "❌ 系統未初始化"

    client = processor._client
    return f"""
**系統狀態**: ✅ 正常運行
**後端**: Dify Chatflow
**API Base**: {client.api_base}
**User**: {client.user}
    """.strip()


def create_gradio_interface():
    """
    Create the Gradio interface for the application.
    """

    custom_css = """
    /* 匹配前端的字體設定 - 僅針對 gradio-app 組件 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&family=Noto+Sans+TC:wght@400;500;700&display=swap');

    /* 限制字體樣式僅應用於 Gradio 容器內部 */
    .gradio-container *,
    .gradio-container {
        font-family: "Inter", "Noto Sans TC", sans-serif !important;
    }

    /* 主容器樣式匹配前端 - 確保不影響外部頁面背景 */
    .gradio-container {
        max-width: 800px !important;
        margin: auto !important;
        color: #d1d5db !important;
        /* 移除背景樣式，讓外部頁面控制背景 */
        background: transparent !important;
        padding: 0.5rem !important;
        border-radius: 1rem !important;
    }

    .gradio-container p {
        font-size: 0.9rem !important;
    }

    /* 玻璃效果僅應用於 Gradio 內部組件 */
    .gradio-container .glass-effect {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }

    /* 文字漸層效果僅應用於 Gradio 內部 */
    .gradio-container .text-gradient {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
    }

    /* 標題樣式僅應用於 Gradio 內部 */
    .gradio-container h1,
    .gradio-container h2,
    .gradio-container h3 {
        color: #d1d5db !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        text-align: left !important;
        margin: 1rem 0 !important;
    }

    /* 特別針對主標題的樣式 */
    .gradio-container h1:first-of-type {
        font-size: 2rem !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
    }

    /* Gradio 組件樣式調整 */
    .gradio-container .chat-message {
        border-radius: 10px !important;
        padding: 10px !important;
        margin: 5px 0 !important;
    }

    /* 針對 Gradio 4.0+ 的 Chatbot 組件樣式 */
    .gradio-container .message-wrap {
        margin-bottom: 1rem !important;
    }

    /* 用戶消息靠右對齊 */
    .gradio-container .message-wrap[data-testid*="user"] .message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        max-width: 80% !important;
        border-radius: 18px 18px 4px 18px !important;
        font-family: "Inter", "Noto Sans TC", sans-serif !important;
    }

    /* AI 回覆靠左對齊 - 使用玻璃效果 */
    .gradio-container .message-wrap[data-testid*="bot"] .message,
    .gradio-container .message-wrap[data-testid*="assistant"] .message {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: #d1d5db !important;
        margin-left: 0 !important;
        margin-right: auto !important;
        max-width: 80% !important;
        border-radius: 18px 18px 18px 4px !important;
        font-family: "Inter", "Noto Sans TC", sans-serif !important;
    }

    /* 深色主題支援 */
    .gradio-container.dark .message-wrap[data-testid*="bot"] .message,
    .gradio-container.dark .message-wrap[data-testid*="assistant"] .message {
        background: rgba(255, 255, 255, 0.1) !important;
        color: #d1d5db !important;
    }

    /* 輸入框樣式匹配前端 - 僅影響 Gradio 內部 */
    .gradio-container input,
    .gradio-container textarea {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: #d1d5db !important;
        font-family: "Inter", "Noto Sans TC", sans-serif !important;
    }

    /* 按鈕樣式匹配前端 - 僅影響 Gradio 內部 */
    .gradio-container .btn-primary,
    .gradio-container button[variant="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        color: white !important;
        font-family: "Inter", "Noto Sans TC", sans-serif !important;
    }

    /* 其他按鈕使用玻璃效果 - 僅影響 Gradio 內部 */
    .gradio-container button:not([variant="primary"]) {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: #d1d5db !important;
        font-family: "Inter", "Noto Sans TC", sans-serif !important;
    }

    /* 訊息內容樣式優化 - 僅影響 Gradio 內部 */
    .gradio-container .message p {
        margin-bottom: 0.5rem !important;
    }

    .gradio-container .message p:last-child {
        margin-bottom: 0 !important;
    }

    /* 載入狀態樣式 - 僅影響 Gradio 內部 */
    .gradio-container .message-wrap.generating .message {
        opacity: 0.8 !important;
        animation: gradio-pulse 1.5s ease-in-out infinite !important;
    }

    @keyframes gradio-pulse {
        0%, 100% { opacity: 0.8; }
        50% { opacity: 1; }
    }

    /* 按鈕載入狀態 - 僅影響 Gradio 內部 */
    .gradio-container .btn-loading {
        opacity: 0.6 !important;
        cursor: not-allowed !important;
    }

    /* Scrollbar 樣式僅應用於 Gradio 內部的滾動條 */
    .gradio-container ::-webkit-scrollbar {
        width: 8px !important;
    }
    .gradio-container ::-webkit-scrollbar-track {
        background: #1f2937 !important;
    }
    .gradio-container ::-webkit-scrollbar-thumb {
        background: #4b5563 !important;
        border-radius: 4px !important;
    }
    """

    # 創建強制深色模式主題
    dark_theme = gr.themes.Soft(
        primary_hue="violet",
        secondary_hue="blue",
    ).set(
        # 強制深色模式背景
        background_fill_primary="*neutral_950",
        background_fill_secondary="*neutral_900",
        block_background_fill="*neutral_900",
        # 文字顏色
        body_text_color="*neutral_200",
        body_text_color_subdued="*neutral_400",
        # 輸入框樣式
        input_background_fill="*neutral_800",
        input_border_color="*neutral_600",
        # 按鈕樣式
        button_primary_background_fill="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        button_primary_background_fill_hover="linear-gradient(135deg, #5a6fd8 0%, #694396 100%)",
        button_secondary_background_fill="*neutral_700",
        button_secondary_background_fill_hover="*neutral_600",
    )

    with gr.Blocks(
        title="ResumeMate - AI 履歷助手",
        css=custom_css,
        theme=dark_theme,
        js="""
        function() {
            // 強制深色模式
            document.documentElement.setAttribute('data-theme', 'dark');
            document.body.classList.add('dark');

            // 防止主題自動切換
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'attributes' &&
                        mutation.attributeName === 'data-theme') {
                        const theme = document.documentElement.getAttribute('data-theme');
                        if (theme !== 'dark') {
                            document.documentElement.setAttribute('data-theme', 'dark');
                            document.body.classList.add('dark');
                        }
                    }
                });
            });

            observer.observe(document.documentElement, {
                attributes: true,
                attributeFilter: ['data-theme']
            });
        }
        """,
    ) as app:
        # 標題區域
        # title_md = gr.Markdown(TEXTS["title"])
        # description_md = gr.Markdown(TEXTS["description"])

        chatbot = gr.Chatbot(
            label=TEXTS["chat_label"],
            height=400,
            placeholder=TEXTS["chat_placeholder"],
            type="messages",
            allow_tags=False,
        )

        # --- Action Bar（依 action 顯示） ---
        action_md = gr.Markdown(visible=False)

        with gr.Row():
            user_input = gr.Textbox(
                label=TEXTS["input_label"],
                placeholder=TEXTS["input_placeholder"],
                scale=4,
            )
            send_btn = gr.Button(TEXTS["send_button"], variant="primary", scale=1)

        # 範例問題
        gr.Examples(
            examples=TEXTS["examples"],
            inputs=user_input,
            label=TEXTS["examples_label"],
        )

        # --- Clarify 區塊（需要補充資訊時顯示） ---
        with gr.Accordion(
            TEXTS["clarify_title"], open=True, visible=False
        ) as clarify_row:
            clarify_input = gr.Textbox(
                label=TEXTS["clarify_label"],
                placeholder=TEXTS["clarify_placeholder"],
            )
            clarify_submit = gr.Button(TEXTS["clarify_submit"])

        # 系統狀態
        with gr.Accordion(TEXTS["status_title"], open=False, visible=False):
            status_display = gr.Markdown(get_system_status())
            refresh_btn = gr.Button(TEXTS["refresh_button"])

        # --- conversation_id 狀態（Dify 多輪對話） ---
        conv_state = gr.State("")

        # --- 事件處理（支援 streaming） ---
        async def handle_user_input_with_streaming(user_text, history, conv_id):
            """處理用戶輸入的包裝函數，支援 streaming"""
            if user_text.strip():
                updated_history = history + [{"role": "user", "content": user_text}]
                yield (
                    "",
                    updated_history,
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(interactive=False, value="處理中..."),
                    conv_id,
                )

                current_conv_id = conv_id
                last_result = None
                async for result in stream_process_question(
                    user_text, updated_history, conv_id
                ):
                    last_result = result
                    if len(result) >= 4:
                        current_conv_id = result[3]
                    yield (
                        "",
                        result[0],
                        result[1],
                        result[2],
                        gr.update(interactive=False, value="處理中..."),
                        current_conv_id,
                    )

                # 最後恢復按鈕
                if last_result:
                    yield (
                        "",
                        last_result[0],
                        last_result[1],
                        last_result[2],
                        gr.update(interactive=True, value="發送"),
                        current_conv_id,
                    )
            else:
                async for result in stream_process_question(
                    user_text, history, conv_id
                ):
                    current_conv_id = result[3] if len(result) >= 4 else conv_id
                    yield (
                        "",
                        result[0],
                        result[1],
                        result[2],
                        gr.update(interactive=True, value="發送"),
                        current_conv_id,
                    )

        send_btn.click(
            fn=handle_user_input_with_streaming,
            inputs=[user_input, chatbot, conv_state],
            outputs=[
                user_input,
                chatbot,
                action_md,
                clarify_row,
                send_btn,
                conv_state,
            ],
        )
        user_input.submit(
            fn=handle_user_input_with_streaming,
            inputs=[user_input, chatbot, conv_state],
            outputs=[
                user_input,
                chatbot,
                action_md,
                clarify_row,
                send_btn,
                conv_state,
            ],
        )

        async def handle_clarify_with_streaming(
            clarify_text: str, history: list[dict[str, Any]], conv_id: str
        ):
            """處理補充資訊的包裝函數"""
            if clarify_text.strip():
                updated_history = history + [{"role": "user", "content": clarify_text}]
                yield (
                    "",
                    updated_history,
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(interactive=False, value="處理中..."),
                    conv_id,
                )

                current_conv_id = conv_id
                last_result = None
                async for result in stream_process_question(
                    clarify_text, updated_history, conv_id
                ):
                    last_result = result
                    if len(result) >= 4:
                        current_conv_id = result[3]
                    yield (
                        "",
                        result[0],
                        result[1],
                        result[2],
                        gr.update(interactive=False, value="處理中..."),
                        current_conv_id,
                    )

                if last_result:
                    yield (
                        "",
                        last_result[0],
                        last_result[1],
                        last_result[2],
                        gr.update(interactive=True, value="送出補充"),
                        current_conv_id,
                    )
            else:
                async for result in stream_process_question(
                    clarify_text, history, conv_id
                ):
                    current_conv_id = result[3] if len(result) >= 4 else conv_id
                    yield (
                        "",
                        result[0],
                        result[1],
                        result[2],
                        gr.update(interactive=True, value="送出補充"),
                        current_conv_id,
                    )

        clarify_submit.click(
            fn=handle_clarify_with_streaming,
            inputs=[clarify_input, chatbot, conv_state],
            outputs=[
                clarify_input,
                chatbot,
                action_md,
                clarify_row,
                clarify_submit,
                conv_state,
            ],
        )

        refresh_btn.click(fn=get_system_status, outputs=status_display)

    return app


def main():
    """主函數"""
    logger.info("啟動 ResumeMate Gradio 應用程式")

    app = create_gradio_interface()

    server_name = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
    try:
        server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    except ValueError:
        server_port = 7860

    # 確定是否使用共享模式
    use_share = os.getenv("GRADIO_SHARE", "").lower() in ("true", "1", "yes")

    model = os.getenv("LITELLM_PROXY_MODEL", "github_copilot/gpt-4o")
    logger.info(f"使用的代理模型: {model}")

    # 啟動應用程式
    if use_share:
        # 使用 Gradio 的共享連結（允許外部訪問）
        logger.info("使用 Gradio 共享模式，生成公開連結...")
        app.launch(
            server_name=server_name,
            server_port=server_port,
            share=True,
            debug=True,
            quiet=False,
        )
    else:
        # 嘗試在指定埠啟動，如果失敗則讓 Gradio 自動找可用埠
        max_port_attempts = 10
        for port_offset in range(max_port_attempts):
            try_port = server_port + port_offset
            try:
                logger.info(f"在所有網絡介面啟動應用 ({server_name}:{try_port})...")
                app.launch(
                    server_name=server_name,
                    server_port=try_port,
                    share=False,
                    debug=True,
                    quiet=False,
                )
                break  # 成功啟動，跳出迴圈
            except OSError:
                if port_offset < max_port_attempts - 1:
                    logger.warning(f"埠 {try_port} 被佔用，嘗試下一個埠...")
                else:
                    # 所有埠都失敗，啟用共享模式
                    logger.warning("無法找到可用埠，啟用共享連結...")
                    app.launch(
                        server_name=server_name,
                        share=True,
                        debug=True,
                        quiet=False,
                    )


if __name__ == "__main__":
    main()
