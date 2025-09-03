# QA 向量快取重構計劃（Proposal）

## 1. 問題描述（Problem Statement）
- 現況：`src/backend/processor.py` 僅有基於問題字串雜湊的 in-memory 短期快取（TTL 預設 5 分鐘），無法跨程序持久化，也無法跨語義相似的問題命中。
- 需求：將 `src/backend/agents/evaluate.py` 產生的高信心（如 `confidence ≥ 0.9`、`status = ok`）答案持久化到向量資料庫（ChromaDB）。
- 目標：下次遇到語義相似問題時先查詢向量快取，若相似度／綜合分數達門檻，直接回覆，降低 LLM 調用時延與成本，並維持高品質與安全性。

## 2. 可行性與現況盤點
- 既有能力：
  - 已整合 ChromaDB 與嵌入提供者（`src/backend/tools/rag.py`）。
  - `EvaluateAgent` 已回傳 `final_answer`、`confidence`、`status` 與 `sources`。
  - `processor.py` 具備生命週期、統計、TTL、並行與快取框架，可無痛插入新流程。
- 需要擴充：
  - 新增一個「QA 答案快取 collection」，與履歷文件 collection 分離，避免污染。
  - 新增查詢與寫入流程、門檻策略、統計與健康檢查欄位。

## 3. 設計總覽（Architecture）
- 新增 `qa_records` collection（例：`qa_records_minilm`/`qa_records_openai`），重用 RAGTools 的嵌入模型與 PersistentClient。
- 讀取流程（Query Path）：
  1) 問題規範化與嵌入 → 查 `qa_records` top-k（預設 k=3）。
  2) 過濾語言/版本/資料一致性 → 計算綜合分數。
  3) 達門檻則直接回覆，`metadata.cached='qa_vector'`、附 `cache_score` 與命中紀錄。
- 寫入流程（Write Path）：
  - Evaluate 完成後若 `status=ok` 且 `confidence ≥ QA_CACHE_WRITE_MIN_CONF`，以背景任務 upsert 一筆（不阻塞主流程）。

## 4. 資料模型（Q&A Cache Schema）
- id：`sha256(normalized_question + language + model + prompt_version)`
- document：原始 `question_text`
- embedding：問題嵌入向量（與 RAG 同源模型）
- metadata：
  - `answer`: string（最終回覆）
  - `confidence`: float（Evaluate 回覆信心）
  - `status`: string（僅收錄 `ok`）
  - `sources`: string[]（來源）
  - `language`: `zh-TW|en`
  - `model`: 回覆模型（如 `gpt-4o-mini`）
  - `prompt_version`: 指令或 persona 版本（可來自環境變數）
  - `resume_collection_name`: 當時履歷用的 collection 名稱
  - `resume_document_count`: collection 文件數（用於資料漂移偵測）
  - `created_at`: ISO 時間戳

## 5. 命中與寫入策略（Thresholds & Scoring）
- 相似度門檻：`QA_CACHE_HIT_MIN_SIM = 0.85`
- 寫入門檻：`QA_CACHE_WRITE_MIN_CONF = 0.90`（且 `status=ok`）
- 綜合分數：`combined = similarity * cached_confidence * recency_factor * consistency_factor`
  - `recency_factor = exp(-age_hours / half_life)`（半衰期預設 168 小時）
  - `consistency_factor`：若 `language/model/prompt_version/resume_collection_name` 與當前不一致，降權（如 0.7），若嚴重不一致則拒用。
- 命中門檻：`QA_CACHE_HIT_MIN_SCORE = 0.75`
- TTL/失效：`QA_CACHE_TTL_HOURS = 168`，超期降權或剔除。

## 6. 環境變數與預設值（.env）
```ini
QA_CACHE_ENABLED=true
QA_CACHE_TOP_K=3
QA_CACHE_WRITE_MIN_CONF=0.90
QA_CACHE_HIT_MIN_SIM=0.85
QA_CACHE_HIT_MIN_SCORE=0.75
QA_CACHE_TTL_HOURS=168
QA_CACHE_HALF_LIFE_HOURS=168
QA_CACHE_COLLECTION_PREFIX=qa_cache
# 版本/一致性
PROMPT_VERSION=v1
```
- 嵌入提供者（沿用 RAGTools）：`EMBEDDING_PROVIDER`、`LOCAL_MODEL_NAME` 或 `EMBEDDING_MODEL`。

## 7. 整合點（Integration Points）
- `src/backend/processor.py`
  - 分析前：呼叫 `qa_cache.search(question.text)`；命中則組裝 `SystemResponse` 直接返回。
  - Evaluate 後：若符合寫入條件，`asyncio.create_task(qa_cache.add(question.text, final_response, meta))` 背景寫入。
  - 統計：新增 `qa_cache_hits`、`qa_cache_hit_rate`、`qa_cache_size` 至 `get_performance_stats()`。
- `src/backend/agents/evaluate.py`
  - 無需改動邏輯；但將 `status/confidence/sources` 傳遞給寫入端使用。
- `src/backend/tools/rag.py`
  - 重用其 client 與嵌入；不混用 collection，避免污染履歷索引。
- 新檔：`src/backend/tools/qa_cache.py`
  - `QACache.search(question_text: str, top_k=3) -> Optional[CachedHit]`
  - `QACache.should_cache(system_resp: SystemResponse) -> bool`
  - `QACache.add(question_text: str, system_resp: SystemResponse, meta: Dict) -> None`

## 8. 風險與緩解（Risks & Mitigations）
- 語義誤命中：採高門檻、多條件一致性、半衰期與 TTL、必要時加關鍵詞重驗（token overlap）。
- 陳舊/資料漂移：保存 `resume_collection_name` 與 `document_count`；變更即降權或拒用。
- 隱私/安全：僅快取可公開答案（`status=ok`），避免敏感/模糊回答進入快取。
- 模型/指令變更：以 `prompt_version` 與 `model` 落盤，異版降權或不命中。

## 9. 實作計劃（Implementation Plan）
1) 新增 `src/backend/tools/qa_cache.py`（Chroma 連線、collection 初始化、查詢/寫入 API、打分與清理）。
2) 在 `processor.py`：
   - 插入 `qa_cache.search()` 命中快速返回。
   - 在 Evaluate 後以背景任務寫入 `qa_cache.add()`。
   - 統計與健康檢查擴充（`qa_cache_hits` 等）。
3) `.env.example` 與 README 更新環境變數與操作說明。
4) 測試：
   - 單元：命中/寫入/TTL/一致性降權與拒用。
   - 整合：多輪提問命中率與時延下降。
5) 壓測與回歸：
   - 蒐集 P50/P95 時延、命中率、誤命中率，調整門檻。

## 10. 驗收標準（Acceptance Criteria）
- 命中時不調用 Evaluate；處理時延顯著下降（依流量，P95 ≥ 40% 改善）。
- 誤命中率低（抽樣或對照測試 < 1%）。
- QA 快取可控（開關、門檻、TTL 可透過 .env 調整）。
- 監控可見（命中率、快取大小、健康狀態）。

## 11. 開放議題（Open Questions）
- 是否沿用現有嵌入提供者（建議與 RAG 同步）？
- 初始門檻是否採用提案值（寫入 0.90、相似 0.85、綜合 0.75）？
- 是否僅快取 `status=ok`，或也允許經品質優化後的 `needs_edit`？（保守建議僅 `ok`）

---
