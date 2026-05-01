from dataclasses import dataclass
from typing import Annotated, Sequence, Optional
import os
import warnings

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

from tools.tools_rag import retriever_tool, search
from tools.tools_text2sqlite import text2sqlite_tool#, get_time_by_timezone
from tools.tools_execute_sqlite import execute_sqlite_query
from tools.tools_charts import highcharts_tool
from tools.tools_export import export_artifacts_tool


from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio

from PIL import Image
from io import BytesIO

from dotenv import load_dotenv
# 加载 .env 文件，但不覆盖已存在的系统环境变量
load_dotenv(override=False)

# 抑制 Streamlit 在非 Streamlit 环境中的警告
# 这些警告在 FastAPI 后端环境中是正常的，可以安全忽略
warnings.filterwarnings("ignore", category=UserWarning, module="streamlit")
warnings.filterwarnings("ignore", message=".*missing ScriptRunContext.*")
warnings.filterwarnings("ignore", message=".*Session state does not function.*")
os.environ["STREAMLIT_SERVER_RUNNING"] = "false"

@dataclass
class MessagesState:
    messages: Annotated[Sequence[BaseMessage], add_messages]

memory = MemorySaver()

# Set up MCP client
import os
from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).resolve().parent
mcp_time_path = project_root / "tools" / "mcp_time.py"

client = MultiServerMCPClient(
    {
        "time": {
            "command": "python",
            # 使用绝对路径
            "args": [str(mcp_time_path)],
            "transport": "stdio",
        },
        # 注释掉失效的 fetch 服务
        # "fetch": {
        #     "transport": "streamable_http",
        #     "url": "https://mcp.api-inference.modelscope.net/12c7b43a064846/mcp"
        # }
    }
)
# 异步方式
async def get_mcp_tools():
    try:
        mcp_tools = await client.get_tools()
        return mcp_tools
    except Exception as e:
        print(f"Warning: Failed to load MCP tools: {e}")
        return []


# 安全地加载 MCP 工具，失败时不阻塞启动
try:
    mcp_tools = asyncio.run(get_mcp_tools())
except Exception as e:
    print(f"Warning: Failed to initialize MCP tools: {e}")
    mcp_tools = []
tools = [retriever_tool, search, text2sqlite_tool, highcharts_tool, execute_sqlite_query, export_artifacts_tool]
tools = tools + mcp_tools

@dataclass
class ModelConfig:
    model_name: str
    api_key: str
    base_url: Optional[str] = None

def get_env_var(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    从系统环境变量或 .env 文件获取环境变量
    优先使用系统环境变量（如果已设置）
    """
    # os.getenv() 会先从系统环境变量读取，如果没有再从 .env 文件读取（如果 load_dotenv 已调用）
    value = os.getenv(var_name, default)
    return value

# 模型配置 - 使用函数动态获取环境变量，而不是在模块加载时
def get_model_configurations():
    """动态获取模型配置，确保每次调用时都读取最新的环境变量"""
    api_key = get_env_var("OPENAI_API_KEY")
    base_url = get_env_var("OPENAI_API_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    
    return {
        "qwen-plus": ModelConfig(
            model_name="qwen-plus", 
            api_key=api_key,
            base_url=base_url
        ),
        "qwen-turbo": ModelConfig(
            model_name="qwen-turbo", 
            api_key=api_key,
            base_url=base_url
        ),
        "qwen3-max-preview": ModelConfig(
            model_name="qwen3-max-preview", 
            api_key=api_key,
            base_url=base_url
        )
    }

sys_msg = SystemMessage(
    content="""You're an AI assistant specializing in data analysis with Sqlite SQL.
    Before answer the question, always get available tools first, then think step by step to use the tools to get the answer.
    Remember first get the schema of the table by using the tool "database_schema_rag" if needed.
    You have access to the following tools:
    - database_schema_rag: This tool allows you to search for database schema details when needed to generate the SQL code.
    - text2sqlite_query: This tool allows you to convert natural language text to a SQLite query.
    - execute_sqlite_query: This tool allows you to execute a SQLite query on a fixed database and return the results as JSON. Use this tool to interact with the SQLite database.
    - high_charts_json: This tool allows you to generate Highcharts JSON config from a list of numbers and chart type. IMPORTANT: When the user asks to draw a chart, graph, or visualization (like "画图", "画出", "图表", "可视化"), you MUST:
      1. First execute a SQL query to get the data
      2. Extract the numeric data from the query results
      3. Call high_charts_json tool with the numbers and appropriate chart type (like "area", "line", "column", "bar", "spline")
      4. Include the chart configuration in your final answer

    Your final answer should contain the analysis results or visualizations based on the user's question and the data retrieved from the database.
    When the user requests a chart, you MUST generate and include the chart configuration using the high_charts_json tool.
    You should try to add some insights based on the data.
    """
)


def create_agent(callback_handler: BaseCallbackHandler, model_name: str) -> StateGraph:
    # 动态获取模型配置，确保读取最新的环境变量
    model_configurations = get_model_configurations()
    config = model_configurations.get(model_name)
    if not config:
        raise ValueError(f"Unsupported model name: {model_name}")

    if not config.api_key:
        # 提供更详细的错误信息
        env_key = os.getenv("OPENAI_API_KEY")
        if env_key:
            raise ValueError(f"API key for model '{model_name}' is empty. Please check your environment variable OPENAI_API_KEY.")
        else:
            raise ValueError(
                f"API key for model '{model_name}' is not set. "
                f"Please set the OPENAI_API_KEY environment variable. "
                f"You can set it in your system environment or create a .env file in the project root."
            )

    llm = ChatOpenAI(
        model=config.model_name,
        api_key=config.api_key,
        callbacks=[callback_handler],
        streaming=True,
        base_url=config.base_url,
        temperature=0.1
    )

    llm_with_tools = llm.bind_tools(tools)

    def llm_agent(state: MessagesState):
        return {"messages": [llm_with_tools.invoke([sys_msg] + state.messages)]}

    builder = StateGraph(MessagesState)
    builder.add_node("llm_agent", llm_agent)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "llm_agent")
    builder.add_conditional_edges("llm_agent", tools_condition)
    builder.add_edge("tools", "llm_agent")
    # builder.add_edge("llm_agent", END)
    react_graph = builder.compile(checkpointer=memory)

    # png_data = react_graph.get_graph(xray=True).draw_mermaid_png()
    # with open("graph_2.png", "wb") as f:
    #     f.write(png_data)

    # image = Image.open(BytesIO(png_data))
    # st.image(image, caption="React Graph")

    return react_graph
