#!/bin/bash

echo "启动 arXiv Paper Tracker..."

# 确保在项目根目录
cd "$(dirname "$0")"

# 启动后端
echo "启动后端服务..."
cd backend
source venv/bin/activate
python -m app.main &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 启动前端
echo "启动前端服务..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ 服务已启动!"
echo ""
echo "前端: http://localhost:5173"
echo "后端: http://localhost:8000"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 等待中断信号
trap "echo '停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM

wait
