---
title: "GitHub Copilot LiteLLM 簡化重構方案"
date: 2025-11-13
status: "建議方案"
---

# GitHub Copilot LiteLLM 簡化重構方案

**設計理念**: 最小化改動，直接在 Agent 中添加 LiteLLM 初始化邏輯，避免過度抽象。

---

## 🎯 目標

1. ✅ 將 `analysis.py` 改成使用 LiteLLM GitHub Copilot 模型
2. ✅ 將 `evaluate.py` 改成使用 LiteLLM GitHub Copilot 模型
3. ✅ 自動配置 GitHub Copilot 特殊 HTTP Headers
4. ✅ 支持 `gpt-5` 和 `gpt-5-mini` 模型切換
5. ✅ 代碼簡潔易懂

---

## 📝 簡化方案

### Step 1: 在 `analysis.py` 中添加 LiteLLM 初始化函數

在 `AnalysisAgent.__init__()` 中添加以下函數和邏輯：

```python
def _create_litellm_model_and_settings(self):
    """為 GitHub Copilot 創建 LiteLLM 模型實例和 ModelSettings

    Returns:
        Tuple[LitellmModel, ModelSettings]: (模型實例, 設置)

    Note:
        GITHUB_COPILOT_TOKEN 環境變數是可選的。
        若不提供，LiteLLM 會自動使用 OAuth Device Flow 進行認證。
        首次使用時會提示設備代碼，之後 Token 會自動快取。
    """
    try:
        from agents.extensions.models.litellm_model import LitellmModel
        from agents import ModelSettings
    except ImportError:
        logger.error("LiteLLM 未安裝，請運行: pip install litellm>=1.0.0")
        raise

    # 從環境變數讀取 Token (可選)
    api_key = os.getenv("GITHUB_COPILOT_TOKEN")
    model = os.getenv("AGENT_MODEL", "gpt-5-mini")

    # 建立 LiteLLM 模型實例
    # 若 api_key 為 None，LiteLLM 會自動使用 OAuth Device Flow
    llm_model = LitellmModel(
        model=f"github_copilot/{model}",
        api_key=api_key,
    )

    # 建立 ModelSettings，配置 GitHub Copilot 所需的 Headers
    model_settings = ModelSettings(
        extra_headers={
            "editor-version": "vscode/1.85.1",
            "Copilot-Integration-Id": "vscode-chat",
        }
    )

    logger.info(f"✅ GitHub Copilot LiteLLM 模型已建立: {model}")
    return llm_model, model_settings
```

### Step 2: 修改 `AnalysisAgent.__init__()`

**改動前**:

```python
def __init__(self, llm: str = "gpt-4o-mini"):
    self.llm = os.environ.get("AGENT_MODEL", llm)
    self.response_length = os.environ.get("AGENT_RESPONSE_LENGTH", "normal")
    self.sdk_agent = None
    self._initialize_sdk_agent()
```

**改動後**:

```python
def __init__(self, llm: str = "gpt-4o-mini"):
    # 1. 建立 LiteLLM 模型
    self.llm_model, self.llm_settings = self._create_litellm_model_and_settings()
    self.response_length = os.environ.get("AGENT_RESPONSE_LENGTH", "normal")
    self.sdk_agent = None
    self._initialize_sdk_agent()
```

### Step 3: 修改 `AnalysisAgent._initialize_sdk_agent()`

**改動前**:

```python
self.sdk_agent = Agent(
    name="韓世翔履歷分析助理",
    instructions=full_instructions,
    tools=[get_contact_info, rag_search_tool],
    model=self.llm,  # ← string 模型
    model_settings=ModelSettings(
        tool_choice="required",
        max_completion_tokens=500,
    ),
    output_type=AgentOutputSchema(AnalysisOutput, strict_json_schema=False),
)
```

**改動後**:

```python
# 建立基礎 ModelSettings
base_settings = ModelSettings(
    tool_choice="required",
    max_completion_tokens=500,
)

# 合併 GitHub Copilot 的 extra_headers
if self.llm_settings and self.llm_settings.extra_headers:
    base_settings.extra_headers = {
        **(base_settings.extra_headers or {}),
        **self.llm_settings.extra_headers,
    }

self.sdk_agent = Agent(
    name="韓世翔履歷分析助理",
    instructions=full_instructions,
    tools=[get_contact_info, rag_search_tool],
    model=self.llm_model,  # ← LitellmModel 實例
    model_settings=base_settings,
    output_type=AgentOutputSchema(AnalysisOutput, strict_json_schema=False),
)
logger.info(f"🚀 Analysis Agent 初始化成功")
```

---

### Step 4: 在 `evaluate.py` 中做同樣的改動

**添加相同的 `_create_litellm_model_and_settings()` 函數**

