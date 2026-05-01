# Conda 环境配置指南

本文档说明如何在 conda 的 nlp 环境下配置 ChatBI 项目。

## 方法一：使用 environment.yml 创建/更新环境（推荐）

### 1. 如果 nlp 环境已存在，更新它：

```bash
# 激活现有环境
conda activate nlp

# 更新环境（从 environment.yml）
conda env update -n nlp -f environment.yml --prune
```

### 2. 如果 nlp 环境不存在，创建新环境：

```bash
# 从 environment.yml 创建环境
conda env create -n nlp -f environment.yml

# 激活环境
conda activate nlp
```

## 方法二：手动安装（如果 environment.yml 不工作）

### 1. 创建/激活 nlp 环境：

```bash
# 如果环境不存在，创建它
conda create -n nlp python=3.12

# 激活环境
conda activate nlp
```

### 2. 安装依赖：

```bash
# 使用 pip 安装所有依赖
pip install -r requirements.txt

# 或者使用 uv（如果已安装）
uv sync
```

## 方法三：在现有 nlp 环境中安装

如果 nlp 环境已经存在，只需要安装项目依赖：

```bash
# 激活环境
conda activate nlp

# 检查 Python 版本（需要 >= 3.12）
python --version

# 如果版本不够，升级 Python
conda install python=3.12

# 安装项目依赖
pip install -r requirements.txt
```

## 验证安装

安装完成后，验证关键包是否安装成功：

```bash
python -c "import streamlit; import langchain; import chromadb; print('所有依赖安装成功！')"
```

## 配置环境变量

1. 创建 `.env` 文件（如果不存在）：

```bash
cp .env.example .env  # 如果有示例文件
```

2. 在 `.env` 文件中添加必要的 API 密钥：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE_URL=your_base_url_here  # 可选
```

## 初始化数据库和向量库

```bash
# 生成示例数据库
cd tools
python generate_sqlite_data.py

# 生成向量数据库（用于 RAG）
python ingest_chromadb.py
```

## 运行项目

```bash
# 确保在项目根目录
streamlit run main.py
```

## 常见问题

### 1. Python 版本不匹配

如果 nlp 环境的 Python 版本 < 3.12：

```bash
conda activate nlp
conda install python=3.12
```

### 2. 包冲突

如果遇到包冲突，可以尝试：

```bash
# 清理 pip 缓存
pip cache purge

# 重新安装
pip install --upgrade -r requirements.txt
```

### 3. chromadb 安装问题

如果 chromadb 安装失败，可能需要系统依赖：

```bash
# macOS
brew install libmagic

# Linux
sudo apt-get install libmagic1
```

### 4. 使用国内镜像源加速

如果下载慢，可以使用清华镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

## 环境管理命令

```bash
# 查看所有 conda 环境
conda env list

# 查看 nlp 环境中安装的包
conda list -n nlp

# 导出环境配置（备份）
conda env export -n nlp > environment_backup.yml

# 删除环境（如果需要重新创建）
conda env remove -n nlp
```

