title: ResumeMate Chat
#!/bin/zsh
# 前端部署腳本 - GitHub Pages

# 輸出顏色設定
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "${YELLOW}開始部署前端到 GitHub Pages...${NC}"

# 確認當前目錄
CURRENT_DIR=$(pwd)
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# 檢查 gh 是否安裝
if ! command -v gh &> /dev/null; then
    echo "${YELLOW}未偵測到 GitHub CLI (gh)，正在安裝...${NC}"
    brew install gh
fi

# 檢查是否已登入 GitHub CLI
if ! gh auth status &> /dev/null; then
    echo "${YELLOW}請登入 GitHub CLI...${NC}"
    gh auth login
fi

# 建立 gh-pages 分支（如不存在）
if ! git show-ref --quiet refs/heads/gh-pages; then
    echo "${YELLOW}建立 gh-pages 分支...${NC}"
    git checkout --orphan gh-pages
    git rm -rf .
    echo "ResumeMate GitHub Pages" > index.html
    git add index.html
    git commit -m "init gh-pages"
    git push origin gh-pages
    git checkout main
fi

# 清理暫存目錄
rm -rf /tmp/resumemate-gh-pages
mkdir -p /tmp/resumemate-gh-pages

# 複製前端檔案到暫存目錄
cp -r src/frontend/* /tmp/resumemate-gh-pages/

# 切換到 gh-pages 分支
git checkout gh-pages

# 清除舊檔案
git rm -rf .

# 複製新檔案
cp -r /tmp/resumemate-gh-pages/* .

# 加入並提交
git add .
git commit -m "deploy: update frontend for GitHub Pages"
git push origin gh-pages

echo "${GREEN}前端已部署到 GitHub Pages！${NC}"
REPO_URL=$(git config --get remote.origin.url | sed 's/.git$//')
echo "請前往 ${REPO_URL}/tree/gh-pages 或設定 GitHub Pages 以查看您的網站"

# 返回 main 分支
git checkout main

# 清理暫存目錄
rm -rf /tmp/resumemate-gh-pages

# 返回原始目錄
cd "$CURRENT_DIR"
