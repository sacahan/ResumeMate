# AGENTS.md

本檔案提供給 AI 編碼助手（如 Gemini、Claude、Cursor 等）在專案中工作時的完整指南，包含專案架構、開發規範與最佳實踐。

## 專案概述

ResumeMate 是一個 AI 驅動的履歷代理平台，結合靜態履歷展示與 AI 互動問答功能。系統串接 Dify Chatflow API 實現個人化履歷對話，支援中英文雙語介面。

## 專案結構

```
ResumeMate/
├── app.py                      # Gradio 主應用程式入口
├── src/
│   ├── backend/                # 後端核心邏輯
│   │   ├── dify/               # Dify API 整合層
│   │   │   ├── __init__.py     # 匯出 DifyProcessor
│   │   │   ├── client.py       # async httpx Dify 客戶端
│   │   │   ├── adapter.py      # Dify 回應 → SystemResponse 映射
│   │   │   └── processor.py    # DifyProcessor 主處理器
│   │   ├── tools/              # 工具模組
│   │   │   └── contact.py      # 聯絡資訊收集工具
│   │   ├── cms/                # 內容管理系統模組
│   │   │   ├── admin_app.py    # 管理後台 Gradio 介面
│   │   │   ├── ai_assistant.py # AI 助手（圖表元數據建議，使用 openai-agents SDK）
│   │   │   ├── data_manager.py # 資料管理器
│   │   │   ├── git_manager.py  # Git 版本控制整合
│   │   │   ├── project_manager.py  # 專案資料管理
│   │   │   └── language_manager.py # 多語言內容管理
│   │   ├── models.py           # Pydantic 資料模型（Question、SystemResponse）
│   │   └── logging_config.py   # 日誌設定
│   └── frontend/               # 前端靜態資源
│       ├── index.html          # 靜態履歷頁面
│       ├── data/               # JSON 資料檔案
│       │   ├── resume-zh.json  # 中文履歷資料
│       │   └── resume-en.json  # 英文履歷資料
│       └── static/             # 靜態資源 (JS/CSS)
├── tests/                      # 測試目錄
│   ├── unit/                   # 單元測試
│   ├── integration/            # 整合測試
│   ├── performance/            # 效能測試
│   └── ux/                     # UX 測試
├── scripts/                    # 部署與執行腳本
│   ├── Dockerfile             # Docker 映像定義
│   ├── requirements.txt        # Docker 依賴套件
│   ├── .env.docker            # Docker 環境變數範本
│   ├── docker-run.sh          # Docker 容器管理腳本
│   ├── build-backend.sh       # Docker 映像建置腳本
│   ├── run-cms.sh             # CMS 本地啟動腳本
│   └── deploy_frontend.sh     # 前端部署 (GitHub Pages)
└── docs/                       # 專案文件
```

## 開發環境設定

### 前置需求

- Python 3.10 以上版本
- Git
- OpenAI API 金鑰

### 環境建置指令

```bash
# 建立並啟用虛擬環境
python -m venv .venv && source .venv/bin/activate

# 安裝依賴套件
pip install -r requirements.txt

# 或使用 uv（推薦）
uv sync
```

### 執行應用程式

```bash
# 啟動 Gradio 介面（預設連接埠 7860）
python app.py

# 或使用 uv
uv run app.py
```

## 測試指令

```bash
# 執行所有測試
pytest

# 僅執行單元測試
pytest tests/unit -q

# 僅執行整合測試
pytest tests/integration

# 詳細輸出
pytest -v
```

## 程式碼品質

### 程式碼格式化與檢查

```bash
# Python 格式化與 lint（使用 Ruff）
ruff --fix . && ruff format .

# JavaScript/TypeScript 格式化
prettier --write "**/*.{js,jsx,ts,tsx,css,json,yaml,yml}"

# 執行 pre-commit hooks
pre-commit install
pre-commit run -a
```

### 程式碼風格規範

- **Python**：Black 相容風格，行長度 88 字元
- **Import 排序**：使用 isort，採用 "black" profile
- **Lint 檢查**：Ruff 強制執行，維持零警告
- **命名規範**：
  - 函數/變數：`snake_case`
  - 類別：`PascalCase`
  - 模組檔案：`lower_snake.py`
  - 測試檔案：`test_*.py`

## 測試指南

- **框架**：pytest + pytest-asyncio（auto 模式）
- **測試路徑**：`tests/`（unit, integration, performance, ux）
- **命名規範**：
  - 測試檔案：`test_<模組名>.py`
  - 測試函數：`test_<行為描述>()`
