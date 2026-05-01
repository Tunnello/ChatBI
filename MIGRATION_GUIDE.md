# ChatBI 框架迁移指南

本文档说明如何从 Streamlit 框架迁移到 React 前端 + FastAPI 后端架构。

## 架构变化

### 之前（Streamlit）
- 单一 Streamlit 应用
- 前端和后端耦合在一起
- 使用 `main.py` 作为入口

### 现在（React + FastAPI）
- **前端**: React + TypeScript + Vite + Ant Design
- **后端**: FastAPI + Python
- 前后端分离，通过 REST API 和 SSE 通信

## 项目结构

```
ChatBI/
├── backend/              # FastAPI 后端
│   ├── api/             # API 路由
│   │   ├── chat.py      # 聊天 API
│   │   └── callback.py  # 回调处理器
│   └── server.py        # 服务器入口
├── frontend/            # React 前端
│   ├── src/
│   │   ├── components/  # React 组件
│   │   ├── services/    # API 服务
│   │   └── utils/       # 工具函数
│   └── package.json
├── agent.py             # Agent 核心逻辑（保持不变）
├── tools/               # 工具模块（保持不变）
└── start.sh             # 启动脚本
```

## 安装和运行

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
# 或使用 yarn
yarn install
```

### 3. 配置环境变量

**后端**（`.env` 文件）:
```env
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
HOST=0.0.0.0
PORT=8000
```

**前端**（`frontend/.env`）:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### 4. 启动服务

#### 方式一：使用启动脚本（推荐）

```bash
./start.sh
```

#### 方式二：手动启动

**终端 1 - 启动后端**:
```bash
cd backend
python server.py
```

**终端 2 - 启动前端**:
```bash
cd frontend
npm run dev
```

### 5. 访问应用

- **前端界面**: http://localhost:5173 (Vite 默认端口)
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs (Swagger UI)

## API 接口

### 聊天查询（SSE 流式输出）

**POST** `/api/chat/query`

**请求体**:
```json
{
  "query": "查询所有产品类别",
  "session_id": "optional_session_id",
  "request_id": "optional_request_id",
  "model": "qwen-plus"
}
```

**响应**: SSE 流式输出
```
event: message
data: {"type": "start", "message": "已接收到你的任务...", "finished": false}

event: message
data: {"type": "response", "message": "查询结果...", "finished": true}
```

### 健康检查

**GET** `/api/chat/health`

**响应**:
```json
{
  "status": "ok",
  "service": "ChatBI API"
}
```

## 主要修改内容

### 后端修改

1. **创建 FastAPI 服务器** (`backend/server.py`)
   - 支持 CORS
   - 注册 API 路由
   - 配置日志

2. **聊天 API** (`backend/api/chat.py`)
   - SSE 流式输出
   - 集成现有 Agent 逻辑
   - 错误处理

3. **回调处理器** (`backend/api/callback.py`)
   - 流式输出处理
   - 消息缓冲

### 前端修改

1. **API 服务** (`frontend/src/services/`)
   - 更新 API 基础 URL
   - 适配新的后端接口

2. **SSE 工具** (`frontend/src/utils/querySSE.ts`)
   - 更新 API 端点
   - 适配后端响应格式

3. **聊天组件** (`frontend/src/components/ChatView/`)
   - 修改消息处理逻辑
   - 适配后端响应格式

## 功能对比

| 功能 | Streamlit 版本 | React 版本 |
|------|---------------|-----------|
| 聊天界面 | ✅ | ✅ |
| 流式输出 | ✅ | ✅ |
| 图表展示 | ✅ | ✅ |
| 工具调用日志 | ✅ | ✅ |
| 模型选择 | ✅ | ✅ |
| 响应式设计 | ⚠️ | ✅ |
| 现代化 UI | ⚠️ | ✅ |

## 常见问题

### Q: 后端启动失败？

**A**: 检查：
1. Python 环境是否正确激活
2. 依赖是否完整安装
3. 端口 8000 是否被占用
4. 环境变量是否正确配置

### Q: 前端无法连接后端？

**A**: 检查：
1. 后端是否正在运行
2. `VITE_API_BASE_URL` 是否正确
3. 浏览器控制台是否有 CORS 错误

### Q: SSE 连接失败？

**A**: 检查：
1. `sse-starlette` 是否已安装
2. 后端日志是否有错误
3. 网络连接是否正常

## 开发建议

1. **后端开发**: 使用 `uvicorn` 的 `reload` 模式进行热重载
2. **前端开发**: Vite 默认支持热重载
3. **调试**: 使用浏览器开发者工具和 Python 日志

## 部署

### 生产环境

1. **后端**: 使用 `gunicorn` 或 `uvicorn` 配合反向代理（Nginx）
2. **前端**: 构建静态文件，使用 Nginx 提供服务

```bash
# 构建前端
cd frontend
npm run build

# 生产环境启动后端
cd backend
uvicorn backend.server:app --host 0.0.0.0 --port 8000 --workers 4
```

## 回退到 Streamlit

如果需要回退到 Streamlit 版本：

```bash
# 直接运行原来的 main.py
streamlit run main.py
```

所有原有的功能都保持不变，只是前端界面不同。

## 更新日期

最后更新：2024-11-09

