#!/bin/bash
# =============================================================================
# 深寻觅 AI Coach - 启动脚本
# 一键启动所有服务
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
    echo "║           🚀 深寻觅 AI Coach - 启动脚本                      ║"
    echo "║                                                              ║"
    echo "║           基于AI的优势教练对话系统                           ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查Docker和Docker Compose
check_docker() {
    log_info "检查Docker环境..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        echo "安装指南: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        echo "安装指南: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # 检查Docker服务是否运行
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行，请启动Docker服务"
        exit 1
    fi
    
    log_success "Docker环境检查通过"
}

# 检查环境变量
check_env() {
    log_info "检查环境变量配置..."
    
    # 检查.env文件
    if [ -f ".env" ]; then
        log_info "加载环境变量文件..."
        set -a
        source .env
        set +a
    else
        log_warning ".env文件不存在，将使用默认配置"
        log_info "建议复制 .env.example 到 .env 并配置相关参数"
    fi
    
    # 检查关键环境变量
    local missing_vars=()
    
    if [ -z "${JWT_SECRET_KEY:-}" ] || [ "${JWT_SECRET_KEY:-}" = "your-secret-key-change-in-production" ]; then
        log_warning "JWT_SECRET_KEY 未设置或使用默认值，建议设置强密钥"
        export JWT_SECRET_KEY="$(openssl rand -hex 32 2>/dev/null || head -c 64 /dev/urandom | xxd -p | head -1)"
        log_info "已自动生成临时JWT密钥"
    fi
    
    if [ -z "${OPENAI_API_KEY:-}" ]; then
        log_warning "OPENAI_API_KEY 未设置，AI对话功能将无法使用"
    fi
    
    log_success "环境变量检查完成"
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    mkdir -p data logs temp ssl
    
    # 设置目录权限
    chmod 755 data logs temp ssl 2>/dev/null || true
    
    log_success "目录创建完成"
}

# 检查端口占用
check_ports() {
    log_info "检查端口占用..."
    
    local ports=(80 443 8000 6379)
    local port_in_use=false
    
    for port in "${ports[@]}"; do
        if command -v netstat &> /dev/null; then
            if netstat -tuln 2>/dev/null | grep -q ":$port "; then
                log_warning "端口 $port 已被占用"
                port_in_use=true
            fi
        elif command -v ss &> /dev/null; then
            if ss -tuln 2>/dev/null | grep -q ":$port "; then
                log_warning "端口 $port 已被占用"
                port_in_use=true
            fi
        fi
    done
    
    if [ "$port_in_use" = true ]; then
        log_warning "部分端口已被占用，可能会导致服务启动失败"
        read -p "是否继续? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_success "端口检查通过"
    fi
}

# 构建Docker镜像
build_images() {
    log_info "构建Docker镜像..."
    
    if [ "${SKIP_BUILD:-false}" = "true" ]; then
        log_info "跳过镜像构建"
        return
    fi
    
    # 使用docker compose构建
    if docker compose build --parallel; then
        log_success "镜像构建完成"
    else
        log_error "镜像构建失败"
        exit 1
    fi
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 停止旧服务（如果存在）
    docker compose down --remove-orphans 2>/dev/null || true
    
    # 启动服务
    if docker compose up -d; then
        log_success "服务启动命令已执行"
    else
        log_error "服务启动失败"
        exit 1
    fi
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    local max_attempts=30
    local attempt=0
    
    # 等待后端服务
    log_info "等待后端服务..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf http://localhost:8000/health &> /dev/null; then
            log_success "后端服务已就绪"
            break
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "后端服务启动超时"
        show_logs
        exit 1
    fi
    
    # 等待Nginx服务
    log_info "等待Nginx服务..."
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf http://localhost/health &> /dev/null; then
            log_success "Nginx服务已就绪"
            break
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "Nginx服务启动超时"
        show_logs
        exit 1
    fi
}

# 显示服务状态
show_status() {
    echo ""
    log_success "🎉 深寻觅 AI Coach 启动成功！"
    echo ""
    echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${BLUE}📱 前端访问地址:${NC}    http://localhost"
    echo -e "  ${BLUE}🔌 API访问地址:${NC}    http://localhost/api"
    echo -e "  ${BLUE}📚 API文档地址:${NC}    http://localhost:8000/docs"
    echo -e "  ${BLUE}🔍 健康检查:${NC}       http://localhost/health"
    echo ""
    echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # 显示容器状态
    echo -e "${BLUE}容器状态:${NC}"
    docker compose ps
    echo ""
}

# 显示日志
show_logs() {
    echo ""
    log_info "服务日志:"
    docker compose logs --tail=50
}

# 显示使用帮助
show_help() {
    echo "深寻觅 AI Coach 启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help       显示帮助信息"
    echo "  -b, --build      强制重新构建镜像"
    echo "  -s, --skip-build 跳过镜像构建"
    echo "  -l, --logs       启动后显示日志"
    echo "  -d, --daemon     后台模式启动（默认）"
    echo ""
}

# 主函数
main() {
    # 解析参数
    local show_log=false
    local skip_build=false
    local force_build=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -b|--build)
                force_build=true
                shift
                ;;
            -s|--skip-build)
                skip_build=true
                shift
                ;;
            -l|--logs)
                show_log=true
                shift
                ;;
            -d|--daemon)
                shift
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 设置环境变量
    if [ "$skip_build" = true ]; then
        export SKIP_BUILD=true
    fi
    
    # 执行启动流程
    print_banner
    check_docker
    check_env
    create_directories
    check_ports
    build_images
    start_services
    wait_for_services
    show_status
    
    # 显示日志
    if [ "$show_log" = true ]; then
        show_logs
    else
        echo -e "查看日志: ${YELLOW}docker compose logs -f${NC}"
        echo -e "停止服务: ${YELLOW}./stop.sh${NC}"
    fi
}

# 执行主函数
main "$@"
