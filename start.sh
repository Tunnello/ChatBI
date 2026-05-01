#!/bin/bash

# ChatBI 启动脚本
# 同时启动后端和前端

echo "🚀 启动 ChatBI..."

# # 初始化 conda（如果需要）
# CONDA_BASE=$(conda info --base 2>/dev/null)
# if [ -n "$CONDA_BASE" ] && [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
#     source "$CONDA_BASE/etc/profile.d/conda.sh"
# fi

# # 激活 conda 环境
# if command -v conda &> /dev/null; then
#     conda activate nlp 2>/dev/null || {
#         echo "⚠️  无法激活 nlp 环境"
#         echo "💡 请先运行: conda activate nlp"
#         echo "💡 或使用: source <conda_base>/etc/profile.d/conda.sh && conda activate nlp"
#     }
# fi

# 检查环境变量
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  警告: OPENAI_API_KEY 环境变量未设置"
fi

# 启动后端
echo "📦 启动后端服务器..."
cd backend

# 确定 Python 路径
if [ -n "$CONDA_DEFAULT_ENV" ] && [ "$CONDA_DEFAULT_ENV" = "nlp" ]; then
    PYTHON_CMD="python"
    echo "✅ 使用 conda 环境: $CONDA_DEFAULT_ENV"
elif [ -f "/opt/homebrew/anaconda3/envs/nlp/bin/python" ]; then
    PYTHON_CMD="/opt/homebrew/anaconda3/envs/nlp/bin/python"
    echo "✅ 使用 nlp 环境的 Python: $PYTHON_CMD"
else
    PYTHON_CMD="python3"
    echo "⚠️  使用系统 Python，请确保已安装依赖"
fi

$PYTHON_CMD server.py &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 启动前端
echo "🎨 启动前端..."
cd frontend
npm install 2>/dev/null || echo "依赖已安装"
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ ChatBI 已启动!"
echo "📡 后端 API: http://localhost:8000"
echo "🌐 前端界面: http://localhost:5173 (或查看终端输出)"
echo ""
echo "按 Ctrl+C 停止服务"

# 等待用户中断
wait

