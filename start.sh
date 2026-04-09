#!/bin/bash

echo "==================================="
echo "  智能售后客服系统 - 启动脚本"
echo "==================================="
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未安装Python3"
    exit 1
fi

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: 未找到.env配置文件"
    echo "请先复制.env.example并配置相关信息:"
    echo "  cp .env.example .env"
    echo "  然后编辑.env文件填入你的配置"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "安装依赖中..."
    pip3 install -r requirements.txt
fi

# 初始化数据库
echo "🗄️  初始化数据库..."
python3 init_data.py

# 启动服务
echo ""
echo "🚀 启动服务..."
echo "访问地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo ""
python3 main.py
