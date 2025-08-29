#!/bin/zsh
# 後端部署腳本 - Hugging Face Spaces

# 輸出顏色設定
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "${YELLOW}開始部署後端到 Hugging Face Spaces...${NC}"

# 確認當前目錄
CURRENT_DIR=$(pwd)
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# 載入環境變數
if [ -f .env ]; then
    source .env
    echo "${GREEN}已載入環境變數${NC}"
else
    echo "${RED}找不到 .env 文件，請確保其存在並包含必要的環境變數${NC}"
    exit 1
fi

# 檢查 HF_TOKEN 是否存在
if [ -z "$HF_TOKEN" ]; then
    echo "${RED}找不到 HF_TOKEN 環境變數，請在 .env 文件中設定 HF_TOKEN=${NC}"
    exit 1
fi

# 檢查 HF_SPACE_NAME 是否存在
if [ -z "$HF_SPACE_NAME" ]; then
    echo "${YELLOW}找不到 HF_SPACE_NAME 環境變數，使用預設名稱 'resumemate-chat'${NC}"
    HF_SPACE_NAME="resumemate-chat"
fi

# 先判斷是否已經安裝才安裝必要的套件
if ! command -v huggingface-cli &> /dev/null; then
    echo "${YELLOW}安裝 Hugging Face CLI...${NC}"
    pip install -U "huggingface_hub[cli]"
fi

#  登入 Hugging Face
echo "${YELLOW}登入 Hugging Face...${NC}"
python -c "from huggingface_hub import login; login('$HF_TOKEN')"

# 建立部署目錄
echo "${YELLOW}準備部署文件...${NC}"
mkdir -p deployment
# 複製主要應用程式檔案
cp app.py deployment/
# 複製整個 src 目錄結構以保持正確的導入路徑
cp -r src deployment/
cp requirements.txt deployment/
# 複製 chroma_db 資料夾（包含向量DB）
cp -r chroma_db deployment/

# 創建部署環境配置
echo "${YELLOW}創建部署環境配置...${NC}"
cat > deployment/.env << EOF
# Gradio 配置
GRADIO_SERVER_PORT=80
GRADIO_SERVER_NAME=0.0.0.0
# 其他環境變數可以在這裡添加
EOF

# 建立 Hugging Face Space 必要檔案
echo "${YELLOW}創建 Hugging Face Space 配置文件...${NC}"
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

# 切換到部署目錄
cd deployment

echo "${YELLOW}使用 Hugging Face Hub API 部署到 Spaces...${NC}"
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

echo "${GREEN}後端部署完成！${NC}"
echo "請前往 https://huggingface.co/spaces/sacahan/$HF_SPACE_NAME 查看您的應用"

# 清理
echo "${YELLOW}清理臨時文件...${NC}"
cd "$REPO_ROOT"
rm -rf deployment

# 返回原始目錄
cd "$CURRENT_DIR"
