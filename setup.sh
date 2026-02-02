#!/bin/bash

echo "================================"
echo "arXiv Paper Tracker 快速启动脚本"
echo "================================"
echo ""

# 检查是否在项目根目录
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 1. 后端设置
echo "📦 步骤 1: 设置后端..."
cd backend

if [ ! -d "venv" ]; then
    echo "   创建 Python 虚拟环境..."
    python3 -m venv venv
fi

echo "   激活虚拟环境并安装依赖..."
source venv/bin/activate
pip install -r requirements.txt

if [ ! -f ".env" ]; then
    echo "   创建 .env 文件..."
    cp .env.example .env
    echo ""
    echo "⚠️  请编辑 backend/.env 文件，填入你的 API Key!"
    echo "   然后重新运行此脚本"
    exit 1
fi

cd ..

# 2. 前端设置
echo ""
echo "📦 步骤 2: 设置前端..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "   安装 npm 依赖..."
    npm install
fi

cd ..

# 3. 初始化数据库
echo ""
echo "📦 步骤 3: 初始化数据库..."
mkdir -p data logs

# 4. 启动说明
echo ""
echo "✅ 设置完成!"
echo ""
echo "================================"
echo "启动方式："
echo "================================"
echo ""
echo "方式 1 - 分别启动（推荐用于开发）:"
echo ""
echo "  终端 1 - 启动后端:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python -m app.main"
echo ""
echo "  终端 2 - 启动前端:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "方式 2 - 后台运行:"
echo "  ./run.sh"
echo ""
echo "================================"
echo "访问地址："
echo "================================"
echo ""
echo "  前端: http://localhost:5173"
echo "  后端: http://localhost:8000"
echo "  API 文档: http://localhost:8000/docs"
echo ""
