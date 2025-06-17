#!/bin/bash

# 🚀 小红书搜索工具一键部署脚本
# 支持多种部署方式：本地、Docker、Docker Compose

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 未安装"
        return 1
    fi
    return 0
}

# 主函数
main() {
    echo "🚀 小红书搜索工具一键部署脚本"
    echo "=================================="
    
    # 显示部署选项
    echo ""
    echo "请选择部署方式："
    echo "1) 本地部署 (需要Python 3.9+)"
    echo "2) Docker部署 (推荐)"
    echo "3) Docker Compose部署"
    echo "4) 仅下载源码"
    echo ""
    
    read -p "请输入选择 (1-4): " choice
    
    case $choice in
        1)
            deploy_local
            ;;
        2)
            deploy_docker
            ;;
        3)
            deploy_docker_compose
            ;;
        4)
            download_source
            ;;
        *)
            log_error "无效选择"
            exit 1
            ;;
    esac
}

# 本地部署
deploy_local() {
    log_info "开始本地部署..."
    
    # 检查Python
    if ! check_command python3; then
        log_error "请先安装Python 3.9+"
        exit 1
    fi
    
    # 检查pip
    if ! check_command pip3; then
        log_error "请先安装pip3"
        exit 1
    fi
    
    # 下载源码
    download_source
    
    # 进入目录
    cd xiaohongshu-search
    
    # 安装依赖
    log_info "安装Python依赖..."
    pip3 install -r requirements.txt
    
    # 启动服务
    log_success "安装完成！"
    log_info "启动服务..."
    python3 app.py
}

# Docker部署
deploy_docker() {
    log_info "开始Docker部署..."
    
    # 检查Docker
    if ! check_command docker; then
        log_error "请先安装Docker"
        exit 1
    fi
    
    # 拉取镜像
    log_info "拉取Docker镜像..."
    docker pull derekzhou1979/xiaohongshu-search:latest
    
    # 创建数据目录
    mkdir -p ./xiaohongshu-cache
    
    # 运行容器
    log_info "启动容器..."
    docker run -d \
        --name xiaohongshu-search \
        -p 8080:8080 \
        -v $(pwd)/xiaohongshu-cache:/app/cache \
        --restart unless-stopped \
        derekzhou1979/xiaohongshu-search:latest
    
    log_success "Docker部署完成！"
    log_info "访问地址: http://localhost:8080"
    log_info "查看日志: docker logs xiaohongshu-search"
}

# Docker Compose部署
deploy_docker_compose() {
    log_info "开始Docker Compose部署..."
    
    # 检查Docker Compose
    if ! check_command docker-compose && ! check_command docker; then
        log_error "请先安装Docker和Docker Compose"
        exit 1
    fi
    
    # 下载源码
    download_source
    
    # 进入目录
    cd xiaohongshu-search
    
    # 创建docker-compose.yml
    if [ ! -f docker-compose.yml ]; then
        log_info "创建docker-compose.yml..."
        cat > docker-compose.yml << EOF
version: '3.8'
services:
  xiaohongshu-search:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./cache:/app/cache
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/"]
      interval: 30s
      timeout: 10s
      retries: 3
EOF
    fi
    
    # 启动服务
    log_info "构建并启动服务..."
    docker-compose up -d --build
    
    log_success "Docker Compose部署完成！"
    log_info "访问地址: http://localhost:8080"
    log_info "查看日志: docker-compose logs -f"
}

# 下载源码
download_source() {
    log_info "下载源码..."
    
    if [ -d "xiaohongshu-search" ]; then
        log_warning "目录已存在，正在更新..."
        cd xiaohongshu-search
        git pull
        cd ..
    else
        git clone https://github.com/DerekZhou1979/xiaohongshu-search.git
    fi
    
    log_success "源码下载完成！"
}

# 清理函数
cleanup() {
    log_info "清理临时文件..."
    # 这里可以添加清理逻辑
}

# 信号处理
trap cleanup EXIT

# 检查操作系统
if [[ "$OSTYPE" == "darwin"* ]]; then
    log_info "检测到macOS系统"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    log_info "检测到Linux系统"
else
    log_warning "未知操作系统，可能需要手动调整"
fi

# 运行主函数
main "$@" 