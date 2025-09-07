#!/bin/bash
# 簡化的前端部署腳本 - 觸發 GitHub Actions 自動部署

# 輸出顏色設定
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}準備部署前端到 GitHub Pages...${NC}"

# 檢查是否在 main 分支
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${YELLOW}正在切換到 main 分支...${NC}"
    git checkout main
fi

if [ -n "$(git status --porcelain)" ]; then
    echo -e "${RED}錯誤: 工作區有未提交的更改，請先提交更改${NC}"
    echo -e "${YELLOW}未提交的檔案:${NC}"
    git status --porcelain
    exit 1
fi

# 確認前端檔案存在
if [ ! -f "src/frontend/index.html" ]; then
    echo -e "${RED}錯誤: src/frontend/index.html 不存在${NC}"
    exit 1
fi

echo -e "${YELLOW}推送到 main 分支...${NC}"
git push origin main

echo -e "${YELLOW}手動觸發 GitHub Actions 部署...${NC}"
# 檢查是否安裝了 gh CLI
if command -v gh &> /dev/null; then
    gh workflow run deploy-pages.yml
    echo -e "${GREEN}GitHub Actions 已手動觸發！${NC}"
else
    echo -e "${YELLOW}注意: 未安裝 GitHub CLI (gh)${NC}"
    echo -e "${YELLOW}請手動到 GitHub Actions 頁面觸發 'Deploy to GitHub Pages' workflow${NC}"
fi

echo -e "${GREEN}部署請求已提交！${NC}"
echo -e "${YELLOW}GitHub Actions 將自動處理前端部署...${NC}"
echo -e "檢查部署狀態: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^/]*\)\/\([^.]*\).*/\1\/\2/')/actions"
echo -e "網站地址: https://$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^/]*\)\/\([^.]*\).*/\1.github.io\/\2/')"
