from typing import List, Dict, Any
from langchain.tools import tool
from langchain_core.language_models import BaseLanguageModel
from langchain.chat_models import init_chat_model
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# 初始化语言模型
llm = init_chat_model(model = st.session_state.get("model", "qwen-plus"), model_provider="openai", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

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
            "你是一个数据库专家，请根据以下自然语言描述，生成一个SQLite查询语句，只返回SQL，不要有任何解释。\n"
            "自然语言描述: 查询所有订单总金额大于1000元的客户姓名和订单号。\n"
            "表结构: CUSTOMER_DETAILS(CUSTOMER_ID, FIRST_NAME, LAST_NAME), ORDER_DETAILS(ORDER_ID, CUSTOMER_ID, TOTAL_AMOUNT)\n"
            "示例SQL: SELECT c.FIRST_NAME, c.LAST_NAME, o.ORDER_ID FROM CUSTOMER_DETAILS c JOIN ORDER_DETAILS o ON c.CUSTOMER_ID = o.CUSTOMER_ID WHERE o.TOTAL_AMOUNT > 1000;\n"
        )
        return (
            f"你是一个数据库专家，请根据以下自然语言描述，生成一个SQLite查询语句，只返回SQL，不要有任何解释。\n"
            f"自然语言描述: {text}\n"
            f"表结构: {table_schema}\n"
            f"示例: {example_prompt}\n"
        )

    # 构造 prompt
    prompt = _build_prompt(text, table_schema)

    # 调用 LLM
    response = llm.invoke(prompt)

    # 只返回SQL语句
    return {"sqlite_query": response.content}
