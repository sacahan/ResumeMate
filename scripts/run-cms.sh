#!/bin/zsh

# ============================================
# ResumeMate CMS Admin 本地啟動腳本
# ============================================
#
# 用途：本地開發環境中直接使用 Python 啟動 CMS 管理介面
#
# 用法：./run-cms.sh [COMMAND] [OPTIONS]
#
# 指令：
#   start             前景啟動 CMS (預設)
#   kill              終止背景執行的 CMS 程序
#   status            查看 CMS 運行狀態
#
# 環境變數：
#   CMS_ADMIN_HOST    Admin 伺服器主機 [default: 127.0.0.1]
#   CMS_ADMIN_PORT    Admin 伺服器連接埠 [default: 7870]
#   CMS_ADMIN_USER    Admin 帳號 [default: admin]
#   CMS_ADMIN_PASS    Admin 密碼 [default: changeme]

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 專案根目錄 (支援 bash 和 zsh)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# PID 檔案位置
PID_FILE="$PROJECT_ROOT/.cms.pid"
LOG_FILE="$PROJECT_ROOT/logs/cms.log"

# 幫助信息
show_help() {
    cat <<'EOF'
ResumeMate CMS Admin 本地啟動工具

用法: ./run-cms.sh [COMMAND] [OPTIONS]

指令:
  start             前景啟動 CMS (預設)
  kill              終止背景執行的 CMS 程序
  status            查看 CMS 運行狀態

選項:
  --host HOST       Admin 伺服器主機 [default: 127.0.0.1]
  --port PORT       Admin 伺服器連接埠 [default: 7870]
  --user USER       Admin 帳號 [default: admin]
  --password PASS   Admin 密碼 [default: changeme]
  --background, -b  背景執行模式
  --help            顯示此幫助信息

🚀 快速開始:

  1. 前景啟動 CMS:
     ./run-cms.sh

  2. 背景啟動 CMS:
     ./run-cms.sh --background
     ./run-cms.sh -b

  3. 終止背景 CMS:
     ./run-cms.sh kill

  4. 查看運行狀態:
     ./run-cms.sh status

  5. 訪問 CMS 管理介面:
     http://127.0.0.1:7870

  6. 帳號資訊:
     帳號: admin
     密碼: changeme

📝 自訂配置:

  ./run-cms.sh --port 8000 --user myuser --password mypass
  ./run-cms.sh -b --port 8000

🔐 安全提醒:
  - 生產環境應修改預設帳號密碼
  - 建議在 .env 檔案中設定敏感資訊

EOF
}

# 顯示互動式選單
show_menu() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  ResumeMate CMS Admin 操作選單          ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} 前景啟動 CMS"
    echo -e "  ${GREEN}2)${NC} 背景啟動 CMS"
    echo -e "  ${GREEN}3)${NC} 終止背景 CMS"
    echo -e "  ${GREEN}4)${NC} 查看運行狀態"
    echo -e "  ${GREEN}5)${NC} 查看說明"
    echo -e "  ${GREEN}0)${NC} 離開"
    echo ""
    echo -n -e "${YELLOW}請選擇操作 [0-5]: ${NC}"
    read -r choice

    case "$choice" in
        1)
            COMMAND="start"
            BACKGROUND_MODE=false
            ;;
        2)
            COMMAND="start"
            BACKGROUND_MODE=true
            ;;
        3)
            COMMAND="kill"
            ;;
        4)
            COMMAND="status"
            ;;
        5)
            show_help
            exit 0
            ;;
        0)
            echo -e "${GREEN}👋 再見！${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ 無效的選項${NC}"
            exit 1
            ;;
    esac
}

# 解析命令列參數
CMS_ADMIN_HOST="127.0.0.1"
CMS_ADMIN_PORT="7870"
CMS_ADMIN_USER="admin"
CMS_ADMIN_PASS=""
CMS_ADMIN_SHARE="false"
BACKGROUND_MODE=false
COMMAND=""

# 如果沒有傳入任何參數，顯示互動式選單
if [[ $# -eq 0 ]]; then
    show_menu
else
    # 檢查第一個參數是否為指令
    case "${1:-}" in
        kill|status)
            COMMAND="$1"
            shift
            ;;
        start)
            COMMAND="start"
            shift
            ;;
    esac
fi

while [[ $# -gt 0 ]]; do
    case $1 in
    --host)
        CMS_ADMIN_HOST="$2"
        shift 2
        ;;
    --port)
        CMS_ADMIN_PORT="$2"
        shift 2
        ;;
    --user)
        CMS_ADMIN_USER="$2"
        shift 2
        ;;
    --password)
        CMS_ADMIN_PASS="$2"
        shift 2
        ;;
    --background|-b)
        BACKGROUND_MODE=true
        shift
        ;;
    --help)
        show_help
        exit 0
        ;;
    *)
        echo -e "${RED}❌ 未知選項: $1${NC}"
        show_help
        exit 1
        ;;
    esac
done

# 如果 COMMAND 仍為空（例如只傳入 --background），預設為 start
if [[ -z "$COMMAND" ]]; then
    COMMAND="start"
fi

# 終止背景 CMS 程序
kill_cms() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${BLUE}🛑 終止 CMS 程序 (PID: $PID)...${NC}"
            kill "$PID" 2>/dev/null || true
            sleep 1
            # 如果程序還在運行，強制終止
            if ps -p "$PID" > /dev/null 2>&1; then
                echo -e "${YELLOW}⚠️  程序未正常終止，強制終止中...${NC}"
                kill -9 "$PID" 2>/dev/null || true
            fi
            rm -f "$PID_FILE"
            echo -e "${GREEN}✓ CMS 程序已終止${NC}"
        else
            echo -e "${YELLOW}⚠️  PID 檔案存在，但程序已不存在${NC}"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${YELLOW}⚠️  未找到運行中的 CMS 程序${NC}"
        echo -e "${BLUE}ℹ️  提示：可使用 'ps aux | grep admin_app' 檢查是否有殘留程序${NC}"
    fi
}

