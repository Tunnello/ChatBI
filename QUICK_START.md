# ChatBI 快速启动指南

## 前置要求

1. Python 3.12+ (推荐使用 conda 环境)
2. Node.js 18+ 和 npm/yarn
3. 已配置 OPENAI_API_KEY 环境变量

## 快速启动（3 步）

### 1. 安装后端依赖

```bash
# 激活 conda 环境
conda activate nlp

# 安装 Python 依赖
pip install -r requirements.txt
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

### 3. 启动服务

```bash
# 方式一：使用启动脚本（推荐）
./start.sh

# 方式二：分别启动
# 终端 1 - 后端
cd backend && python server.py

# 终端 2 - 前端  
cd frontend && npm run dev
```

## 访问应用

- **前端界面**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 配置说明

### 后端环境变量（`.env` 或系统环境变量）

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
HOST=0.0.0.0
PORT=8000
```

### 前端环境变量（`frontend/.env`）

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 常见问题

### 后端启动失败

1. 检查 Python 环境：`python --version`
2. 检查依赖：`pip list | grep fastapi`
3. 检查端口占用：`lsof -i :8000`

### 前端无法连接后端

1. 确认后端正在运行
2. 检查 `frontend/.env` 中的 `VITE_API_BASE_URL`
3. 查看浏览器控制台错误信息

### 依赖安装失败

```bash
# 后端
pip install --upgrade pip
pip install -r requirements.txt

# 前端
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 下一步

查看 [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) 了解详细的架构说明和 API 文档。

