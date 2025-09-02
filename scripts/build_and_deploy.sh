#!/bin/bash
# ResumeMate 完整部署腳本 - 統一部署前端和後端

# 輸出顏色設定
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}ResumeMate 完整部署工具${NC}"
echo -e "=================================="

# 獲取腳本目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 切換到專案根目錄
cd "$REPO_ROOT"

# 檢查必要腳本是否存在
if [ ! -f "$SCRIPT_DIR/deploy_backend.sh" ]; then
    echo -e "${RED}錯誤: deploy_backend.sh 腳本不存在${NC}"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/deploy_frontend.sh" ]; then
    echo -e "${RED}錯誤: deploy_frontend.sh 腳本不存在${NC}"
    exit 1
fi

# 確保腳本有執行權限
chmod +x "$SCRIPT_DIR/deploy_backend.sh"
chmod +x "$SCRIPT_DIR/deploy_frontend.sh"

echo -e "${BLUE}部署選項:${NC}"
echo -e "1. 部署後端 (Hugging Face Spaces)"
echo -e "2. 部署前端 (GitHub Pages)"
echo -e "3. 完整部署 (後端 + 前端)"
echo -e "4. 退出"
echo -e ""

while true; do
    read -p "請選擇部署選項 (1-4): " choice
    case $choice in
        1)
            echo -e "${YELLOW}開始部署後端...${NC}"
            "$SCRIPT_DIR/deploy_backend.sh"
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}後端部署完成！${NC}"
            else
                echo -e "${RED}後端部署失敗！${NC}"
                exit 1
            fi
            break
        ;;
        2)
            echo -e "${YELLOW}開始部署前端...${NC}"
            "$SCRIPT_DIR/deploy_frontend.sh"
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}前端部署完成！${NC}"
            else
                echo -e "${RED}前端部署失敗！${NC}"
                exit 1
            fi
            break
        ;;
        3)
            echo -e "${YELLOW}開始完整部署...${NC}"
            echo -e ""
            echo -e "${BLUE}步驟 1/2: 部署後端${NC}"
            "$SCRIPT_DIR/deploy_backend.sh"
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}後端部署完成！${NC}"
                echo -e ""
                echo -e "${BLUE}步驟 2/2: 部署前端${NC}"
                "$SCRIPT_DIR/deploy_frontend.sh"
                if [ $? -eq 0 ]; then
                    echo -e ""
                    echo -e "${GREEN}=== 完整部署成功！===${NC}"
                    echo -e "後端: https://huggingface.co/spaces/sacahan/resumemate-chat"
                    echo -e "前端: https://sacahan.github.io/ResumeMate"
                else
                    echo -e "${RED}前端部署失敗！${NC}"
                    exit 1
                fi
            else
                echo -e "${RED}後端部署失敗，停止後續部署${NC}"
                exit 1
            fi
            break
        ;;
        4)
            echo -e "${YELLOW}取消部署${NC}"
            exit 0
        ;;
        *)
            echo -e "${RED}無效選項，請輸入 1-4${NC}"
        ;;
    esac
done