```python
def _create_litellm_model_and_settings(self):
    """為 GitHub Copilot 創建 LiteLLM 模型實例和 ModelSettings

    Returns:
        Tuple[LitellmModel, ModelSettings]: (模型實例, 設置)

    Note:
        GITHUB_COPILOT_TOKEN 環境變數是可選的。
        若不提供，LiteLLM 會自動使用 OAuth Device Flow 進行認證。
    """
    try:
        from agents.extensions.models.litellm_model import LitellmModel
        from agents import ModelSettings
    except ImportError:
        logger.error("LiteLLM 未安裝，請運行: pip install litellm>=1.0.0")
        raise

    # 從環境變數讀取 Token (可選)
    api_key = os.getenv("GITHUB_COPILOT_TOKEN")
    model = os.getenv("AGENT_MODEL", "gpt-5-mini")

    llm_model = LitellmModel(
        model=f"github_copilot/{model}",
        api_key=api_key,
    )

    model_settings = ModelSettings(
        extra_headers={
            "editor-version": "vscode/1.85.1",
            "Copilot-Integration-Id": "vscode-chat",
        }
    )

    logger.info(f"✅ GitHub Copilot LiteLLM 模型已建立: {model}")
    return llm_model, model_settings
```

**修改 `EvaluateAgent.__init__()`**:

```python
def __init__(self, llm: str = "gpt-4o-mini"):
    # 1. 建立 LiteLLM 模型
    self.llm_model, self.llm_settings = self._create_litellm_model_and_settings()
    self.response_length = os.environ.get("AGENT_RESPONSE_LENGTH", "normal")
    self.quality_analyzer = AnswerQualityAnalyzer()
    # ... 其他初始化
```

**修改 `EvaluateAgent._initialize_sdk_agent()`**:

```python
# 建立基礎 ModelSettings
base_settings = ModelSettings(
    max_completion_tokens=600,
)

# 合併 GitHub Copilot 的 extra_headers
if self.llm_settings and self.llm_settings.extra_headers:
    base_settings.extra_headers = {
        **(base_settings.extra_headers or {}),
        **self.llm_settings.extra_headers,
    }

self.sdk_agent = Agent(
    name="韓世翔品質評估助理",
    instructions=full_instructions,
    model=self.llm_model,  # ← LitellmModel 實例
    model_settings=base_settings,
    output_type=AgentOutputSchema(EvaluateOutput, strict_json_schema=False),
)
logger.info(f"🔍 Evaluate Agent 初始化成功")
```

---

## ⚙️ 環境變數配置

**.env (可選)**:

```bash
# GitHub Copilot Token (可選)
# 若不提供，LiteLLM 會自動使用 OAuth Device Flow
# GITHUB_COPILOT_TOKEN=ghp_xxxxxxxxxxxxx

# 模型選擇 (可選，預設: gpt-5-mini)
AGENT_MODEL=gpt-5-mini
# 或使用更強大的模型
# AGENT_MODEL=gpt-5

# 回覆長度控制 (可選)
AGENT_RESPONSE_LENGTH=normal
```

### 認證方式

#### 方式 1: OAuth Device Flow (推薦，無需環境變數)

- 首次使用時會提示設備代碼
- 按照提示訪問 GitHub 授權頁面
- Token 會自動快取，後續無需操作

#### 方式 2: 使用環境變數 (CI/CD 場景)

```bash
export GITHUB_COPILOT_TOKEN=ghp_xxxxxxxxxxxxx
```

---

## 📊 改動統計

| 文件 | 行數變化 | 主要改動 |
|------|---------|---------|
| `analysis.py` | +30 行 | 添加 LiteLLM 初始化函數 + 模型替換 |
| `evaluate.py` | +30 行 | 添加 LiteLLM 初始化函數 + 模型替換 |
| 總計 | ~60 行 | 簡單直接，無額外抽象層 |

---

## ✅ 改動檢查清單

### analysis.py

- [ ] 添加 `_create_litellm_model_and_settings()` 函數
- [ ] 修改 `__init__()` 調用此函數
- [ ] 修改 `_initialize_sdk_agent()` 使用 `self.llm_model`
- [ ] 合併 ModelSettings 中的 extra_headers
- [ ] 測試通過

### evaluate.py

- [ ] 添加 `_create_litellm_model_and_settings()` 函數
- [ ] 修改 `__init__()` 調用此函數
- [ ] 修改 `_initialize_sdk_agent()` 使用 `self.llm_model`
- [ ] 合併 ModelSettings 中的 extra_headers
- [ ] 測試通過

---

## 🎯 優勢

✅ **簡潔**: 沒有額外的配置類或工廠類
✅ **明確**: 每個 Agent 獨立清晰，易於理解
✅ **易維護**: 改動集中在兩個文件中
✅ **少依賴**: 無新增外部依賴或模塊
✅ **易調試**: 重複代碼便於追蹤問題

---

## 📚 相關文檔

- [GITHUB_COPILOT_GUIDE.md](./GITHUB_COPILOT_GUIDE.md) - GitHub Copilot 集成指南
- [LiteLLM 官方文檔](https://docs.litellm.ai)

---

**版本**: 1.0
**狀態**: 簡化方案
**最後更新**: 2025-11-13
