#!/bin/bash
# =============================================================================
# 深寻觅 AI Coach - 停止脚本
# 一键停止所有服务
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 打印Banner
print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║           🛑 深寻觅 AI Coach - 停止脚本                      ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 显示帮助
show_help() {
    echo "深寻觅 AI Coach 停止脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help       显示帮助信息"
    echo "  -v, --volumes    同时删除数据卷（谨慎使用）"
    echo "  -i, --images     同时删除镜像"
    echo "  -a, --all        停止并清理所有资源（包括数据）"
    echo "  -f, --force      强制停止，不提示确认"
    echo ""
}

# 停止服务
stop_services() {
    log_info "正在停止服务..."
    
    if docker compose ps -q | grep -q .; then
        if docker compose down; then
            log_success "服务已停止"
        else
            log_error "停止服务失败"
            exit 1
        fi
    else
        log_warning "没有运行中的服务"
    fi
}

# 删除数据卷
cleanup_volumes() {
    log_info "删除数据卷..."
    
    # 删除命名卷
    docker volume rm -f ai_coach_redis_data 2>/dev/null || true
    
    # 清理未使用的卷
    docker volume prune -f &>/dev/null || true
    
    log_success "数据卷已清理"
}

# 删除镜像
cleanup_images() {
    log_info "删除镜像..."
    
    # 删除项目相关镜像
    docker images --filter "reference=shenxunmi/ai-coach-*" -q | xargs -r docker rmi -f 2>/dev/null || true
    
    log_success "镜像已清理"
}

# 完整清理
cleanup_all() {
    log_warning "这将删除所有数据，包括数据库和日志！"
    
    if [ "$FORCE" != "true" ]; then
        read -p "确定要继续吗? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "操作已取消"
            exit 0
        fi
    fi
    
    log_info "执行完整清理..."
    
    # 停止并删除容器
    docker compose down --volumes --remove-orphans 2>/dev/null || true
    
    # 删除数据目录
    if [ -d "data" ]; then
        rm -rf data/*
        log_info "数据目录已清空"
    fi
    
    if [ -d "logs" ]; then
        rm -rf logs/*
        log_info "日志目录已清空"
    fi
    
    if [ -d "temp" ]; then
        rm -rf temp/*
        log_info "临时目录已清空"
    fi
    
    # 清理卷和镜像
    cleanup_volumes
    cleanup_images
    
    # 清理构建缓存
    docker builder prune -f &>/dev/null || true
    
    log_success "完整清理完成"
}

# 显示状态
show_status() {
    echo ""
    log_success "✅ 深寻觅 AI Coach 已停止"
    echo ""
    
    # 显示容器状态
    local running_containers=$(docker compose ps -q 2>/dev/null | wc -l)
    if [ "$running_containers" -gt 0 ]; then
        echo -e "${YELLOW}仍有 $running_containers 个容器在运行${NC}"
        docker compose ps
    else
        echo -e "${GREEN}所有容器已停止${NC}"
    fi
    echo ""
    
    echo -e "启动服务: ${YELLOW}./start.sh${NC}"
    echo ""
}

# 主函数
main() {
    # 默认选项
    local cleanup_volumes_flag=false
    local cleanup_images_flag=false
    local cleanup_all_flag=false
    export FORCE=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--volumes)
                cleanup_volumes_flag=true
                shift
                ;;
            -i|--images)
                cleanup_images_flag=true
                shift
                ;;
            -a|--all)
                cleanup_all_flag=true
                shift
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    print_banner
    
    # 执行清理操作
    if [ "$cleanup_all_flag" = true ]; then
        cleanup_all
    else
        stop_services
        
        if [ "$cleanup_volumes_flag" = true ]; then
            cleanup_volumes
        fi
        
        if [ "$cleanup_images_flag" = true ]; then
            cleanup_images
        fi
    fi
    
    show_status
}

# 执行主函数
main "$@"
