#!/bin/bash

# 小红书搜索服务启动脚本

# 检查Python环境
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "错误: 未找到Python环境，请安装Python 3.7+"
    exit 1
fi

# 检查Chrome浏览器
if ! command -v google-chrome &>/dev/null && ! command -v "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" &>/dev/null; then
    echo "警告: 未找到Chrome浏览器，Selenium可能无法正常工作"
    echo "请安装Chrome浏览器后再运行此脚本"
    echo "下载地址: https://www.google.com/chrome/"
    read -r -p "是否继续? [y/N] " choice
    if [[ ! "$choice" =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 1
    fi
fi

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "使用虚拟环境..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        echo "警告: 虚拟环境存在但无法激活，使用系统Python"
    fi
else
    echo "未找到虚拟环境，使用系统Python"
fi

# 检查依赖
echo "检查依赖..."
$PYTHON -m pip install -r config/requirements.txt

# 添加webdriver-manager依赖
echo "安装webdriver-manager..."
$PYTHON -m pip install webdriver-manager

# 创建必要的目录
mkdir -p cache/{cookies,temp,logs} static/images

# 检查cookie文件
COOKIE_FILE="cache/cookies/xiaohongshu_cookies.json"
if [ ! -f "$COOKIE_FILE" ]; then
    echo "未找到小红书cookie文件，需要先获取cookie"
    echo "请选择获取cookie的方式:"
    echo "1. 打开浏览器登录小红书 (推荐)"
    echo "2. 手动设置cookie"
    echo "3. 跳过 (搜索功能可能受限)"
    read -r -p "请选择 [1-3]: " choice
    
    case $choice in
        1)
            echo "启动登录流程..."
            $PYTHON src/utils/login_helper.py
            if [ $? -ne 0 ]; then
                echo "登录失败，请手动运行 $PYTHON src/utils/login_helper.py 重试"
                exit 1
            fi
            ;;
        2)
            echo "启动cookie设置工具..."
            $PYTHON src/utils/cookie_manager.py
            if [ $? -ne 0 ]; then
                echo "设置cookie失败，请手动运行 $PYTHON src/utils/cookie_manager.py 重试"
                exit 1
            fi
            ;;
        3)
            echo "跳过登录，搜索功能可能受限"
            ;;
        *)
            echo "无效选择，跳过登录"
            ;;
    esac
else
    echo "已找到cookie文件: $COOKIE_FILE"
fi

# 检查并清理8080端口
echo "检查8080端口是否被占用..."
PORT_PID=$(lsof -ti:8080 2>/dev/null)
if [ ! -z "$PORT_PID" ]; then
    echo "发现8080端口被进程 $PORT_PID 占用，正在停止该进程..."
    kill -9 $PORT_PID 2>/dev/null
    sleep 2
    if lsof -ti:8080 &>/dev/null; then
        echo "警告: 8080端口仍被占用"
        read -r -p "是否继续启动? [y/N] " choice
        if [[ ! "$choice" =~ ^[Yy]$ ]]; then
            echo "已取消启动"
            exit 1
        fi
    else
        echo "端口8080已释放"
    fi
else
    echo "端口8080可用"
fi

# 清理cache文件夹中的临时文件（保留cookie文件）
echo "清理cache文件夹中的临时文件..."
if [ -d "cache/temp" ]; then
    TEMP_FILES_COUNT=$(find cache/temp -type f | wc -l | tr -d ' ')
    if [ "$TEMP_FILES_COUNT" -gt 0 ]; then
        echo "发现 $TEMP_FILES_COUNT 个临时文件，正在清理..."
        rm -f cache/temp/*
        echo "临时文件清理完成"
    else
        echo "cache/temp文件夹中没有需要清理的临时文件"
    fi
    if [ -f "cache/cookies/xiaohongshu_cookies.json" ]; then
        echo "已保留登录凭证文件: xiaohongshu_cookies.json"
    fi
else
    echo "cache/temp文件夹不存在，跳过清理"
fi

# 启动服务
echo "启动小红书搜索服务..."
echo "访问地址: http://localhost:8080"
echo "如需登录，请访问: http://localhost:8080/login"
echo "按 Ctrl+C 停止服务"
$PYTHON src/server/main_server.py 