# 查看 CMS 運行狀態
status_cms() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ CMS 正在運行中 (PID: $PID)${NC}"
            echo -e "${BLUE}🔗 訪問位址：${NC}"
            echo -e "  ${GREEN}http://${CMS_ADMIN_HOST}:${CMS_ADMIN_PORT}${NC}"
            echo ""
            echo -e "${BLUE}📋 日誌檔案：${NC}"
            echo -e "  ${GREEN}${LOG_FILE}${NC}"
            echo ""
            echo -e "${YELLOW}ℹ️  使用 './run-cms.sh kill' 終止程序${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  PID 檔案存在 (PID: $PID)，但程序已不存在${NC}"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  CMS 未在背景運行${NC}"
        return 1
    fi
}

# 顯示啟動信息
show_startup_info() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  ResumeMate CMS Admin 本地啟動          ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""
    if [ "$BACKGROUND_MODE" = true ]; then
        echo -e "${GREEN}✓ 背景模式啟動中...${NC}"
    else
        echo -e "${GREEN}✓ 前景模式啟動中...${NC}"
    fi
    echo ""
    echo -e "${BLUE}📊 服務配置：${NC}"
    echo -e "  主機: ${GREEN}${CMS_ADMIN_HOST}${NC}"
    echo -e "  連接埠: ${GREEN}${CMS_ADMIN_PORT}${NC}"
    echo -e "  帳號: ${GREEN}${CMS_ADMIN_USER}${NC}"
    echo ""
    echo -e "${BLUE}🔗 訪問位址：${NC}"
    echo -e "  ${GREEN}http://${CMS_ADMIN_HOST}:${CMS_ADMIN_PORT}${NC}"
    echo ""
    echo -e "${BLUE}📝 登入認證：${NC}"
    echo -e "  帳號: ${GREEN}${CMS_ADMIN_USER}${NC}"
    echo -e "  密碼: ${GREEN}${CMS_ADMIN_PASS}${NC}"
    echo ""
    if [ "$BACKGROUND_MODE" = true ]; then
        echo -e "${YELLOW}ℹ️  背景模式：使用 './run-cms.sh kill' 終止程序${NC}"
        echo -e "${YELLOW}ℹ️  日誌輸出：${LOG_FILE}${NC}"
    else
        echo -e "${YELLOW}ℹ️  按 Ctrl+C 停止服務${NC}"
    fi
    echo ""
}

# 處理指令
case "$COMMAND" in
    kill)
        kill_cms
        exit 0
        ;;
    status)
        status_cms
        exit $?
        ;;
esac

# 切換至專案根目錄
cd "$PROJECT_ROOT"

# 載入根目錄的 .env 檔案（如果存在）
if [ -f ".env" ]; then
    echo -e "${BLUE}📋 載入環境變數...${NC}"
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    echo -e "${GREEN}✓ 已載入 .env${NC}"
fi

# 設定環境變數
export CMS_ADMIN_HOST
export CMS_ADMIN_PORT
export CMS_ADMIN_USER
export CMS_ADMIN_PASS
export CMS_ADMIN_SHARE

# 檢查是否已有背景 CMS 程序在運行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  CMS 已經在背景運行中 (PID: $PID)${NC}"
        echo -e "${BLUE}ℹ️  使用 './run-cms.sh kill' 終止現有程序${NC}"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

# 顯示啟動信息
show_startup_info

# 確保日誌目錄存在
mkdir -p "$(dirname "$LOG_FILE")"

# 啟動 CMS
if [ "$BACKGROUND_MODE" = true ]; then
    # 背景模式
    if command -v uv &>/dev/null; then
        echo -e "${BLUE}🚀 使用 uv 背景啟動 CMS...${NC}"
        nohup uv run python -m src.backend.cms.admin_app > "$LOG_FILE" 2>&1 &
    else
        echo -e "${BLUE}🚀 使用 python 背景啟動 CMS...${NC}"
        nohup python -m src.backend.cms.admin_app > "$LOG_FILE" 2>&1 &
    fi
    CMS_PID=$!
    echo "$CMS_PID" > "$PID_FILE"

    # 等待一下確認程序已啟動
    sleep 2
    if ps -p "$CMS_PID" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ CMS 已在背景啟動 (PID: $CMS_PID)${NC}"
        echo -e "${BLUE}📋 日誌檔案：${LOG_FILE}${NC}"
        echo -e "${YELLOW}ℹ️  使用 './run-cms.sh kill' 終止程序${NC}"
        echo -e "${YELLOW}ℹ️  使用 './run-cms.sh status' 查看狀態${NC}"
    else
        echo -e "${RED}❌ CMS 啟動失敗，請檢查日誌：${LOG_FILE}${NC}"
        rm -f "$PID_FILE"
        exit 1
    fi
else
    # 前景模式
    if command -v uv &>/dev/null; then
        echo -e "${BLUE}🚀 使用 uv 啟動 CMS...${NC}"
        echo ""
        uv run python -m src.backend.cms.admin_app
    else
        echo -e "${BLUE}🚀 使用 python 啟動 CMS...${NC}"
        echo ""
        python -m src.backend.cms.admin_app
    fi
fi
