#!/bin/bash

# 🚀 小红书搜索工具 - 开发模式启动脚本
# 使用Nodemon实现自动重载功能

echo "🚀 启动小红书搜索工具开发服务器..."
echo "📁 当前目录: $(pwd)"
echo "🔍 监控文件: src/, static/, *.py"
echo "⚡ 自动重载: 1.5秒延迟"
echo "🌐 访问地址: http://localhost:8080"
echo "=" * 50

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行: python -m venv venv"
    exit 1
fi

# 检查nodemon
if ! command -v nodemon &> /dev/null; then
    echo "❌ Nodemon未安装，请先运行: npm install -g nodemon"
    exit 1
fi

echo "✅ 环境检查完成"
echo "🔄 启动Nodemon监控..."
echo ""

# 启动nodemon
nodemon 