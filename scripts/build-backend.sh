#!/bin/zsh

# ============================================
# ResumeMate Docker Image Build Script (簡化版)
# ============================================
# 建置並推送 Docker 映像至 Docker Hub
#
# 用法：./build-backend.sh [OPTIONS]
#
# Options:
#   --platform PLATFORM   架構選擇: arm64, amd64, 或 all [default: all]
#   --action ACTION       動作: build, push, 或 build-push [default: build-push]
#   --tag TAG            映像標籤 [default: latest]
#   --no-interactive     非互動模式，使用預設值
#   --help               顯示幫助信息

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 配置
DOCKER_USERNAME="${DOCKER_USERNAME:-sacahan}"
DOCKER_TAG="${DOCKER_TAG:-latest}"
IMAGE_NAME="resumemate"
FULL_IMAGE_NAME="$DOCKER_USERNAME/$IMAGE_NAME"

# 幫助信息
show_help() {
    cat << 'EOF'
ResumeMate Docker 映像建置腳本

用法: ./build-backend.sh [OPTIONS]

選項：
  --platform PLATFORM   架構選擇 (arm64, amd64, all) [default: all]
  --action ACTION       動作 (build, push, build-push) [default: build-push]
  --tag TAG            映像標籤 [default: latest]
  --no-interactive     非互動模式
  --help               顯示此幫助信息

💡 範例：

  # 建置 arm64 映像
  ./build-backend.sh --platform arm64 --action build

  # 建置並推送到 Docker Hub
  ./build-backend.sh --platform all --action build-push

  # 僅推送既有映像
  ./build-backend.sh --action push

🔗 映像名稱: sacahan/resumemate:latest

EOF
}

# 解析命令列參數
PLATFORM=""
ACTION=""
INTERACTIVE=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --action)
            ACTION="$2"
            shift 2
            ;;
        --tag)
            DOCKER_TAG="$2"
            shift 2
            ;;
        --no-interactive)
            INTERACTIVE=false
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "❌ 未知選項: $1"
            show_help
            exit 1
            ;;
    esac
done

# 互動式平台選擇
if [ -z "$PLATFORM" ] && [ "$INTERACTIVE" = true ]; then
    echo ""
    echo "════════════════════════════════════════"
    echo "架構選擇"
    echo "════════════════════════════════════════"
    echo "1. arm64 (M1/M2/M3 Mac, ARM 伺服器)"
    echo "2. amd64 (Intel Mac, x86_64 伺服器)"
    echo "3. all (arm64 + amd64) [default]"
    echo ""
    read "?選擇架構 (1-3) [default: 3]: " platform_choice
    platform_choice=${platform_choice:-3}

    case $platform_choice in
        1) PLATFORM="arm64" ;;
        2) PLATFORM="amd64" ;;
        3) PLATFORM="all" ;;
        *)
            echo "❌ 選擇無效，使用預設值: all"
            PLATFORM="all"
            ;;
    esac
elif [ -z "$PLATFORM" ]; then
    PLATFORM="all"
fi

# 驗證平台選擇
case $PLATFORM in
    arm64) PLATFORMS="linux/arm64" ;;
    amd64) PLATFORMS="linux/amd64" ;;
    all)   PLATFORMS="linux/arm64,linux/amd64" ;;
    *)
        echo "❌ 無效的架構: $PLATFORM"
        exit 1
        ;;
esac

# 互動式動作選擇
if [ -z "$ACTION" ] && [ "$INTERACTIVE" = true ]; then
    echo ""
    echo "════════════════════════════════════════"
    echo "動作選擇"
    echo "════════════════════════════════════════"
    echo "1. build (僅建置，不推送)"
    echo "2. push (僅推送既有映像)"
    echo "3. build-push (建置並推送) [default]"
    echo ""
    read "?選擇動作 (1-3) [default: 3]: " action_choice
    action_choice=${action_choice:-3}

    case $action_choice in
        1) ACTION="build" ;;
        2) ACTION="push" ;;
        3) ACTION="build-push" ;;
        *)
            echo "❌ 選擇無效，使用預設值: build-push"
            ACTION="build-push"
            ;;
    esac
elif [ -z "$ACTION" ]; then
    ACTION="build-push"
fi

# 驗證動作選擇
case $ACTION in
    build|push|build-push) ;;
    *)
        echo "❌ 無效的動作: $ACTION"
        exit 1
        ;;
esac

# 設定 Docker buildx
setup_buildx() {
    echo ""
    echo "⚙️  設定 Docker buildx 多平台建置..."
    echo "════════════════════════════════════════"

    BUILDER_NAME="multiarch-builder"

    if ! docker buildx inspect "$BUILDER_NAME" &> /dev/null; then
        echo "正在建立 buildx builder: $BUILDER_NAME"
        docker buildx create --name "$BUILDER_NAME" --driver docker-container --use
    else
        echo "使用既有 buildx builder: $BUILDER_NAME"
        docker buildx use "$BUILDER_NAME"
    fi

    docker buildx inspect --bootstrap

    echo "正在註冊 QEMU multiarch 支援..."
    docker run --rm --privileged tonistiigi/binfmt:latest --install all || \
    docker run --rm --privileged multiarch/qemu-user-static --reset -p yes || true

    echo "✅ Docker buildx 設定完成!"
}

# 主執行
echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║  ResumeMate Docker - 映像建置                   ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "📋 配置："
echo "   映像名稱: $FULL_IMAGE_NAME:$DOCKER_TAG"
echo "   架構:     $PLATFORMS"
echo "   動作:     $ACTION"
echo ""

# 設定 buildx
setup_buildx

# Step 1: 建置 (如果動作是 build 或 build-push)
if [ "$ACTION" != "push" ]; then
    echo ""
    echo "🔨 建置 Docker 映像..."
    echo "════════════════════════════════════════"

    cd "$PROJECT_ROOT"

    # 決定推送旗標
    PUSH_FLAG="--load"
    if [ "$ACTION" = "build-push" ]; then
        PUSH_FLAG="--push"
    fi

    docker buildx build \
        --platform "$PLATFORMS" \
        $PUSH_FLAG \
        -t "$FULL_IMAGE_NAME:$DOCKER_TAG" \
        -f "$SCRIPT_DIR/Dockerfile" \
        "$PROJECT_ROOT"

    echo "✅ 映像建置成功!"
else
    echo ""
    echo "⏭️  跳過建置步驟 (僅推送模式)"
fi

# Step 2: 推送 (僅在 push 動作時，推送既有映像)
if [ "$ACTION" = "push" ]; then
    echo ""
    echo "📤 推送 Docker 映像至 Registry..."
    echo "════════════════════════════════════════"

    docker push "$FULL_IMAGE_NAME:$DOCKER_TAG"

    echo "✅ 映像推送成功!"
elif [ "$ACTION" = "build" ]; then
    echo ""
    echo "⏭️  跳過推送步驟 (僅建置模式)"
fi

echo ""
echo "✅ 建置流程完成!"
echo ""
echo "下一步："
echo "  - 驗證映像: docker images | grep $IMAGE_NAME"
echo "  - 啟動容器: cd scripts && ./docker-run.sh run"
