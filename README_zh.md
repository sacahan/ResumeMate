# ResumeMate

ResumeMate 是一個 AI 驅動的履歷代理人平台，結合靜態履歷展示與 AI 互動問答功能。

🚀 **線上展示**: [https://huggingface.co/spaces/sacahan/resumemate-chat](https://huggingface.co/spaces/sacahan/resumemate-chat)

## 核心特色

- **智慧問答**：透過 RAG 技術實現個人化的履歷內容對話
- **對話式聯絡**：自然語言收集聯絡資訊，適合 iframe 嵌入
- **雙語支援**：中英文介面無縫切換
- **簡潔展示**：清晰呈現個人資料、經歷與專長

## 技術架構

- **前端**：HTML + Tailwind CSS，響應式設計
- **後端**：Python + Gradio + OpenAI SDK
- **資料庫**：ChromaDB 向量資料庫
- **部署**：GitHub Pages + HuggingFace Spaces
  - **AI 對話介面**: [HuggingFace Space](https://huggingface.co/spaces/sacahan/resumemate-chat)
  - **靜態履歷**: GitHub Pages

## 快速開始

請參考 [開發環境設定指南](DEVELOPMENT.md) 設定您的開發環境。

### 必要條件

- Python 3.10 或更高版本
- Git
- OpenAI API 金鑰

### 設定步驟

1. 克隆儲存庫

   ```bash
   git clone https://github.com/sacahan/ResumeMate.git
   cd ResumeMate
   ```

2. 執行環境設定腳本

   ```bash
   chmod +x scripts/setup_dev_env.sh
   ./scripts/setup_dev_env.sh
   ```

3. 編輯 `.env` 檔案，添加您的 OpenAI API 金鑰

## 專案結構

參見 [開發環境設定指南](DEVELOPMENT.md) 中的專案結構說明。

## 開發計劃

詳細的開發計劃請參見 [開發計劃文件](plans/development_plan.md)。

## 貢獻指南

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 創建 Pull Request

## 授權

本專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 檔案
