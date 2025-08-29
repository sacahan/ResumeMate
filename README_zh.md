# ResumeMate

ResumeMate 是一個 AI 驅動的履歷代理人平台，結合靜態履歷展示與 AI 互動問答功能。

🚀 **線上展示**: [https://huggingface.co/spaces/sacahan/resumemate-chat](https://huggingface.co/spaces/sacahan/resumemate-chat)

## 核心特色

- **智慧問答**：透過 RAG 技術實現個人化的履歷內容對話
- **聯絡資訊查詢**：專用工具快速回應聯絡方式相關問題
- **對話式聯絡**：自然語言收集聯絡資訊，適合 iframe 嵌入
- **雙語支援**：中英文介面無縫切換
- **響應式設計**：支援各種螢幕尺寸的最佳化體驗
- **JSON 驅動內容**：彈性的資料管理與版本控制

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

## 專案進度

### 🎉 第二階段完成 (Analysis Agent MVP + 前端基礎)

#### ✅ 後端核心功能

- **Analysis Agent**：完整實作雙工具策略
  - `get_contact_info`：聯絡資訊專用查詢工具
  - `rag_search_tool`：履歷內容檢索工具
- **Evaluate Agent**：多狀態評估系統，支援品質控制
- **非同步架構**：高效能的 async/await 處理模式

#### ✅ 前端完整功能

- **響應式履歷頁面**：完整的 HTML5 + Tailwind CSS 實作
- **多語言支援**：中英文無縫切換機制
- **JSON 資料管理**：動態載入與版本控制系統
- **互動效果**：平滑滾動、動畫效果、聊天範例

#### ✅ 測試與品質保證

- **單元測試**：Analysis Agent 完整測試覆蓋
- **整合測試**：前後端協同工作驗證
- **聯絡資訊工具**：專用聯絡資訊收集系統

### 📋 下一階段：功能完善與最佳化

準備進入第三階段，專注於：

- AI 能力提升與提示詞優化
- 系統效能最佳化
- UI/UX 體驗改善
- 正式部署準備

## 貢獻指南

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 創建 Pull Request

## 授權

本專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 檔案
