#!/bin/bash
# 最安全的部署方案：純本地構建 + 手動上傳

# 輸出顏色設定
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "${BLUE}ResumeMate 前端構建與部署工具${NC}"
echo "=================================="

# 檢查前端檔案
if [ ! -f "src/frontend/index.html" ]; then
    echo "${RED}錯誤: src/frontend/index.html 不存在${NC}"
    exit 1
fi

# 創建構建目錄
BUILD_DIR="build"
echo "${YELLOW}清理並創建構建目錄: $BUILD_DIR${NC}"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# 複製檔案
echo "${YELLOW}複製前端檔案...${NC}"
cp -r src/frontend/* "$BUILD_DIR"/

# 更新配置
echo "${YELLOW}更新生產環境配置...${NC}"

# 更新 iframe URL
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' 's|http://localhost:7860|https://sacahan-resumemate-chat.hf.space|g' "$BUILD_DIR/index.html"
    # 確保相對路径正確
    sed -i '' 's|src="./data/|src="data/|g' "$BUILD_DIR/static/js/main.js" 2>/dev/null || true
else
    sed -i 's|http://localhost:7860|https://sacahan-resumemate-chat.hf.space|g' "$BUILD_DIR/index.html"
    sed -i 's|src="./data/|src="data/|g' "$BUILD_DIR/static/js/main.js" 2>/dev/null || true
fi

# 創建 CNAME 檔案（如果有自定義域名）
# echo "your-domain.com" > "$BUILD_DIR/CNAME"

# 創建 .nojekyll 檔案（避免 Jekyll 處理）
touch "$BUILD_DIR/.nojekyll"

# 創建部署資訊
cat > "$BUILD_DIR/deploy-info.json" << EOF
{
  "deployTime": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "branch": "$(git rev-parse --abbrev-ref HEAD)",
  "commit": "$(git rev-parse HEAD)",
  "version": "1.0.0"
}
EOF

echo "${GREEN}構建完成！${NC}"
echo "構建檔案位於: $BUILD_DIR/"
echo ""
echo "${BLUE}部署選項:${NC}"
echo "1. 手動上傳: 將 $BUILD_DIR/ 內容上傳到 GitHub Pages"
echo "2. 使用 GitHub CLI: gh-pages branch 推送"
echo "3. 使用 GitHub Actions: 推送到 main 分支自動部署"
echo ""

read -p "是否要使用 GitHub CLI 自動推送到 gh-pages? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "${YELLOW}使用 GitHub CLI 推送...${NC}"

    # 檢查 gh 是否安裝
    if ! command -v gh &> /dev/null; then
        echo "${YELLOW}安裝 GitHub CLI...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install gh
        else
            echo "請先安裝 GitHub CLI: https://cli.github.com/"
            exit 1
        fi
    fi

    # 檢查登入狀態
    if ! gh auth status &> /dev/null; then
        echo "${YELLOW}請登入 GitHub CLI...${NC}"
        gh auth login
    fi

    # 推送到 gh-pages
    cd "$BUILD_DIR"
    git init
    git add .
    git commit -m "deploy: 前端部署 $(date +'%Y-%m-%d %H:%M:%S')"
    git branch -M gh-pages
    git remote add origin "$(cd .. && git config --get remote.origin.url)"
    git push -f origin gh-pages
    cd ..

    echo "${GREEN}部署成功！${NC}"
    REPO_URL=$(git config --get remote.origin.url | sed 's/git@github.com:/https:\/\/github.com\//' | sed 's/.git$//')
    echo "GitHub Pages 設定: $REPO_URL/settings/pages"
else
    echo "${BLUE}手動部署步驟:${NC}"
    echo "1. 前往 GitHub repository settings"
    echo "2. 啟用 GitHub Pages"
    echo "3. 選擇 'Deploy from a branch' → 'gh-pages'"
    echo "4. 將 $BUILD_DIR/ 內容推送到 gh-pages 分支"
fi

echo ""
echo "${GREEN}構建檔案保留在: $BUILD_DIR/${NC}"
echo "如需清理，執行: rm -rf $BUILD_DIR"
