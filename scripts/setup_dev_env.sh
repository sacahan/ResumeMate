#!/bin/zsh
# ResumeMate 開發環境初始化腳本

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "${GREEN}開始初始化 ResumeMate 開發環境...${NC}"

# 檢查 Python 版本
python_version=$(python3 --version 2>&1)
echo "檢測到 Python 版本: $python_version"
if [[ $python_version != *"Python 3.1"* ]] && [[ $python_version != *"Python 3.2"* ]]; then
    echo "${RED}需要 Python 3.10 或更高版本! 請升級您的 Python.${NC}"
    exit 1
fi

# 建立虛擬環境
echo "${YELLOW}建立虛擬環境...${NC}"
python3 -m venv .venv
source .venv/bin/activate

# 安裝依賴
echo "${YELLOW}安裝依賴...${NC}"
pip install -U pip
pip install -e ".[dev]"

# 產生 .env 檔案
if [ ! -f .env ]; then
    echo "${YELLOW}產生 .env 檔案...${NC}"
    cp .env.example .env
    echo "${GREEN}.env 檔案已產生，請編輯填入您的 API 金鑰與 Token${NC}"
else
    echo "${YELLOW}.env 檔案已存在，跳過產生${NC}"
fi

# 設定 pre-commit hook
echo "${YELLOW}設定 pre-commit hook...${NC}"
cat > .git/hooks/pre-commit << EOF
#!/bin/sh
isort src tests
black src tests
flake8 src tests
EOF
chmod +x .git/hooks/pre-commit

echo "${GREEN}開發環境初始化完成！${NC}"
echo "請運行: source .venv/bin/activate 啟動虛擬環境"
echo "然後編輯 .env 檔案，設定您的 OpenAI API 金鑰與 Token"
