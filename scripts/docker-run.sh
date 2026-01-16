#!/bin/bash

# ============================================
# ResumeMate Docker 管理腳本 (簡化版)
# ============================================
#
# 用法：./docker-run.sh [command]
#
# 命令：
#   build               建置映像
#   run, up             啟動容器
#   stop, down          停止容器
#   logs                查看容器日誌
#   shell               進入容器 shell
#   status, ps          查看容器狀態
#   clean               清理資源
#   help                顯示幫助信息

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

ENV_FILE="$PROJECT_DIR/.env.docker"
if [[ ! -f "$ENV_FILE" && -f "$SCRIPT_DIR/.env.docker" ]]; then
    ENV_FILE="$SCRIPT_DIR/.env.docker"
fi
if [[ -z "${GRADIO_SERVER_PORT:-}" && -f "$ENV_FILE" ]]; then
    # shellcheck disable=SC1090
    set -a
    source "$ENV_FILE"
    set +a
fi
CONTAINER_NAME="resumemate"
IMAGE_NAME="sacahan/resumemate"
CONTAINER_PORT="${GRADIO_SERVER_PORT:-7860}"
HOST_PORT="${HOST_PORT:-$CONTAINER_PORT}"

# 掛載目錄
CHROMA_DB_PATH="${PROJECT_DIR}/chroma_db"
LOGS_DIR="${PROJECT_DIR}/logs"
LITELLM_TOKEN_DIR="${PROJECT_DIR}/github_copilot"

# 幫助信息
show_help() {
    cat << 'EOF'
ResumeMate Docker 管理工具

用法: ./docker-run.sh [command]

📋 命令:

  build               建置映像
  run, up             啟動容器
  stop, down          停止容器
  logs                查看容器日誌 (使用 -f 參數跟蹤)
  shell               進入容器 shell
  status, ps          查看容器狀態
  clean               清理容器、映像
  help                顯示此幫助信息

🚀 快速開始:

  1. 設定環境變數 (複製根目錄 .env.example):
     cp .env.example .env
     # 編輯 .env 檔案設定必要的環境變數

  2. 建置映像:
     ./docker-run.sh build

  3. 啟動容器:
     ./docker-run.sh run

  4. 查看日誌:
     ./docker-run.sh logs -f

  5. 進入容器:
     ./docker-run.sh shell

  6. 停止容器:
     ./docker-run.sh stop

🔗 服務端點:
  主應用 (Gradio UI):  http://localhost:8459

📁 掛載目錄:
  - Host: ./chroma_db → Container: /app/chroma_db
  - Host: ./logs → Container: /app/logs
  - Host: ./github_copilot → Container: /root/.config/litellm/github_copilot

💡 環境變數:
  使用根目錄 .env 檔案，包含：
  - GITHUB_COPILOT_TOKEN (必要)
  - AGENT_MODEL
  - EMBEDDING_PROVIDER 等

EOF
}

# 顯示服務信息
show_info() {
    echo ""
    echo -e "${BLUE}📊 ResumeMate Docker 容器信息${NC}"
    echo -e "${BLUE}════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${BLUE}服務端點:${NC}"
    echo -e "    http://localhost:${HOST_PORT}"
    echo ""
    echo -e "  ${BLUE}本地目錄:${NC}"
    echo -e "    日誌:      $PROJECT_DIR/logs"
    echo -e "    向量資料庫: $PROJECT_DIR/chroma_db"
    echo ""
    echo -e "  ${BLUE}常用命令:${NC}"
    echo -e "    ${GREEN}./docker-run.sh logs${NC}   # 查看日誌"
    echo -e "    ${GREEN}./docker-run.sh shell${NC}  # 進入容器"
    echo -e "    ${GREEN}./docker-run.sh stop${NC}   # 停止容器"
    echo ""
}

# 建立必要的本地目錄
ensure_directories() {
    mkdir -p "$PROJECT_DIR/chroma_db" "$PROJECT_DIR/logs"
}

# 主函式
main() {
    local command=${1:-help}
    shift || true

    case "$command" in
        build)
            echo -e "${BLUE}🔨 建置映像 $IMAGE_NAME...${NC}"
            docker build -t "$IMAGE_NAME" -f "$SCRIPT_DIR/Dockerfile" "$PROJECT_DIR"
            echo -e "${GREEN}✓ 建置完成${NC}"
            ;;
        run|up)
            echo -e "${BLUE}🚀 啟動容器...${NC}"
            ensure_directories

            # 檢查容器是否已存在
            if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
                echo -e "${YELLOW}容器已存在，移除舊容器...${NC}"
                docker rm -f "$CONTAINER_NAME" > /dev/null
            fi

            docker run -d \
                --name "$CONTAINER_NAME" \
                -p "${HOST_PORT}:${CONTAINER_PORT}" \
                -v "$CHROMA_DB_PATH:/app/chroma_db" \
                -v "$LOGS_DIR:/app/logs" \
                -v "$LITELLM_TOKEN_DIR:/root/.config/litellm/github_copilot" \
                --env-file "$ENV_FILE" \
                "$IMAGE_NAME"

            echo -e "${GREEN}✓ 容器已啟動${NC}"
            show_info
            ;;
        stop|down)
            echo -e "${BLUE}🛑 停止容器...${NC}"
            if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
                docker stop "$CONTAINER_NAME" > /dev/null
                docker rm "$CONTAINER_NAME" > /dev/null
                echo -e "${GREEN}✓ 容器已停止${NC}"
            else
                echo -e "${YELLOW}⚠️  容器不存在${NC}"
            fi
            ;;
        logs)
            echo -e "${BLUE}📋 容器日誌${NC}"
            if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
                docker logs "$@" "$CONTAINER_NAME"
            else
                echo -e "${RED}❌ 容器不存在${NC}"
                exit 1
            fi
            ;;
        shell)
            echo -e "${BLUE}🐚 進入容器 shell...${NC}"
            if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
                docker exec -it "$CONTAINER_NAME" /bin/bash
            else
                echo -e "${RED}❌ 容器未運行${NC}"
                exit 1
            fi
            ;;
        status|ps)
            echo -e "${BLUE}📊 容器狀態:${NC}"
            docker ps -a --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
            ;;
        clean)
            echo -e "${YELLOW}⚠️  此操作將刪除容器和映像...${NC}"
            read -p "確認要繼續嗎？(y/N) " -r reply
            echo
            if [[ $reply =~ ^[Yy]$ ]]; then
                echo -e "${BLUE}清理中...${NC}"
                docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
                docker rmi "$IMAGE_NAME" 2>/dev/null || true
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
