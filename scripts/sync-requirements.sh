#!/bin/bash

# ============================================
# ResumeMate Requirements Sync Script
# ============================================
# 自動同步 requirements.txt 版本號到
# requirements-main.txt 和 requirements-admin.txt
#
# 用法: ./sync-requirements.sh
#

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 專案根目錄（相對於此腳本）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 檔案路徑
REQUIREMENTS_FILE="$PROJECT_DIR/requirements.txt"
REQUIREMENTS_MAIN="$SCRIPT_DIR/requirements-main.txt"
REQUIREMENTS_ADMIN="$SCRIPT_DIR/requirements-admin.txt"

# 檢查檔案是否存在
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${RED}✗ 找不到 $REQUIREMENTS_FILE${NC}"
    exit 1
fi

if [ ! -f "$REQUIREMENTS_MAIN" ]; then
    echo -e "${RED}✗ 找不到 $REQUIREMENTS_MAIN${NC}"
    exit 1
fi

if [ ! -f "$REQUIREMENTS_ADMIN" ]; then
    echo -e "${RED}✗ 找不到 $REQUIREMENTS_ADMIN${NC}"
    exit 1
fi

echo -e "${BLUE}同步 requirements 版本號...${NC}"
echo ""

# 主應用依賴列表
MAIN_DEPS=(
    "gradio"
    "chromadb"
    "openai"
    "openai-agents"
    "litellm"
    "langchain"
    "pydantic"
    "python-dotenv"
)

# Admin 依賴列表
ADMIN_DEPS=(
    "gradio"
    "Pillow"
    "openai"
    "litellm"
    "pydantic"
    "python-dotenv"
)

# 提取版本號函數
get_version() {
    local package=$1
    grep "^${package}" "$REQUIREMENTS_FILE" | head -1 || echo ""
}

# 更新檔案中的版本號
update_version_in_file() {
    local file=$1
    local package=$2
    local version=$3

    if [ -z "$version" ]; then
        return
    fi

    # 檢查是否已存在
    if grep -q "^${package}[>=<]" "$file"; then
        # 使用 sed 更新版本
        sed -i '' "s/^${package}[>=<].*/$(echo "$version" | sed 's/[\/&]/\\&/g')/" "$file"
        echo -e "  ${GREEN}✓${NC} $package: $(echo "$version" | awk '{print $NF}')"
    fi
}

# 同步主應用依賴
echo -e "${BLUE}📦 同步主應用依賴...${NC}"
for dep in "${MAIN_DEPS[@]}"; do
    version=$(get_version "$dep")
    if [ -n "$version" ]; then
        update_version_in_file "$REQUIREMENTS_MAIN" "$dep" "$version"
    fi
done

echo ""

# 同步 Admin 依賴
echo -e "${BLUE}📦 同步 Admin 依賴...${NC}"
for dep in "${ADMIN_DEPS[@]}"; do
    version=$(get_version "$dep")
    if [ -n "$version" ]; then
        update_version_in_file "$REQUIREMENTS_ADMIN" "$dep" "$version"
    fi
done

echo ""
echo -e "${GREEN}✓ 同步完成${NC}"
echo ""
echo -e "${BLUE}檔案已更新：${NC}"
echo "  - $REQUIREMENTS_MAIN"
echo "  - $REQUIREMENTS_ADMIN"
