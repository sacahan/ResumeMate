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

# 安裝必要的套件
echo "${YELLOW}安裝 Hugging Face CLI...${NC}"
pip install huggingface_hub

# 登入 Hugging Face
echo "${YELLOW}登入 Hugging Face...${NC}"
python -c "from huggingface_hub import login; login('$HF_TOKEN')"

# 建立部署目錄
echo "${YELLOW}準備部署文件...${NC}"
mkdir -p deployment
cp -r src/backend/* deployment/
cp requirements.txt deployment/
cp README.md deployment/
# 複製 chroma_db 資料夾（包含向量DB）
cp -r chroma_db deployment/

# 建立 Hugging Face Space 必要檔案
echo "${YELLOW}創建 Hugging Face Space 配置文件...${NC}"
cat > deployment/README.md << EOF
---
title: ResumeMate Chat
emoji: 📝
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
---

# ResumeMate Chat

AI 驅動的履歷問答系統
EOF

# 切換到部署目錄
cd deployment

# 部署到 Hugging Face Spaces
echo "${YELLOW}部署到 Hugging Face Spaces...${NC}"
if command -v huggingface-cli &> /dev/null; then
    echo "${YELLOW}使用 huggingface-cli 部署...${NC}"
    huggingface-cli upload-space "$HF_SPACE_NAME" .
else
    echo "${YELLOW}使用 Python API 部署...${NC}"
    python -c "from huggingface_hub import HfApi; api = HfApi(); api.upload_folder(folder_path='.', repo_id='$HF_SPACE_NAME', repo_type='space')"
fi

echo "${GREEN}後端部署完成！${NC}"
echo "請前往 https://huggingface.co/spaces/$HF_SPACE_NAME 查看您的應用"

# 清理
echo "${YELLOW}清理臨時文件...${NC}"
cd "$REPO_ROOT"
rm -rf deployment

# 返回原始目錄
cd "$CURRENT_DIR"
