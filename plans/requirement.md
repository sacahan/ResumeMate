
# AI 履歷代理人需求規格

## 1. 目標

參考 [prototype.html](./prototype.html) 的設計，打造一個 AI 履歷代理人，分為「履歷簡介」與「互動式聊天」兩大區塊：

- **履歷簡介**：上半部顯示靜態履歷資訊。
- **互動式聊天**：下半部提供聊天介面，由 AI 回覆履歷相關問題。

---

## 2. 功能需求

### 2.1. 履歷簡介顯示

- **基本資料**：姓名、職稱、聯絡方式等。
- **核心內容**：自我介紹、學歷、工作經歷、技能、作品集。

### 2.2. 互動式聊天介面

- **提問**：支援使用者以自然語言提問。
- **回答**：
  - **RAG 整合**：從履歷資料中檢索並回答。
  - **超出範圍處理**：若問題超出履歷範圍，應回覆「很抱歉，此問題超出我的知識範圍，我會請本人回覆您」，並記錄問題。
  - **聯絡方式**：引導提問者留下聯絡方式以便後續追蹤。

---

## 3. 技術需求

### 3.1. 前端

- **技術棧**：HTML, CSS, JavaScript。
- **設計**：響應式設計，以卡片或分欄呈現。
- **聊天介面**：
  - **推薦方案**：以 `iframe` 嵌入 Hugging Face Gradio UI。
  - **備用方案**：自建聊天框，串接後端 API。

### 3.2. 後端/AI

- **AI 框架**：使用 OpenAI Agent SDK。
- **Agent 設計**：
  - **Analysis Agent**：解析問題，從向量資料庫檢索資訊。
  - **Evaluate Agent**：評估回覆的正確性與適切性。
- **資料檢索**：透過 RAG 工具串接本地向量資料庫 (`chroma_db`)。

### 3.3. 資料結構

- **靜態履歷**：JSON 或 Markdown 格式。
- **向量履歷**：儲存於 `chroma_db` 資料夾。

---

## 4. 部署策略

### 4.1. 部署架構

#### 推薦架構：GitHub Pages + Hugging Face Space

- **靜態網頁**：部署於 GitHub Pages。
  - **自訂網域**：支援綁定自訂網域 (如 `brianhan.cc`)。需在 repo 中新增 `CNAME` 檔案並設定 DNS。
- **Gradio UI & AI 後端**：託管於 Hugging Face Space。
  - **向量資料庫**：可將 `chroma_db` 檔案一同部署至 Space，但需注意其儲存與效能限制。
- **優點**：免費、穩定、易於維護。
- **挑戰**：需處理自訂網域的 CORS 問題，確保 `iframe` 能正常嵌入。

### 4.2. 部署腳本

#### Gradio UI 部署 (Hugging Face Space)

```bash
# deploy_gradio.sh
#!/bin/bash
echo "Deploying Gradio UI to Hugging Face Space..."
pip install gradio huggingface_hub
huggingface-cli login
gradio deploy --space your-username/resumemate-chat --app-file app.py
echo "Deployment complete."
```

#### 靜態網頁部署 (GitHub Pages)

```bash
# deploy_static.sh
#!/bin/bash
echo "Deploying static site to GitHub Pages..."
# npm run build # 如果需要建置
git checkout -b gh-pages
git add .
git commit -m "Deploy to GitHub Pages"
git push origin gh-pages --force
echo "Deployment complete."
```

### 4.3. 環境設定

#### 環境變數 (`.env`)

```env
OPENAI_API_KEY="your_openai_api_key"
HUGGINGFACE_TOKEN="your_huggingface_token"
CHROMA_DB_PATH="./chroma_db"
```

#### 相依套件 (`requirements.txt`)

```env
gradio>=4.0.0
openai>=1.0.0
chromadb>=0.4.0
huggingface_hub>=0.16.0
```

---

## 5. 測試策略

- **單元測試**：測試前端 JS、後端 Agent 邏輯、RAG 檢索功能。
- **整合測試**：測試前端與 Gradio UI、Agent 與向量資料庫的整合。
- **用戶測試**：測試 UI/UX、響應式設計、問答準確性。

---

## 6. 參考資料

- [Gradio 官方文件](https://www.gradio.app/docs/)
- [OpenAI Agent SDK](https://platform.openai.com/docs/agents)
- [Hugging Face Spaces 部署指南](https://huggingface.co/docs/hub/spaces)
- [GitHub Pages 設定](https://docs.github.com/en/pages)
