
# ChatBI 智能数据对话助手

ChatBI 是一个基于 Streamlit 的智能数据对话应用，支持自然语言与本地 SQLite 数据库交互，自动生成 SQL 查询并可视化结果。适用于数据分析、报表生成、业务洞察等场景，无需手写 SQL，轻松获取数据洞察。

## 主要功能

- **自然语言 SQL 生成**：输入中文或英文问题，自动生成并执行 SQL 查询。
- **多模型支持**：集成主流大模型（如 Qwen、GPT、Claude、Llama 等）。
- **数据可视化**：支持表格和图表展示查询结果。
- **会话记忆**：上下文记忆，支持多轮对话。
- **自定义数据库结构**：支持自定义 SQLite 数据库和表结构。
- **错误自愈**：自动识别 SQL 错误并给出修复建议。

## 项目结构

- `main.py`：Streamlit 主入口，负责 UI 渲染和对话逻辑。
- `agent.py`：智能体核心，负责模型调用和工具管理。
- `tools_execute_sqlite.py`：SQLite 查询工具，负责 SQL 执行与结果返回。
- `generate_sqlite_data.py`：生成示例数据库和数据。
- `ui/sqlitechat_ui.py`：UI 组件，负责消息展示和图表渲染。
- `docs/`：数据库表结构说明（如 `customer_details.md`、`order_details.md` 等）。
- `sql/`：数据库建表 SQL 文件。
- `example.db`：示例 SQLite 数据库。

## 安装与运行

1. 克隆项目：
   ```bash
   git clone https://github.com/yourusername/ChatBI.git
   cd ChatBI
   ```

2. 安装依赖（建议使用虚拟环境）：
   ```bash
   pip install -r requirements.txt
   ```

3. 生成示例数据库（可选）：
   ```bash
   python generate_sqlite_data.py
   ```

4. 启动应用：
   ```bash
   streamlit run main.py
   ```

## 数据库结构示例

- 客户表（CUSTOMER_DETAILS）：客户信息
- 订单表（ORDER_DETAILS）：订单信息
- 产品表（PRODUCTS）：产品信息
- 支付表（PAYMENTS）：支付记录
- 交易表（TRANSACTIONS）：交易流水

详细字段见 `docs/` 文件夹。

## 贡献方式

欢迎提交 PR 或 Issue，完善功能、修复 Bug 或优化体验。

## 许可证

MIT License
