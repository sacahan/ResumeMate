#!/bin/bash

# ============================================
# ResumeMate 服務啟動腳本
# ============================================
# 同時啟動主應用 (port 7860) 和 Infographics Admin (port 7870)
#
# 此腳本設計用於 Docker 容器內執行

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# PID 檔案
ADMIN_PID_FILE="/tmp/admin_app.pid"

# 清理函數 - 處理信號時終止所有子程序
cleanup() {
    echo -e "\n${YELLOW}收到終止信號，正在關閉服務...${NC}"

    # 終止 admin_app
    if [ -f "$ADMIN_PID_FILE" ]; then
        ADMIN_PID=$(cat "$ADMIN_PID_FILE")
        if kill -0 "$ADMIN_PID" 2>/dev/null; then
            echo -e "${BLUE}停止 Infographics Admin (PID: $ADMIN_PID)...${NC}"
            kill "$ADMIN_PID" 2>/dev/null || true
        fi
        rm -f "$ADMIN_PID_FILE"
    fi

    # 終止所有子程序
    jobs -p | xargs -r kill 2>/dev/null || true

    echo -e "${GREEN}服務已關閉${NC}"
    exit 0
}

# 註冊信號處理
trap cleanup SIGTERM SIGINT SIGQUIT

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   ResumeMate 服務啟動中...${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 顯示環境資訊
echo -e "${BLUE}📋 服務配置：${NC}"
echo -e "  主應用連接埠: ${GRADIO_SERVER_PORT:-7860}"
echo -e "  Admin 連接埠: ${INFOGRAPHICS_ADMIN_PORT:-7870}"
echo -e "  Git 自動提交: ${INFOGRAPHICS_GIT_AUTO_COMMIT:-false}"
echo -e "  Git 自動推送: ${INFOGRAPHICS_GIT_AUTO_PUSH:-false}"
echo ""

# 啟動 Infographics Admin（背景）
echo -e "${BLUE}🚀 啟動 Infographics Admin...${NC}"
python -m src.backend.infographics.admin_app &
ADMIN_PID=$!
echo "$ADMIN_PID" >"$ADMIN_PID_FILE"
echo -e "${GREEN}✓ Infographics Admin 已啟動 (PID: $ADMIN_PID)${NC}"

# 等待 Admin 啟動
sleep 2

# 檢查 Admin 是否正常運行
if ! kill -0 "$ADMIN_PID" 2>/dev/null; then
    echo -e "${RED}✗ Infographics Admin 啟動失敗${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}🚀 啟動主應用...${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# 啟動主應用（前台）
# 這會阻塞直到主應用退出
python app.py

# 如果主應用退出，清理並退出
cleanup
