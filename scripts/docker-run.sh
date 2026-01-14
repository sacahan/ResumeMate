#!/bin/bash

# ============================================
# ResumeMate Docker Compose Wrapper Script
# ============================================
# 簡化 docker compose 命令的包裝腳本
#
# 用法：./docker-run.sh [command] [service]
#
# 命令：
#   up              啟動所有服務
#   down            停止並移除所有服務
#   main            啟動主應用容器
#   admin           啟動 Admin 容器
#   restart         重啟所有服務
#   build           建置所有服務的映像
#   logs            查看容器日誌
#   status          查看服務狀態
#   shell           進入容器 shell
#   sync-deps       同步 requirements 版本號
#   clean           清理資源
#   help            顯示幫助信息
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

# 切換到 scripts 目錄以便 docker compose 找到 docker-compose.yml
cd "$SCRIPT_DIR"

# 幫助信息
show_help() {
    cat << 'EOF'
ResumeMate Docker Compose 管理工具

用法: ./docker-run.sh [command] [options]

📋 命令:

  up              啟動所有服務（main + admin）
  down            停止並移除所有服務
  main            啟動只有主應用的容器
  admin           啟動只有 Admin 的容器
  restart         重啟所有服務 (或指定服務)
  build           建置所有服務的映像 (或指定服務)
  logs            查看容器日誌 (支援 -f 參數跟蹤)
  status          查看服務狀態
  shell           進入容器 shell (預設 main，可指定 admin)
  sync-deps       同步 requirements 版本號到分離檔案
  clean           清理資源 (容器、映像、卷)
  help            顯示此幫助信息

🚀 快速開始:

  1. 複製環境變數檔案:
     cp .env.main.example .env.main
     cp .env.admin.example .env.admin
     # 編輯 .env.main 和 .env.admin 設定必要的環境變數

  2. 建置並啟動服務:
     ./docker-run.sh build
     ./docker-run.sh up

  3.查看日誌:
     ./docker-run.sh logs       # 查看所有服務
     ./docker-run.sh logs -f    # 跟蹤日誌

  4. 進入 Admin 容器:
     ./docker-run.sh shell admin

  5. 停止服務:
     ./docker-run.sh down

🔗 服務端點:
  主應用 (Gradio UI):  http://localhost:8459
  Admin 管理介面:      http://localhost:7870

📝 環境配置:
  - .env.main       主應用環境變數
  - .env.admin      Admin 環境變數
  日誌目錄:           ../logs/
  向量資料庫:         ../chroma_db/

💡 常用命令快速參考:

  建置:     docker compose build [service]
  啟動:     docker compose up -d [service]
  停止:     docker compose down
  重啟:     docker compose restart [service]
  查看狀態:   docker compose ps
  查看日誌:   docker compose logs -f [service]

EOF
}

# 顯示服務信息
show_info() {
    echo ""
    echo -e "${BLUE}📊 ResumeMate 服務配置${NC}"
    echo -e "${BLUE}═════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${BLUE}服務端點:${NC}"
    echo -e "    主應用:    http://localhost:${HOST_PORT:-8459}"
    echo -e "    Admin:     http://localhost:${ADMIN_PORT:-7870}"
    echo ""
    echo -e "  ${BLUE}本地目錄:${NC}"
    echo -e "    日誌:      $PROJECT_DIR/logs"
    echo -e "    向量資料庫: $PROJECT_DIR/chroma_db"
    echo -e "    圖片:      $PROJECT_DIR/src/frontend/static/images/infographics"
    echo ""
    echo -e "  ${BLUE}常用命令:${NC}"
    echo -e "    ${GREEN}./docker-run.sh logs${NC}        # 查看日誌"
    echo -e "    ${GREEN}./docker-run.sh shell admin${NC} # 進入 Admin 容器"
    echo -e "    ${GREEN}./docker-run.sh status${NC}      # 查看狀態"
    echo -e "    ${GREEN}./docker-run.sh down${NC}        # 停止服務"
    echo ""
}

