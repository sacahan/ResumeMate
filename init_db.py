"""初始化 ChromaDB 資料庫

載入履歷資料到向量資料庫
"""

import sys
import os
import logging

# 添加 src 目錄到 Python 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from backend.tools import RAGTools

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_sample_resume_data():
    """取得範例履歷資料"""
    return [
        {
            "id": "personal_info",
            "content": "我是一位軟體工程師，專精於 Python、JavaScript 和雲端服務開發。擁有 5 年以上的全端開發經驗，熟悉 React、Django、Flask 等框架。目前專注於 AI 應用開發和系統架構設計。",
            "metadata": {"category": "基本資料", "type": "個人簡介"},
        },
        {
            "id": "skills_programming",
            "content": "程式語言：Python (精通)、JavaScript (精通)、TypeScript (熟練)、Java (熟練)、Go (基礎)。前端技術：React、Vue.js、HTML5、CSS3、Tailwind CSS。後端技術：Django、Flask、FastAPI、Node.js、Express。",
            "metadata": {"category": "技能", "type": "程式設計"},
        },
        {
            "id": "skills_database",
            "content": "資料庫技術：PostgreSQL (精通)、MySQL (精通)、MongoDB (熟練)、Redis (熟練)、ChromaDB (熟練)。雲端服務：AWS (EC2, S3, Lambda, RDS)、Google Cloud Platform、Azure。",
            "metadata": {"category": "技能", "type": "資料庫與雲端"},
        },
        {
            "id": "skills_ai",
            "content": "AI/ML 技術：LangChain、OpenAI API、Gradio、機器學習基礎、自然語言處理、RAG 系統設計。開發工具：Git、Docker、Kubernetes、CI/CD、測試自動化。",
            "metadata": {"category": "技能", "type": "AI與工具"},
        },
        {
            "id": "experience_current",
            "content": "目前擔任資深軟體工程師 (2022-至今)，負責 AI 應用系統開發和架構設計。主要工作包括：設計和實作 RAG 系統、開發 AI 聊天機器人、建置微服務架構、優化系統效能。",
            "metadata": {"category": "工作經驗", "type": "目前職位"},
        },
        {
            "id": "experience_previous",
            "content": "曾任全端工程師 (2019-2022)，參與多個 Web 應用專案開發。主要負責前後端整合、API 設計、資料庫優化、用戶介面設計。成功交付多個企業級應用系統。",
            "metadata": {"category": "工作經驗", "type": "前職經驗"},
        },
        {
            "id": "projects_resumemate",
            "content": "ResumeMate 專案：AI 驅動的履歷代理人平台，結合 RAG 技術實現智慧問答功能。使用 Python、LangChain、ChromaDB、Gradio 等技術，部署於 GitHub Pages 和 HuggingFace Spaces。",
            "metadata": {"category": "專案經驗", "type": "AI專案"},
        },
        {
            "id": "projects_ecommerce",
            "content": "電商平台專案：完整的線上購物系統，包含商品管理、訂單處理、支付整合、用戶管理等功能。使用 React + Django，支援高並發訪問，月活躍用戶達 10萬+。",
            "metadata": {"category": "專案經驗", "type": "Web專案"},
        },
        {
            "id": "education_degree",
            "content": "資訊工程學士學位，主修電腦科學。在學期間專精於資料結構、演算法、軟體工程、資料庫系統。畢業專題為機器學習應用於推薦系統。",
            "metadata": {"category": "教育背景", "type": "學位"},
        },
        {
            "id": "education_certificates",
            "content": "相關證照：AWS Certified Developer、Google Cloud Professional、Docker 認證、敏捷開發認證。持續學習 AI/ML 相關技術，完成多項線上課程。",
            "metadata": {"category": "教育背景", "type": "證照與學習"},
        },
        {
            "id": "contact_info",
            "content": "聯絡方式：歡迎透過 LinkedIn、GitHub 或專業平台與我聯繫。Email 請通過 LinkedIn 私訊或填寫聯絡表單。位於台灣，可接受遠端工作機會。",
            "metadata": {"category": "聯絡資訊", "type": "聯絡方式"},
        },
        {
            "id": "languages",
            "content": "語言能力：中文（母語）、英文（流利，可進行技術溝通和文件撰寫）、日文（基礎會話）。具備跨國團隊合作經驗。",
            "metadata": {"category": "其他能力", "type": "語言能力"},
        },
    ]


def initialize_database():
    """初始化資料庫"""
    try:
        logger.info("開始初始化 ChromaDB 資料庫...")

        # 初始化 RAG 工具
        rag_tools = RAGTools()

        # 取得範例資料
        sample_data = get_sample_resume_data()

        logger.info(f"準備載入 {len(sample_data)} 筆資料...")

        # 準備資料格式
        ids = [item["id"] for item in sample_data]
        documents = [item["content"] for item in sample_data]
        metadatas = [item["metadata"] for item in sample_data]

        # 將資料加入 collection
        rag_tools.collection.add(ids=ids, documents=documents, metadatas=metadatas)

        logger.info("資料載入完成！")

        # 檢查載入結果
        collection_info = rag_tools.get_collection_info()
        logger.info(f"資料庫狀態: {collection_info}")

        # 測試檢索功能
        logger.info("測試檢索功能...")
        test_results = rag_tools.rag_search("程式設計技能", top_k=3)

        if test_results:
            logger.info(f"檢索測試成功，找到 {len(test_results)} 個結果:")
            for i, result in enumerate(test_results, 1):
                logger.info(f"  {i}. {result.doc_id} (分數: {result.score:.3f})")
        else:
            logger.warning("檢索測試失敗，沒有找到結果")

        return True

    except Exception as e:
        logger.error(f"初始化資料庫失敗: {e}")
        return False


if __name__ == "__main__":
    success = initialize_database()
    if success:
        print("✅ 資料庫初始化成功！")
    else:
        print("❌ 資料庫初始化失敗！")
