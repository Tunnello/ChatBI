import streamlit as st
from dataclasses import dataclass
from typing import Annotated, Sequence, Optional

from langchain.callbacks.base import BaseCallbackHandler
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

from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio

from PIL import Image
from io import BytesIO

from dotenv import load_dotenv
load_dotenv()

@dataclass
class MessagesState:
    messages: Annotated[Sequence[BaseMessage], add_messages]

memory = MemorySaver()

# Set up MCP client
client = MultiServerMCPClient(
    {
        "time": {
            "command": "python",
            # Make sure to update to the full absolute path to your file
            "args": ["./tools/mcp_time.py"],
            "transport": "stdio",
        },
        # "time": {
        #     # make sure you start your weather server on port 1234
        #     "url": "https://:1234/mcp/",
        #     "transport": "streamable_http",
        # },
        # "weather": {
        #     # make sure you start your weather server on port 8000
        #     "url": "https://:8000/mcp/",
        #     "transport": "streamable_http",
        # }
    }
)
# 异步方式
async def get_mcp_tools():
    mcp_tools = await client.get_tools()
    return mcp_tools


mcp_tools = asyncio.run(client.get_tools())
# st.write(f"mcp_tools: {mcp_tools}")

tools = [retriever_tool, search, text2sqlite_tool, highcharts_tool, execute_sqlite_query]
tools = tools + mcp_tools
@dataclass
class ModelConfig:
    model_name: str
    api_key: str
    base_url: Optional[str] = None

model_configurations = {
    "qwen-plus": ModelConfig(
        model_name="qwen-plus", api_key=st.secrets["OPENAI_API_KEY"],
        base_url=st.secrets["OPENAI_API_BASE_URL"] if "OPENAI_API_BASE_URL" in st.secrets else None
    ),
    "qwen-turbo": ModelConfig(
        model_name="qwen-turbo", api_key=st.secrets["OPENAI_API_KEY"],
        base_url=st.secrets["OPENAI_API_BASE_URL"] if "OPENAI_API_BASE_URL" in st.secrets else None
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
    - high_charts_json: This tool allows you to generate Highcharts JSON config from a list of numbers and chart type.

    Your final answer should contain the analysis results or visualizations based on the user's question and the data retrieved from the database.
    """
)


def create_agent(callback_handler: BaseCallbackHandler, model_name: str) -> StateGraph:
    config = model_configurations.get(model_name)
    if not config:
        raise ValueError(f"Unsupported model name: {model_name}")

    if not config.api_key:
        raise ValueError(f"API key for model '{model_name}' is not set. Please check your environment variables or secrets configuration.")

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
