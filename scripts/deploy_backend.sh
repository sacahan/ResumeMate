#!/bin/zsh
# 後端部署腳本 - Hugging Face Spaces

# 輸出顏色設定
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}開始部署後端到 Hugging Face Spaces...${NC}"

# 確認當前目錄
CURRENT_DIR=$(pwd)
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# 載入環境變數
if [ -f .env ]; then
    source .env
    echo -e "${GREEN}已載入環境變數${NC}"
else
    echo -e "${RED}找不到 .env 文件，請確保其存在並包含必要的環境變數${NC}"
    exit 1
fi

# 檢查 HF_TOKEN 是否存在
if [ -z "$HF_TOKEN" ]; then
    echo -e "${RED}找不到 HF_TOKEN 環境變數，請在 .env 文件中設定 HF_TOKEN=${NC}"
    exit 1
fi

# 檢查 HF_SPACE_NAME 是否存在
if [ -z "$HF_SPACE_NAME" ]; then
    echo -e "${YELLOW}找不到 HF_SPACE_NAME 環境變數，使用預設名稱 'resumemate-chat'${NC}"
    HF_SPACE_NAME="resumemate-chat"
fi

# 先判斷是否已經安裝才安裝必要的套件
if ! command -v huggingface-cli &> /dev/null; then
    echo -e "${YELLOW}安裝 Hugging Face CLI...${NC}"
    pip install -U "huggingface_hub[cli]"
fi

#  登入 Hugging Face
echo -e "${YELLOW}登入 Hugging Face...${NC}"
python -c "from huggingface_hub import login; login('$HF_TOKEN')"

# 建立部署目錄
echo -e "${YELLOW}準備部署文件...${NC}"
mkdir -p deployment
# 複製主要應用程式檔案
cp app.py deployment/
# 複製整個 src 目錄結構以保持正確的導入路徑（排除 frontend 和 __pycache__）
rsync -av --exclude='frontend' --exclude='__pycache__' src/ deployment/src/
cp requirements.txt deployment/
# 注意：NOT 複製 chroma_db，因為：
# 1. 向量 DB 非常大（數百 MB）
# 2. Hugging Face Spaces 有存儲限制
# 3. 可以在運行時動態生成或使用 git-lfs

# 創建部署環境配置
echo -e "${YELLOW}創建 Hugging Face Space 配置文件...${NC}"
# 注意：不在這裡設定 .env，因為密鑰應該在 Hugging Face Spaces Settings 中設定
# Hugging Face 會自動注入環境變數
cat > deployment/README.md << EOF
---
title: ResumeMate Chat
emoji: 📝
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 5.44.1
app_file: app.py
pinned: false
license: apache-2.0
---

# ResumeMate

ResumeMate is an AI-powered resume agent platform that combines static resume presentation with interactive AI Q&A features.
EOF

# 創建 .gitignore 以避免大文件被上傳
cat > deployment/.gitignore << EOF
__pycache__/
*.py[cod]
*$py.class
*.so
.env
.env.local
*.db
*.sqlite3
chroma_db/
*.egg-info/
dist/
build/
.venv/
venv/
EOF

# 切換到部署目錄
cd deployment

echo -e "${YELLOW}使用 Hugging Face Hub API 部署到 Spaces...${NC}"
# 使用 Python API 創建或更新 Space
python -c "
import os
from huggingface_hub import HfApi, Repository
from pathlib import Path

# 初始化 API
api = HfApi()
space_name = '$HF_SPACE_NAME'
username = api.whoami()['name']
repo_id = f'{username}/{space_name}'

print(f'部署到 Space: {repo_id}')

try:
    # 嘗試創建 Space（如果不存在）
    api.create_repo(
        repo_id=repo_id,
        repo_type='space',
        space_sdk='gradio',
        exist_ok=True
    )
    print('Space 已創建或已存在')

    # 上傳所有文件
    api.upload_folder(
        folder_path='.',
        repo_id=repo_id,
        repo_type='space',
        commit_message='Deploy ResumeMate application'
    )
    print('文件上傳完成!')

except Exception as e:
    print(f'部署失敗: {e}')
    exit(1)
"

echo -e "${GREEN}後端部署完成！${NC}"
echo -e "請前往 https://huggingface.co/spaces/sacahan/$HF_SPACE_NAME 查看您的應用"

# 清理
echo -e "${YELLOW}清理臨時文件...${NC}"
cd "$REPO_ROOT"
rm -rf deployment

# 返回原始目錄
cd "$CURRENT_DIR"
