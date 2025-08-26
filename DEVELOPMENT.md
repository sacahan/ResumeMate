# 開發環境設定指南

本文件描述如何為 ResumeMate 專案設定開發環境和使用 CI/CD 流程。

## 環境需求

- Python 3.10 或更高版本
- Git
- 文本編輯器或 IDE (如 VS Code)
- OpenAI API 金鑰

## 設定開發環境

1. 克隆專案儲存庫

```bash
git clone https://github.com/sacahan/ResumeMate.git
cd ResumeMate
```

2. 執行環境設定腳本

```bash
# 確保腳本有執行權限
chmod +x scripts/setup_dev_env.sh

# 執行設定腳本
./scripts/setup_dev_env.sh
```

3. 啟動虛擬環境

```bash
source .venv/bin/activate
```

4. 編輯 `.env` 檔案，添加您的 OpenAI API 金鑰

```bash
# 編輯 .env 檔案
nano .env
```

更新以下內容：

```plaintext
OPENAI_API_KEY=your_actual_api_key_here
```

## 專案結構

```
ResumeMate/
├── .github/                # GitHub 相關設定
│   └── workflows/          # CI/CD 工作流程定義
├── chroma_db/              # 向量資料庫
├── plans/                  # 專案計劃文件
├── scripts/                # 實用腳本
├── src/                    # 源代碼
│   ├── backend/            # 後端代碼
│   │   ├── agents/         # AI 代理人實作
│   │   ├── data/           # 資料和資料模型
│   │   └── tools/          # 工具和工具實作
│   └── frontend/           # 前端代碼
│       └── static/         # 靜態資源
│           ├── css/        # 樣式表
│           ├── js/         # JavaScript 檔案
│           └── images/     # 圖片
├── tests/                  # 測試
│   ├── unit/               # 單元測試
│   └── integration/        # 整合測試
├── .env                    # 環境變數設定
├── pyproject.toml          # 專案設定
├── requirements.txt        # 依賴項目
└── README.md               # 專案說明
```

## 開發工作流程

1. **創建分支**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **編寫代碼和測試**

   - 請遵循 Python 風格指南 (PEP 8)
   - 添加適當的測試
   - 運行測試確保通過

   ```bash
   # 運行測試
   pytest

   # 格式化代碼
   black src tests
   isort src tests

   # 檢查代碼品質
   flake8 src tests
   ```

3. **提交變更**

   ```bash
   git add .
   git commit -m "描述性的提交訊息"
   ```

4. **推送分支**

   ```bash
   git push origin feature/your-feature-name
   ```

5. **創建 Pull Request**

   在 GitHub 界面上創建 Pull Request，進行代碼審查。

## 部署流程

本專案使用本地腳本進行部署，避免使用 GitHub Actions 產生額外成本：

1. **設定身份驗證**
   - 為部署到 GitHub Pages，需要設定 GitHub 身份驗證：
     - 方法 1: 在 `.env` 文件中添加 `GITHUB_TOKEN=your_personal_access_token`
     - 方法 2: 設置 SSH 金鑰連接到 GitHub
     - 方法 3: 儲存 Git 憑證 (`git config --global credential.helper store`)
   - 為部署到 Hugging Face Spaces，需要在 `.env` 文件中設定：
     - `HF_TOKEN=your_hugging_face_token`
     - `HF_SPACE_NAME=your_space_name`

2. **準備部署**
   - 確保所有測試通過
   - 確保代碼格式符合規範
   - 確保在 `.env` 文件中設定了必要的身份驗證令牌

3. **使用整合部署腳本**

   ```bash
   # 確保腳本有執行權限
   chmod +x scripts/deploy.sh

   # 執行部署
   ./scripts/deploy.sh
   ```

   此腳本會自動運行測試、檢查代碼格式，然後依序部署前端和後端。

4. **單獨部署前端或後端**

   ```bash
   # 僅部署前端
   ./scripts/deploy_frontend.sh

   # 僅部署後端
   ./scripts/deploy_backend.sh
   ```

## 本地運行專案

### 運行後端

```bash
cd src/backend
python app.py
```

### 檢視前端

由於前端是靜態頁面，可以使用簡單的 HTTP 服務器：

```bash
cd src/frontend
python -m http.server 8000
```

然後訪問 `http://localhost:8000` 查看前端頁面。

## 其他資源

- [專案計劃文件](plans/development_plan.md)
- [需求文件](plans/requirement.md)