- **最佳實踐**：
  - 新功能與修復須附帶測試
  - 外部 API 使用 mock
  - 本地執行 `pytest -q` 確保通過

## 提交與 Pull Request 規範

### Commit 規範

遵循 Conventional Commits 格式，使用正體中文：

```text
<type>(<scope>): <description>

# 範例
feat(agents): 新增問答評估功能
fix(processor): 修復回應解析錯誤
docs(readme): 更新安裝說明
```

**類型**：`feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Pull Request 規範

- 清晰的描述與問題連結
- 提供驗證步驟
- UI 變更須附上截圖/GIF
- 確保測試通過且 pre-commit 無錯誤

## 本地開發

### CMS 管理介面 (本地 Python 啟動)

```bash
# 互動式選單（推薦）
./scripts/run-cms.sh

# 前景啟動 CMS 管理後台
./scripts/run-cms.sh start

# 背景啟動 CMS
./scripts/run-cms.sh --background
./scripts/run-cms.sh -b

# 終止背景 CMS 程序
./scripts/run-cms.sh kill

# 查看 CMS 運行狀態
./scripts/run-cms.sh status

# 自訂配置
./scripts/run-cms.sh --port 8000 --user myuser --password mypass

# 訪問 CMS
http://127.0.0.1:7861
```

### 主應用 (本地 Python 啟動)

```bash
# 啟動 Gradio 主應用
python app.py

# 或使用 uv
uv run app.py
```

## 部署流程

### Docker 部署（生產環境）

#### 1. 建置 Docker 映像

```bash
# 基本建置 (arm64 + amd64)
./scripts/build-backend.sh

# 指定架構
./scripts/build-backend.sh --platform arm64 --action build

# 建置並推送至 Docker Hub
./scripts/build-backend.sh --action build-push
```

#### 2. 執行 Docker 容器

```bash
# 啟動容器
./scripts/docker-run.sh run

# 查看容器狀態
./scripts/docker-run.sh status

# 查看容器日誌
./scripts/docker-run.sh logs -f

# 停止容器
./scripts/docker-run.sh stop
```

**Docker 掛載設定**：

- Host: `./logs` → Container: `/app/logs`
- 使用根目錄 `.env` 檔案作為環境變數來源

### 前端部署 (GitHub Pages)

```bash
./scripts/deploy_frontend.sh
```

## 安全與設定

- 複製 `.env.example` 至 `.env` 並設定 `DIFY_API_KEY`（必要）
- **絕對不要** 將金鑰或敏感資訊提交至版本控制
- Python 3.10+ 為必要環境
- 公開 API 變更需於 PR 中說明遷移方式

## 核心技術棧

- **Python 3.10+**：async/await 非同步模式
- **Dify Chatflow API**：AI 問答（透過 httpx）
- **OpenAI Agents SDK**：僅供 CMS `InfographicAssistantAgent` 使用
- **Gradio 5.x**：Web 介面框架
- **Pydantic 2.x**：資料驗證

## AI 工作流程

1. **問題處理**：使用者輸入結構化為 `Question` 模型
2. **Dify 呼叫**：`DifyProcessor.process_question(question, conversation_id)` 呼叫 Dify Chatflow API
   - `conversation_id=""` → Dify 建立新對話並回傳 ID
   - 後續呼叫傳入 `conversation_id` 實現多輪對話連貫性
3. **回應適配**：`adapter.adapt()` 將 Dify JSON → `(SystemResponse, conversation_id)`
4. **狀態儲存**：`gr.State` 在 Gradio 中保存 `conversation_id` 供下輪使用

## 開發工作流程規則

### Python 環境管理

優先使用 `uv` 進行 Python 套件管理：

```bash
uv run    # 執行 Python 程式
uv sync   # 同步虛擬環境
uv add    # 新增依賴套件
```

### 環境變數管理

- **本地開發**：使用根目錄 `.env` 檔案（自動由 `python-dotenv` 載入）
- **Docker 部署**：同樣使用根目錄 `.env` 檔案，通過 `--env-file` 參數傳遞
- **Docker 環境參考**：可參考 `scripts/.env.docker` 了解容器內路徑設定

### 文件維護

- 重構完成後檢視 README.md 是否需要更新
- 重大變更須同步更新相關文件

### 雙語支援

- 系統支援正體中文與英文
- 所有回應來自 Dify Chatflow API
- 回應包含固定信心度分數（`0.85`）以供品質評估
