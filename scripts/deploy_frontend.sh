#!/bin/bash
# 安全的前端部署腳本 - 使用 git subtree 避免分支切換風險

# 輸出顏色設定
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "${YELLOW}開始安全部署前端到 GitHub Pages...${NC}"

# 確認在 main 分支且工作區乾淨
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "${RED}錯誤: 必須在 main 分支執行部署${NC}"
    exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
    echo "${RED}錯誤: 工作區有未提交的更改，請先提交或暫存${NC}"
    exit 1
fi

# 確保前端檔案存在
if [ ! -f "src/frontend/index.html" ]; then
    echo "${RED}錯誤: src/frontend/index.html 不存在${NC}"
    exit 1
fi

# 創建臨時構建目錄
BUILD_DIR="dist"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "${YELLOW}複製前端檔案...${NC}"
cp -r src/frontend/* "$BUILD_DIR"/

# 確保 iframe 使用正確的 HuggingFace Space URL
echo "${YELLOW}更新 iframe URL...${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' 's|http://localhost:7860|https://sacahan-resumemate-chat.hf.space|g' "$BUILD_DIR/index.html"
else
    # Linux
    sed -i 's|http://localhost:7860|https://sacahan-resumemate-chat.hf.space|g' "$BUILD_DIR/index.html"
fi

# 確保構建目錄被 git 追蹤（臨時）
git add "$BUILD_DIR"
git commit -m "temp: add build files for deployment"

echo "${YELLOW}推送到 gh-pages 分支...${NC}"
# 使用 git subtree 推送（如果 gh-pages 分支不存在會自動創建）
if git rev-parse --verify origin/gh-pages >/dev/null 2>&1; then
    # gh-pages 分支存在，推送更新
    git subtree push --prefix="$BUILD_DIR" origin gh-pages
else
    # gh-pages 分支不存在，創建並推送
    git subtree push --prefix="$BUILD_DIR" origin gh-pages
fi

# 清理臨時構建檔案
echo "${YELLOW}清理臨時檔案...${NC}"
git reset --soft HEAD~1  # 撤銷構建檔案的提交
git reset HEAD "$BUILD_DIR"  # 取消暫存
rm -rf "$BUILD_DIR"

echo "${GREEN}前端部署完成！${NC}"
echo "GitHub Pages 將在幾分鐘後更新"
echo "網站地址: https://$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^/]*\)\/\([^.]*\).*/\1.github.io\/\2/')"
