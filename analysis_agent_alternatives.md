# AnalysisAgent 工具使用改進替代方案

## 當前問題

AnalysisAgent 未能積極使用 rag_search_tool 檢索履歷資訊，即使對明顯相關的問題如「你有什麼技能？」

## 替代方案

### 方案 A：使用特定工具強制

```python
model_settings=ModelSettings(
    tool_choice="rag_search_tool"  # 直接指定工具名稱
)
```

### 方案 B：使用 stop_on_first_tool 行為

```python
agent = Agent(
    name="Analysis Agent",
    instructions=DEFAULT_INSTRUCTIONS,
    tools=[rag_search_tool],
    model=self.llm,
    tool_use_behavior="stop_on_first_tool",  # 使用工具後立即停止
    model_settings=ModelSettings(tool_choice="required")
)
```

### 方案 C：自定義工具使用處理器

```python
from agents.agent import ToolsToFinalOutputResult

def force_tool_use_handler(
    context: RunContextWrapper[Any],
    tool_results: List[FunctionToolResult]
) -> ToolsToFinalOutputResult:
    """強制使用工具結果作為最終輸出"""
    if tool_results:
        # 直接使用第一個工具結果
        result = tool_results[0]
        return ToolsToFinalOutputResult(
            is_final_output=True,
            final_output=result.output
        )
    return ToolsToFinalOutputResult(is_final_output=False)

agent = Agent(
    name="Analysis Agent",
    instructions=DEFAULT_INSTRUCTIONS,
    tools=[rag_search_tool],
    model=self.llm,
    tool_use_behavior=force_tool_use_handler,
    model_settings=ModelSettings(tool_choice="required")
)
```

### 方案 D：簡化 Instructions（極度直接）

```python
DIRECT_INSTRUCTIONS = """
你必須對每個問題先使用 rag_search_tool 檢索履歷資料。

步驟：
1. 立即呼叫 rag_search_tool(query="問題關鍵詞", top_k=5)
2. 根據檢索結果回答

不要跳過檢索步驟。即使問題看似簡單，也要先檢索。
"""
```

### 方案 E：多重工具策略

```python
@function_tool
def skills_search_tool() -> List[Dict[str, Any]]:
    """專門搜索技能相關資訊"""
    rag_tools = RAGTools()
    return rag_tools.rag_search("技能 skill programming", top_k=5)

@function_tool
def experience_search_tool() -> List[Dict[str, Any]]:
    """專門搜索工作經驗資訊"""
    rag_tools = RAGTools()
    return rag_tools.rag_search("工作 experience job", top_k=5)

# 然後在 agent 中使用多個專用工具
tools=[rag_search_tool, skills_search_tool, experience_search_tool]
```

## 調試建議

### 1. 檢查工具是否被調用

在 `rag_search_tool` 中添加日誌：

```python
@function_tool
def rag_search_tool(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    print(f"🔧 RAG工具被調用！查詢: {query}")
    logger.info(f"RAG工具調用 - 查詢: {query}, top_k: {top_k}")
    # ... 原有代碼
```

### 2. 檢查 ModelSettings 是否生效

在初始化後檢查：

```python
print(f"Agent model settings: {self.sdk_agent.model_settings}")
print(f"Tool choice: {self.sdk_agent.model_settings.tool_choice if self.sdk_agent.model_settings else 'None'}")
```

### 3. 檢查 Agent 執行過程

在 `_analyze_with_sdk` 中添加詳細日誌：

```python
result = await Runner.run(self.sdk_agent, input=question.text)
logger.info(f"SDK執行結果類型: {type(result)}")
logger.info(f"是否有工具調用: {hasattr(result, 'tool_calls')}")
```

## 最激進方案：預先檢索

如果所有方案都失效，可考慮在 Agent 外部預先執行檢索：

```python
async def analyze(self, question: Question) -> AnalysisResult:
    # 強制預先檢索
    rag_tools = RAGTools()
    pre_search_results = rag_tools.rag_search(question.text, top_k=5)

    # 將檢索結果注入到 instructions 中
    enhanced_instructions = f"""
    {DEFAULT_INSTRUCTIONS}

    已預先檢索到以下履歷片段：
    {json.dumps(pre_search_results, ensure_ascii=False, indent=2)}

    請基於這些片段回答問題。
    """

    # 臨時修改 agent instructions
    original_instructions = self.sdk_agent.instructions
    self.sdk_agent.instructions = enhanced_instructions

    try:
        return await self._analyze_with_sdk(question)
    finally:
        self.sdk_agent.instructions = original_instructions
```
