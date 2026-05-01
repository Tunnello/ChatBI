# ChatBI API 接口文档

本文档详细说明 ChatBI 项目的 API 接口定义和交互方式。

**当前架构**：FastAPI 后端 + React 前端（推荐使用）

> **注意**：项目已从 Streamlit 迁移到 React + FastAPI 架构。Streamlit 相关代码仍保留在项目中，但不再作为主要使用方式。如需使用 Streamlit 版本，请参考文档末尾的[传统架构说明](#传统架构streamlit-已弃用)。

## 目录

- [架构概览](#架构概览)
- [FastAPI 后端接口](#fastapi-后端接口)
- [前端调用方式](#前端调用方式)
- [数据格式](#数据格式)
- [错误处理](#错误处理)
- [工具接口](#工具接口)
- [传统架构（Streamlit，已弃用）](#传统架构streamlit-已弃用)

---

## 架构概览

### 当前架构：FastAPI + React

```
┌─────────────────┐
│  React Frontend │  ← 前端界面 (React + TypeScript + Ant Design)
│  (Port 5173)    │    使用 Vite 构建，支持热重载
└────────┬────────┘
         │ HTTP/SSE
         ↓
┌─────────────────┐
│  FastAPI Server │  ← 后端 API (Python + FastAPI)
│  (Port 8000)    │    提供 REST API 和 SSE 流式输出
└────────┬────────┘
         │
         ├─→ agent.py      ← Agent 核心逻辑
         ├─→ tools/        ← 工具模块（RAG、SQL、图表等）
         └─→ LangGraph     ← Agent 编排框架
```

**技术栈**：
- **前端**：React 19 + TypeScript + Vite + Ant Design + ECharts
- **后端**：FastAPI + Python 3.12+ + LangGraph + LangChain
- **通信**：REST API + SSE (Server-Sent Events)

---

## FastAPI 后端接口

### 基础信息

- **Base URL**: `http://localhost:8000`
- **API Prefix**: `/api`
- **文档地址**: `http://localhost:8000/docs` (Swagger UI)
- **ReDoc 地址**: `http://localhost:8000/redoc`

### 1. 聊天查询接口（SSE 流式输出）

**接口**: `POST /api/chat/query`

**描述**: 发送用户查询，通过 SSE (Server-Sent Events) 流式返回 AI 响应。

**请求头**:
```http
Content-Type: application/json
```

**请求体**:
```json
{
  "query": "查询所有产品类别，每个类别有多少产品",
  "session_id": "optional_session_id",
  "request_id": "optional_request_id",
  "model": "qwen-plus"
}
```

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | string | 是 | - | 用户查询内容 |
| `session_id` | string | 否 | "default" | 会话 ID，用于保持上下文 |
| `request_id` | string | 否 | UUID | 请求 ID，用于追踪 |
| `model` | string | 否 | "qwen-plus" | 模型名称，可选：`qwen-plus`, `qwen-turbo`, `qwen3-max-preview` |

**响应格式**: SSE 流式输出

**SSE 事件格式**:
```
event: message
data: {"type": "start", "request_id": "...", "session_id": "...", "message": "已接收到你的任务...", "finished": false}

event: message
data: {"type": "response", "request_id": "...", "session_id": "...", "message": "查询结果...", "finished": false}

event: message
data: {"type": "response", "request_id": "...", "session_id": "...", "message": "最终完整响应...", "finished": true}
```

**响应数据格式**:
```json
{
  "type": "start" | "response" | "error",
  "request_id": "string",
  "session_id": "string",
  "message": "string",
  "finished": boolean
}
```

**字段说明**:

- `type`: 消息类型
  - `start`: 开始处理
  - `response`: 响应内容（可能多次）
  - `error`: 错误信息
- `request_id`: 请求 ID
- `session_id`: 会话 ID
- `message`: 消息内容（支持 Markdown 和 JSON 代码块）
- `finished`: 是否完成（`true` 表示最终消息）

**示例**:

```bash
# 使用 curl 测试
curl -N -X POST http://localhost:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "查询所有产品类别",
    "model": "qwen-plus"
  }'
```

**前端调用示例** (TypeScript):

```typescript
import querySSE from '@/utils/querySSE';

querySSE({
  body: {
    query: "查询所有产品类别",
    session_id: "user_123",
    model: "qwen-plus"
  },
  handleMessage: (data) => {
    console.log('收到消息:', data.message);
    // 更新 UI
  },
  handleError: (error) => {
    console.error('错误:', error);
  },
  handleClose: () => {
    console.log('连接关闭');
  }
});
```

---

### 2. 健康检查接口

**接口**: `GET /api/chat/health`

**描述**: 检查服务健康状态。

**请求**: 无参数

**响应**:
```json
{
  "status": "ok",
  "service": "ChatBI API"
}
```

**示例**:
```bash
curl http://localhost:8000/api/chat/health
```

---

### 3. 获取模型列表接口

**接口**: `GET /api/chat/models`

**描述**: 获取所有可用的 AI 模型列表。

**请求**: 无参数

**响应**:
```json
[
  {
    "modelName": "qwen-plus",
    "modelCode": "qwen-plus",
    "schemaList": []
  },
  {
    "modelName": "qwen-turbo",
    "modelCode": "qwen-turbo",
    "schemaList": []
  },
  {
    "modelName": "qwen3-max-preview",
    "modelCode": "qwen3-max-preview",
    "schemaList": []
  }
]
```

**字段说明**:

- `modelName`: 模型显示名称
- `modelCode`: 模型代码（用于 API 调用）
- `schemaList`: 数据库 Schema 列表（暂未实现）

**示例**:
```bash
curl http://localhost:8000/api/chat/models
```

---

## 前端调用方式

### React 前端实现

前端使用 TypeScript + React，通过 SSE 与后端通信。

**主要文件**：
- `frontend/src/services/agent.ts` - API 服务封装
- `frontend/src/utils/querySSE.ts` - SSE 工具函数
- `frontend/src/components/ChatView/` - 聊天界面组件

**API 服务封装** (`frontend/src/services/agent.ts`):
```typescript
import api from "./index";

export const agentApi = {
  chatQuery: (data: { 
    query: string; 
    session_id?: string; 
    request_id?: string; 
    model?: string 
  }) => api.post(`/api/chat/query`, data),
  
  healthCheck: () => api.get(`/api/chat/health`),
  
  allModels: () => api.get(`/api/chat/models`),
};
```

**SSE 调用示例** (`frontend/src/utils/querySSE.ts`):
```typescript
import querySSE from '@/utils/querySSE';

querySSE({
  body: {
    query: "查询所有产品类别",
    session_id: "user_123",
    model: "qwen-plus"
  },
  handleMessage: (data) => {
    // 处理接收到的消息
    console.log('收到消息:', data.message);
    // 更新 UI 状态
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: data.message
    }]);
    
    if (data.finished) {
      // 处理完成
      setIsLoading(false);
    }
  },
  handleError: (error) => {
    console.error('错误:', error);
    setIsLoading(false);
  },
  handleClose: () => {
    console.log('连接关闭');
    setIsLoading(false);
  }
});
```

**环境变量配置** (`frontend/.env`):
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 传统架构（Streamlit，已弃用）

> **注意**：以下内容为传统 Streamlit 架构的接口说明，当前项目主要使用 React + FastAPI 架构。Streamlit 代码仍保留在项目中，但不再推荐使用。

### Streamlit 架构接口

### 核心接口

#### 1. Agent 创建接口

**位置**: `agent.py`

**函数签名**:
```python
def create_agent(
    callback_handler: BaseCallbackHandler, 
    model_name: str
) -> StateGraph
```

**参数**:
- `callback_handler` (BaseCallbackHandler): 回调处理器，用于处理流式输出
- `model_name` (str): 模型名称，可选值：
  - `"qwen-plus"`
  - `"qwen-turbo"`
  - `"qwen3-max-preview"`

**返回值**:
- `StateGraph`: LangGraph 状态图对象

**调用位置**: `main.py:235`
```python
react_graph = create_agent(callback_handler, st.session_state["model"])
```

---

#### 2. Agent 执行接口

**位置**: `main.py`

**函数调用**:
```python
result = react_graph.invoke(state, config=config, debug=True)
```

**参数**:
- `state` (MessagesState): 消息状态对象
  ```python
  state = MessagesState(messages=[HumanMessage(content=user_input_content)])
  ```
- `config` (dict): 配置字典
  ```python
  config = {"configurable": {"thread_id": "42"}}
  ```
- `debug` (bool): 是否开启调试模式

**返回值**:
```python
{
    "messages": [AIMessage, ToolMessage, ...]  # 消息列表
}
```

---

#### 3. 消息状态接口

**位置**: `agent.py`

**数据结构**:
```python
@dataclass
class MessagesState:
    messages: Annotated[Sequence[BaseMessage], add_messages]
```

**消息类型**:
- `HumanMessage`: 用户输入消息
- `AIMessage`: AI 回复消息
- `ToolMessage`: 工具调用结果消息

---

#### 4. 回调接口

**位置**: `ui/sqlitechat_ui.py`

**类定义**:
```python
class StreamlitUICallbackHandler(BaseCallbackHandler):
    def __init__(self, model: str)
    def start_loading_message(self)
    def on_llm_new_token(self, token, run_id, parent_run_id=None, **kwargs)
    def on_llm_end(self, response, run_id, parent_run_id=None, **kwargs)
    def display_dataframe(self, df)
```

**主要方法**:

1. **`start_loading_message()`**: 显示加载提示
2. **`on_llm_new_token(token, ...)`**: 流式输出处理，实时更新 UI
3. **`on_llm_end(...)`**: LLM 输出结束时的清理工作
4. **`display_dataframe(df)`**: 显示数据框

---

## 数据格式

### 请求格式

#### FastAPI 请求

```json
{
  "query": "查询所有产品类别",
  "session_id": "user_123",
  "request_id": "req_456",
  "model": "qwen-plus"
}
```

#### Streamlit 消息格式

```python
{
    "role": "user",
    "content": "查询所有产品类别"
}
```

---

### 响应格式

#### FastAPI SSE 响应

**开始消息**:
```json
{
  "type": "start",
  "request_id": "req_456",
  "session_id": "user_123",
  "message": "已接收到你的任务，将立即开始处理...",
  "finished": false
}
```

**流式响应**:
```json
{
  "type": "response",
  "request_id": "req_456",
  "session_id": "user_123",
  "message": "根据查询结果...",
  "finished": false
}
```

**最终响应**:
```json
{
  "type": "response",
  "request_id": "req_456",
  "session_id": "user_123",
  "message": "完整的响应内容，可能包含图表 JSON 配置...",
  "finished": true
}
```

**错误响应**:
```json
{
  "type": "error",
  "request_id": "req_456",
  "session_id": "user_123",
  "message": "处理请求时出错: 错误信息",
  "finished": true
}
```

#### Streamlit 消息格式

```python
{
    "role": "assistant",
    "content": "根据查询结果，共有以下产品类别：..."
}
```

---

### 图表配置格式

当用户请求生成图表时，响应消息中会包含 Highcharts JSON 配置：

```markdown
根据查询结果，我为您生成了以下图表：

```json
{
  "chart": {
    "type": "column"
  },
  "title": {
    "text": "产品类别统计"
  },
  "xAxis": {
    "categories": ["类别1", "类别2", "类别3"]
  },
  "yAxis": {
    "title": {
      "text": "数量"
    }
  },
  "series": [{
    "name": "产品数量",
    "data": [10, 20, 15]
  }]
}
```
```

前端会自动识别并渲染图表。

---

## 错误处理

### FastAPI 错误响应

**HTTP 状态码**:
- `200`: 成功（SSE 流式输出）
- `400`: 请求参数错误
- `500`: 服务器内部错误

**错误响应格式**:
```json
{
  "detail": "错误信息"
}
```

### Streamlit 错误处理

**API Key 验证** (`agent.py:133-143`):
```python
if not config.api_key:
    raise ValueError(
        f"API key for model '{model_name}' is not set. "
        f"Please set the OPENAI_API_KEY environment variable."
    )
```

**输入验证** (`main.py:212-213`):
```python
if len(prompt) > 500:
    st.error("Input is too long! Please limit your message to 500 characters.")
```

---

## 工具接口

### 可用工具列表

**位置**: `agent.py:75`

```python
tools = [
    retriever_tool,        # 数据库 Schema RAG 检索
    search,                # DuckDuckGo 搜索
    text2sqlite_tool,      # 自然语言转 SQL
    highcharts_tool,       # 生成 Highcharts 图表配置
    execute_sqlite_query,  # 执行 SQLite 查询
] + mcp_tools             # MCP 工具（如时间工具）
```

### 工具调用流程

```
1. LLM 决定调用工具
   ↓
2. 工具调用路由 (tools_condition)
   ↓
3. 执行工具 (ToolNode)
   ↓
4. 返回工具结果
   ↓
5. 继续处理或结束
```

### 工具消息格式

**ToolMessage**:
```python
ToolMessage(
    name="execute_sqlite_query",
    content='{"results": [...]}',
    tool_call_id="call_123"
)
```

**属性**:
- `name`: 工具名称
- `content`: 工具返回内容（JSON 字符串）
- `tool_call_id`: 工具调用 ID

---

## 状态管理

### FastAPI 会话管理

使用 `session_id` 参数保持会话上下文：

```python
config = {
    "configurable": {"thread_id": session_id},
    "recursion_limit": 50
}
```

### Streamlit Session State

**主要状态变量**:

1. **`st.session_state["messages"]`**
   - 类型: `List[Dict[str, str]]`
   - 格式: `[{"role": "user|assistant", "content": "..."}]`

2. **`st.session_state["model"]`**
   - 类型: `str`
   - 可选值: `"qwen-plus"`, `"qwen-turbo"`, `"qwen3-max-preview"`

3. **`st.session_state["tool_events"]`**
   - 类型: `List[ToolMessage]`
   - 用途: 存储工具调用日志

---

## 配置接口

### 模型配置

**位置**: `agent.py:get_model_configurations()`

**返回配置**:
```python
{
    "qwen-plus": ModelConfig(
        model_name="qwen-plus",
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE_URL", 
                          "https://dashscope.aliyuncs.com/compatible-mode/v1")
    ),
    # ... 其他模型
}
```

### 环境变量

**必需**:
- `OPENAI_API_KEY`: 阿里百炼 API Key

**可选**:
- `OPENAI_API_BASE_URL`: API 基础 URL（默认: `https://dashscope.aliyuncs.com/compatible-mode/v1`）
- `HOST`: 服务器主机（默认: `0.0.0.0`）
- `PORT`: 服务器端口（默认: `8000`）
- `ENV`: 环境模式（`local` 启用热重载）

---

## 关键文件映射

| 文件 | 主要接口/功能 |
|------|-------------|
| `backend/server.py` | FastAPI 服务器入口 |
| `backend/api/chat.py` | 聊天 API 路由 |
| `backend/api/callback.py` | 流式输出回调处理器 |
| `agent.py` | Agent 核心，创建和执行 Agent |
| `frontend/src/services/agent.ts` | React 前端 API 服务 |
| `frontend/src/utils/querySSE.ts` | React 前端 SSE 工具 |
| `main.py` | Streamlit 前端入口（已弃用） |
| `ui/sqlitechat_ui.py` | Streamlit UI 组件（已弃用） |
| `tools/tools_rag.py` | RAG 工具 |
| `tools/tools_text2sqlite.py` | 文本转 SQL 工具 |
| `tools/tools_execute_sqlite.py` | SQL 执行工具 |
| `tools/tools_charts.py` | 图表生成工具 |

---

## 使用示例

### React 前端调用示例

**在 React 组件中使用**:
```typescript
import { useState } from 'react';
import querySSE from '@/utils/querySSE';

function ChatComponent() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = (query: string) => {
    setIsLoading(true);
    
    querySSE({
      body: {
        query: query,
        session_id: 'user_123',
        model: 'qwen-plus'
      },
      handleMessage: (data) => {
        if (data.type === 'start') {
          // 开始处理
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: data.message
          }]);
        } else if (data.type === 'response') {
          // 更新最后一条消息
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1] = {
              role: 'assistant',
              content: data.message
            };
            return newMessages;
          });
          
          if (data.finished) {
            setIsLoading(false);
          }
        } else if (data.type === 'error') {
          // 错误处理
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: `错误: ${data.message}`
          }]);
          setIsLoading(false);
        }
      },
      handleError: (error) => {
        console.error('SSE 错误:', error);
        setIsLoading(false);
      },
      handleClose: () => {
        setIsLoading(false);
      }
    });
  };

  return (
    // ... UI 组件
  );
}
```

### FastAPI 后端示例（直接调用）

**Python 客户端**:
```python
import requests
import json

# 发送查询
response = requests.post(
    'http://localhost:8000/api/chat/query',
    json={
        'query': '查询所有产品类别',
        'model': 'qwen-plus',
        'session_id': 'user_123'
    },
    stream=True
)

# 处理 SSE 流
for line in response.iter_lines():
    if line:
        if line.startswith(b'data: '):
            data = json.loads(line[6:])
            print(data['message'])
            if data['finished']:
                break
```

**JavaScript 客户端**:
```javascript
const eventSource = new EventSource('http://localhost:8000/api/chat/query', {
  method: 'POST',
  body: JSON.stringify({
    query: '查询所有产品类别',
    model: 'qwen-plus'
  })
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.message);
  if (data.finished) {
    eventSource.close();
  }
};
```

### Streamlit 使用示例

如需使用 Streamlit 版本，运行：

```bash
streamlit run main.py
```

**代码示例**:
```python
# main.py
from agent import create_agent
from ui.sqlitechat_ui import StreamlitUICallbackHandler

# 创建回调处理器
callback_handler = StreamlitUICallbackHandler(model)

# 创建 Agent
react_graph = create_agent(callback_handler, model)

# 执行查询
messages = [HumanMessage(content="查询所有产品类别")]
state = MessagesState(messages=messages)
config = {"configurable": {"thread_id": "42"}}

result = react_graph.invoke(state, config=config)
```

> **提示**：建议使用新的 React + FastAPI 架构，功能更强大，体验更好。

---

## 更新日期

最后更新：2024-11-09

---

## 相关文档

- [README.md](README.md) - 项目总体说明
- [QUICK_START.md](QUICK_START.md) - 快速启动指南
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 架构迁移指南
- [ENV_CONFIG.md](ENV_CONFIG.md) - 环境配置说明
