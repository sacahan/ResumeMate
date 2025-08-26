"""ResumeMate Gradio 應用程式

提供 AI 履歷問答介面
"""

import asyncio
import logging
import gradio as gr
import sys
import os

# 添加 src 目錄到 Python 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from backend.models import Question
from backend.processor import ResumeMateProcessor

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


async def process_user_question(user_input: str, history: list) -> tuple:
    """處理使用者問題

    Args:
        user_input: 使用者輸入
        history: 對話歷史

    Returns:
        tuple: (回應, 更新的歷史)
    """
    if not processor:
        error_msg = "抱歉，系統初始化失敗，請稍後再試。"
        history.append([user_input, error_msg])
        return "", history

    if not user_input.strip():
        error_msg = "請輸入您的問題。"
        history.append([user_input, error_msg])
        return "", history

    try:
        # 創建問題物件
        question = Question(
            text=user_input.strip(),
            language="zh-TW",
            context=[item[0] for item in history[-3:]]
            if history
            else None,  # 最近3輪對話作為上下文
        )

        # 處理問題
        response = await processor.process_question(question)

        # 格式化回應
        answer = response.answer

        # 如果有來源，添加來源資訊
        if response.sources:
            answer += f"\n\n📚 參考來源: {', '.join(response.sources)}"

        # 添加信心分數（僅供調試）
        if response.confidence < 0.3:
            answer += "\n\n💡 提示：此回答的可信度較低，建議進一步確認。"

        # 更新歷史
        history.append([user_input, answer])

        return "", history

    except Exception as e:
        logger.error(f"處理問題時發生錯誤: {e}")
        error_msg = f"抱歉，處理您的問題時發生錯誤：{str(e)}"
        history.append([user_input, error_msg])
        return "", history


def get_system_status() -> str:
    """取得系統狀態"""
    if not processor:
        return "❌ 系統未初始化"

    try:
        info = processor.get_system_info()
        status_text = f"""
**系統狀態**: ✅ 正常運行
**版本**: {info["version"]}
**資料庫**: {info["database"]["document_count"]} 個文件
**代理人**: Analysis Agent ✅, Evaluate Agent ✅
        """
        return status_text.strip()
    except Exception as e:
        return f"❌ 系統狀態檢查失敗: {e}"


def create_gradio_interface():
    """創建 Gradio 介面"""

    # 自定義 CSS
    custom_css = """
    .gradio-container {
        max-width: 800px !important;
        margin: auto !important;
    }
    .chat-message {
        border-radius: 10px !important;
        padding: 10px !important;
        margin: 5px 0 !important;
    }
    """

    with gr.Blocks(
        title="ResumeMate - AI 履歷助手", css=custom_css, theme=gr.themes.Soft()
    ) as app:
        gr.Markdown("""
        # 🤖 ResumeMate - AI 履歷助手

        歡迎使用 ResumeMate！我是您的 AI 履歷助手，可以回答關於我的：
        - 🎯 專業技能和經驗
        - 💼 工作經歷和專案
        - 🎓 教育背景
        - 📞 聯絡資訊

        請隨時提問，我會盡力為您解答！
        """)

        # 聊天介面
        chatbot = gr.Chatbot(
            label="對話", height=400, placeholder="目前還沒有對話記錄..."
        )

        with gr.Row():
            user_input = gr.Textbox(
                label="您的問題", placeholder="例如：你有什麼程式設計經驗？", scale=4
            )
            send_btn = gr.Button("發送", variant="primary", scale=1)

        # 範例問題
        with gr.Row():
            gr.Examples(
                examples=[
                    "你好，請介紹一下自己",
                    "你有什麼技能？",
                    "你的工作經驗如何？",
                    "你的教育背景是什麼？",
                    "如何聯絡你？",
                ],
                inputs=user_input,
                label="範例問題",
            )

        # 系統狀態
        with gr.Accordion("系統狀態", open=False):
            status_display = gr.Markdown(get_system_status())
            refresh_btn = gr.Button("刷新狀態")

        # 事件處理
        def handle_user_input(user_text, history):
            return asyncio.run(process_user_question(user_text, history))

        # 綁定事件
        send_btn.click(
            fn=handle_user_input,
            inputs=[user_input, chatbot],
            outputs=[user_input, chatbot],
        )

        user_input.submit(
            fn=handle_user_input,
            inputs=[user_input, chatbot],
            outputs=[user_input, chatbot],
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
