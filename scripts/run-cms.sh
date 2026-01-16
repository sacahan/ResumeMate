#!/bin/zsh

# ============================================
# ResumeMate CMS Admin 本地啟動腳本
# ============================================
#
# 用途：本地開發環境中直接使用 Python 啟動 CMS 管理介面
#
# 用法：./run-cms.sh [OPTIONS]
#
# 環境變數：
#   CMS_ADMIN_HOST    Admin 伺服器主機 [default: 127.0.0.1]
#   CMS_ADMIN_PORT    Admin 伺服器連接埠 [default: 7861]
#   CMS_ADMIN_USER    Admin 帳號 [default: admin]
#   CMS_ADMIN_PASS    Admin 密碼 [default: changeme]

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 專案根目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 幫助信息
show_help() {
    cat <<'EOF'
ResumeMate CMS Admin 本地啟動工具

用法: ./run-cms.sh [OPTIONS]

選項:
  --host HOST       Admin 伺服器主機 [default: 127.0.0.1]
  --port PORT       Admin 伺服器連接埠 [default: 7861]
  --user USER       Admin 帳號 [default: admin]
  --password PASS   Admin 密碼 [default: changeme]
  --help            顯示此幫助信息

🚀 快速開始:

  1. 啟動 CMS:
     ./run-cms.sh

  2. 訪問 CMS 管理介面:
     http://127.0.0.1:7861

  3. 帳號資訊:
     帳號: admin
     密碼: changeme

📝 自訂配置:

  ./run-cms.sh --port 8000 --user myuser --password mypass

🔐 安全提醒:
  - 生產環境應修改預設帳號密碼
  - 建議在 .env 檔案中設定敏感資訊

EOF
}

# 解析命令列參數
CMS_ADMIN_HOST="${CMS_ADMIN_HOST:-127.0.0.1}"
CMS_ADMIN_PORT="${CMS_ADMIN_PORT:-7861}"
CMS_ADMIN_USER="${CMS_ADMIN_USER:-admin}"
CMS_ADMIN_PASS="${CMS_ADMIN_PASS:-changeme}"
CMS_ADMIN_SHARE="${CMS_ADMIN_SHARE:-false}"

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

# 顯示啟動信息
show_startup_info() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  ResumeMate CMS Admin 本地啟動          ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}✓ 啟動中...${NC}"
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
    echo -e "${YELLOW}ℹ️  按 Ctrl+C 停止服務${NC}"
    echo ""
}

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

# 顯示啟動信息
show_startup_info

# 啟動 CMS
if command -v uv &>/dev/null; then
    echo -e "${BLUE}🚀 使用 uv 啟動 CMS...${NC}"
    echo ""
    uv run python -m src.backend.cms.admin_app
else
    echo -e "${BLUE}🚀 使用 python 啟動 CMS...${NC}"
    echo ""
    python -m src.backend.cms.admin_app
fi
