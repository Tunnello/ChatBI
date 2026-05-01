# 环境变量配置说明

本文档详细说明 ChatBI 项目的环境变量配置方法。

## 目录

- [后端环境变量](#后端环境变量)
- [前端环境变量](#前端环境变量)
- [配置方式](#配置方式)
- [获取 API Key](#获取-api-key)
- [常见问题](#常见问题)

---

## 后端环境变量

### 配置文件位置

在**项目根目录**创建 `.env` 文件。

### 必需配置

```env
# 阿里百炼 API 配置（必需）
OPENAI_API_KEY=your_qwen_api_key_here
```

### 可选配置

```env
# API 基础 URL（可选，默认值如下）
OPENAI_API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 服务器配置（可选）
HOST=0.0.0.0          # 服务器监听地址，默认 0.0.0.0
PORT=8000             # 服务器端口，默认 8000

# 环境模式（可选）
ENV=local             # 环境模式：local（开发，启用热重载）或 production（生产）

# 日志配置（可选）
LOG_PATH=logs/server.log  # 日志文件路径，默认 logs/server.log
```

### 完整配置示例

```env
# 阿里百炼 API 配置
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# API 基础 URL
OPENAI_API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 环境模式
ENV=local

# 日志配置
LOG_PATH=logs/server.log
```

---

## 前端环境变量

### 配置文件位置

在 `frontend/` 目录下创建 `.env` 文件。

### 必需配置

```env
# 后端 API 基础 URL（必需）
VITE_API_BASE_URL=http://localhost:8000
```

### 完整配置示例

```env
# 后端 API 基础 URL
VITE_API_BASE_URL=http://localhost:8000
```

### 生产环境配置

如果部署到生产环境，修改为实际的后端地址：

```env
# 生产环境示例
VITE_API_BASE_URL=https://api.yourdomain.com
```

---

## 配置方式

### 方式一：使用 .env 文件（推荐）

#### 后端配置

1. 在项目根目录创建 `.env` 文件：
   ```bash
   touch .env
   ```

2. 编辑 `.env` 文件，添加配置：
   ```env
   OPENAI_API_KEY=your_api_key_here
   OPENAI_API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
   ```

#### 前端配置

1. 在 `frontend/` 目录创建 `.env` 文件：
   ```bash
   cd frontend
   touch .env
   ```

2. 编辑 `.env` 文件，添加配置：
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```

### 方式二：系统环境变量

#### macOS/Linux

在 `~/.zshrc` 或 `~/.bashrc` 中添加：

```bash
# 后端环境变量
export OPENAI_API_KEY="your_qwen_api_key_here"
export OPENAI_API_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export HOST="0.0.0.0"
export PORT="8000"
export ENV="local"
```

使配置生效：
```bash
source ~/.zshrc  # 或 source ~/.bashrc
```

#### Windows

在系统环境变量中设置，或使用 PowerShell：

```powershell
$env:OPENAI_API_KEY="your_qwen_api_key_here"
$env:OPENAI_API_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
```

### 优先级说明

环境变量的优先级（从高到低）：
1. 系统环境变量
2. `.env` 文件中的配置

后端代码使用 `load_dotenv(override=False)`，确保系统环境变量优先。

---

## 获取 API Key

### 阿里云百炼平台

1. 访问 [阿里云百炼平台](https://dashscope.aliyuncs.com/)
2. 注册/登录账号
3. 进入控制台，创建 API Key
4. 复制 API Key 到 `.env` 文件

### 其他兼容 OpenAI API 的服务

如果使用其他兼容 OpenAI API 的服务（如 OpenAI、Azure OpenAI 等），只需修改 `OPENAI_API_BASE_URL`：

```env
# OpenAI
OPENAI_API_BASE_URL=https://api.openai.com/v1

# Azure OpenAI
OPENAI_API_BASE_URL=https://your-resource.openai.azure.com
```

---

## 常见问题

### Q1: 环境变量设置了但代码读取不到？

**A**: 检查以下几点：

1. **确认文件位置**：
   - 后端 `.env` 文件应在项目根目录
   - 前端 `.env` 文件应在 `frontend/` 目录

2. **确认文件格式**：
   ```env
   # 正确格式（无引号，无空格）
   OPENAI_API_KEY=sk-xxxxxxxxxxxxx
   
   # 错误格式
   OPENAI_API_KEY = "sk-xxxxxxxxxxxxx"  # 有空格和引号
   ```

3. **重启服务**：
   - 修改 `.env` 文件后，需要重启后端和前端服务

4. **验证环境变量**：
   ```bash
   # 后端
   python3 -c "import os; from dotenv import load_dotenv; load_dotenv(override=False); print('API Key:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"
   
   # 前端（需要重启开发服务器）
   # 在浏览器控制台查看：console.log(import.meta.env.VITE_API_BASE_URL)
   ```

### Q2: 前端无法连接后端？

**A**: 检查以下几点：

1. **确认后端正在运行**：
   ```bash
   curl http://localhost:8000/api/chat/health
   ```

2. **检查前端 `.env` 文件**：
   - 确认 `VITE_API_BASE_URL` 正确
   - 确认文件在 `frontend/` 目录下

3. **检查 CORS 配置**：
   - 后端默认允许所有来源（开发环境）
   - 生产环境需要配置具体域名

4. **查看浏览器控制台**：
   - 打开浏览器开发者工具（F12）
   - 查看 Network 标签，检查请求 URL 和错误信息

### Q3: 如何验证环境变量是否正确配置？

**A**: 使用以下命令验证：

```bash
# 检查后端环境变量
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv(override=False)
print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')
print('OPENAI_API_BASE_URL:', os.getenv('OPENAI_API_BASE_URL', 'NOT SET'))
print('HOST:', os.getenv('HOST', '0.0.0.0'))
print('PORT:', os.getenv('PORT', '8000'))
"

# 检查前端环境变量（需要重启开发服务器）
# 在浏览器控制台运行：
# console.log('VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL)
```

### Q4: 生产环境如何配置？

**A**: 生产环境配置建议：

1. **使用系统环境变量**（更安全）：
   ```bash
   export OPENAI_API_KEY="your_production_key"
   export ENV="production"
   ```

2. **修改前端 `.env`**：
   ```env
   VITE_API_BASE_URL=https://api.yourdomain.com
   ```

3. **构建前端**：
   ```bash
   cd frontend
   npm run build
   ```

4. **启动后端（生产模式）**：
   ```bash
   cd backend
   uvicorn backend.server:app --host 0.0.0.0 --port 8000 --workers 4
   ```

### Q5: .env 文件会被提交到 Git 吗？

**A**: 不会。`.env` 文件已添加到 `.gitignore`，不会被提交到版本控制。

但建议：
- 不要将包含真实 API Key 的 `.env` 文件提交到代码仓库
- 可以创建 `.env.example` 文件作为模板（不包含真实密钥）

---

## 配置检查清单

启动项目前，请确认：

- [ ] 后端 `.env` 文件已创建（项目根目录）
- [ ] `OPENAI_API_KEY` 已配置
- [ ] 前端 `.env` 文件已创建（`frontend/` 目录）
- [ ] `VITE_API_BASE_URL` 已配置
- [ ] 环境变量已验证（使用上述验证命令）
- [ ] 后端服务可以正常启动
- [ ] 前端可以正常连接后端

---

## 相关文档

- [README.md](README.md) - 项目总体说明
- [QUICK_START.md](QUICK_START.md) - 快速启动指南
- [API_INTERFACE.md](API_INTERFACE.md) - API 接口文档

---

## 更新日期

最后更新：2024-11-09
