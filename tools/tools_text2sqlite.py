from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_core.language_models import BaseLanguageModel
from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv

load_dotenv()

# 延迟初始化语言模型
llm = None
_current_model_name = None

def get_llm(model_name: str = "qwen-plus"):
    """
    获取或初始化语言模型
    
    注意：此函数不再依赖 Streamlit session_state，因为现在主要使用 FastAPI 后端。
    模型名称应该通过 agent.py 中的 LLM 配置传递，工具内部使用默认模型。
    """
    global llm, _current_model_name
    
    # 使用传入的模型名称（不再尝试从 Streamlit 获取）
    current_model = model_name
    
    # 如果模型名称改变或 llm 未初始化，重新创建
    if llm is None or _current_model_name != current_model:
        llm = init_chat_model(
            model=current_model, 
            model_provider="openai", 
            base_url=os.getenv("OPENAI_API_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        )
        _current_model_name = current_model  # 保存当前模型名称
    return llm

@tool(
    "text2sqlite_query",
    description="Use LLM to convert natural language text to a SQLite query."
)
def text2sqlite_tool(text: str, table_schema: str = "") -> Dict[str, Any]:
    """
    参数:
        text: 自然语言描述
        table_schema: 可选，表结构信息（如有）
    返回:
        生成的 SQLite 查询语句
    """
    def _build_prompt(text: str, table_schema: str) -> str:
        """
        构造给大模型的prompt。
        参数:
            text: 自然语言描述
            table_schema: 表结构信息
        """
        example_prompt = (
            "自然语言描述: 查询所有订单总金额大于1000元的客户姓名和订单号。\n"
            "表结构: " \
            "Table 2: STREAM_HACKATHON.STREAMLIT.ORDER_DETAILS (Stores order information)" \
            "This table contains information about orders placed by customers, including the date and total amount of each order." \

            "ORDER_ID: Number (38,0) [Primary Key, Not Null] - Unique identifier for orders" \
            "CUSTOMER_ID: Number (38,0) [Foreign Key - CUSTOMER_DETAILS(CUSTOMER_ID)] - Customer who made the order" \
            "ORDER_DATE: Date - Date when the order was made" \
            "TOTAL_AMOUNT: Number (10,2) - Total amount of the order" \
            "输出SQL: SELECT COUNT(*) FROM ORDER_DETAILS WHERE ORDER_DATE >= DATE('now', '-7 days');"
        )
        return (
            f"你是一个数据库专家，请根据以下自然语言描述，生成一个SQLite查询语句，只返回SQL，不要有任何解释。\n"
            f"注意：输出SQL里只需要跟上表名如：ORDER_DETAILS即可，不需要前缀STREAM_HACKATHON.STREAMLIT\n"
            f"自然语言描述: {text}\n"
            f"表结构: {table_schema}\n"
            f"示例: {example_prompt}\n"
        )

    # 构造 prompt
    prompt = _build_prompt(text, table_schema)

    # 获取 LLM 并调用
    current_llm = get_llm()
    response = current_llm.invoke(prompt)

    # 只返回SQL语句
    return {"sqlite_query": response.content}


import datetime

@tool(
    "get_time_by_timezone",
    description="获取指定时区的当前时间，返回格式如 2025-09-06 15:30:00。参数 timezone 例如 'Asia/Shanghai'、'UTC'、'America/New_York'。"
)
def get_time_by_timezone(timezone: str = "Asia/Shanghai") -> Dict[str, Any]:
    """
    获取指定时区的当前时间。
    参数:
        timezone: 时区字符串（如 'Asia/Shanghai', 'UTC', 'America/New_York'），默认北京时间
    返回:
        当前时间字符串，格式如 '2025-09-06 15:30:00'
    """
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(timezone)
        now = datetime.datetime.now(tz)
        return {"current_time": now.strftime("%Y-%m-%d %H:%M:%S"), "timezone": timezone}
    except Exception as e:
        # 回退到北京时间
        utc_now = datetime.datetime.utcnow()
        beijing_now = utc_now + datetime.timedelta(hours=8)
        return {
            "current_time": beijing_now.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": "Asia/Shanghai",
            "error": str(e)}