# 檢查環境變數檔案
check_env_files() {
    if [ ! -f ".env.main" ]; then
        echo -e "${YELLOW}⚠️  未找到 .env.main${NC}"
        echo -e "${YELLOW}正在從示例複製...${NC}"
        cp .env.main.example .env.main
        echo -e "${GREEN}✓ 已建立 .env.main (請編輯後再執行)${NC}"
        echo -e "${YELLOW}請編輯 .env.main 檔案配置必要的環境變數${NC}"
        return 1
    fi

    if [ ! -f ".env.admin" ]; then
        echo -e "${YELLOW}⚠️  未找到 .env.admin${NC}"
        echo -e "${YELLOW}正在從示例複製...${NC}"
        cp .env.admin.example .env.admin
        echo -e "${GREEN}✓ 已建立 .env.admin (請編輯後再執行)${NC}"
        echo -e "${YELLOW}請編輯 .env.admin 檔案配置必要的環境變數${NC}"
        return 1
    fi

    return 0
}

# 同步依賴
sync_requirements() {
    echo -e "${BLUE}🔄 同步 requirements...${NC}"
    bash sync-requirements.sh
    echo -e "${GREEN}✓ 同步完成${NC}"
}

# 主函式
main() {
    local command=${1:-help}

    case "$command" in
        up)
            echo -e "${BLUE}🚀 啟動所有服務...${NC}"
            check_env_files || exit 1
            docker compose up -d
            show_info
            ;;
        down)
            echo -e "${BLUE}🛑 停止所有服務...${NC}"
            docker compose down
            echo -e "${GREEN}✓ 服務已停止${NC}"
            ;;
        main)
            echo -e "${BLUE}🚀 啟動主應用...${NC}"
            check_env_files || exit 1
            docker compose up -d main
            echo -e "${GREEN}✓ 主應用已啟動${NC}"
            echo -e "  訪問: http://localhost:${HOST_PORT:-8459}"
            ;;
        admin)
            echo -e "${BLUE}🚀 啟動 Admin 應用...${NC}"
            check_env_files || exit 1
            docker compose up -d admin
            echo -e "${GREEN}✓ Admin 應用已啟動${NC}"
            echo -e "  訪問: http://localhost:${ADMIN_PORT:-7870}"
            ;;
        restart)
            local service=${2:-}
            if [ -z "$service" ]; then
                echo -e "${BLUE}🔄 重啟所有服務...${NC}"
                docker compose restart
            else
                echo -e "${BLUE}🔄 重啟 $service...${NC}"
                docker compose restart "$service"
            fi
            echo -e "${GREEN}✓ 重啟完成${NC}"
            ;;
        build)
            local service=${2:-}
            if [ -z "$service" ]; then
                echo -e "${BLUE}🔨 建置所有服務的映像...${NC}"
                docker compose build
            else
                echo -e "${BLUE}🔨 建置 $service 映像...${NC}"
                docker compose build "$service"
            fi
            echo -e "${GREEN}✓ 建置完成${NC}"
            ;;
        logs)
            local service=${2:-}
            if [ -z "$service" ]; then
                echo -e "${BLUE}📋 顯示所有服務日誌...${NC}"
                docker compose logs -f
            else
                echo -e "${BLUE}📋 顯示 $service 日誌...${NC}"
                docker compose logs -f "$service"
            fi
            ;;
        status|ps)
            echo -e "${BLUE}📊 服務狀態:${NC}"
            docker compose ps
            ;;
        shell)
            local service=${2:-main}
            echo -e "${BLUE}🐚 進入 $service 容器...${NC}"
            docker compose exec "$service" /bin/bash
            ;;
        sync-deps)
            check_env_files || exit 1
            sync_requirements
            ;;
        clean)
            echo -e "${YELLOW}⚠️  此操作將刪除所有容器和映像...${NC}"
            read -p "確認要繼續嗎？(y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${BLUE}清理中...${NC}"
                docker compose down -v
                docker rmi resumemate-main resumemate-admin 2>/dev/null || true
                echo -e "${GREEN}✓ 清理完成${NC}"
            else
                echo -e "${YELLOW}已取消${NC}"
            fi
            ;;
        help|-h|--help)
            show_help
            ;;
        *)
            echo -e "${RED}❌ 未知命令: $command${NC}"
            echo ""
            echo -e "${BLUE}使用 '${GREEN}./docker-run.sh help${BLUE}' 查看完整幫助信息${NC}"
            exit 1
            ;;
    esac
}

main "$@"
