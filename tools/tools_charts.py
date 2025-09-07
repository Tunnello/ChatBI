from typing import List, Dict, Any
from langchain.tools import tool
from langchain_core.language_models import BaseLanguageModel
from langchain.chat_models import init_chat_model
import streamlit as st
from dotenv import load_dotenv
import json
# import streamlit_highcharts as hct

load_dotenv()

# 初始化语言模型
llm = init_chat_model(model = st.session_state.get("model", "qwen-plus"), model_provider="openai", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")


@tool(
    "high_charts_json",
    description="Use LLM to generate Highcharts JSON config from a list of numbers and chart type."
)
def highcharts_tool(numbers: List[float], chart_type: str = "line") -> Dict[str, Any]:
    """
    参数:
        numbers: 数字列表，用于生成图表数据
        chart_type: 图表类型（如 'line', 'column', 'bar', 'spline' 等），默认为 'line'
    返回:
        Highcharts JSON 配置字典
    """
    def _build_prompt(numbers: List[float], chart_type: str) -> str:
        """
        构造给大模型的prompt。
        参数:
            numbers: 数字列表
            chart_type: 图表类型
        """
        example_json = '''json\n{
   "title":{
      "text":"Sales of petroleum products March, Norway",
      "align":"left"
   },
   "xAxis":{
      "categories":["Jet fuel","Duty-free diesel"]
   },
   "yAxis":{
      "title":{"text":"Million liter"}
   },
   "series":[
        {"type":"column",
            "name":"2020",
            "data":[59,83]},
        {"type":"column",
            "name":"2021",
            "data":[24,79]
        },
        {"type":"column",
            "name":"2022",
            "data":[58,88]
        },
        {"type":"spline",
            "name":"Average",
            "data":[47,83.33],
            "marker":{
                "lineWidth":2,
                "fillColor":"black"
            }
        }
    ]
}'''
        return (
            f"你是一个前端可视化专家，请根据以下要求生成 Highcharts 的 {chart_type} 图 JSON 配置：\n"
            f"- 数据列表: {numbers}\n"
            f"- 图表类型: {chart_type}\n"
            "- 只输出标准 JSON，不要有任何解释、不要有 html、markdown 标签。\n"
            "- 保证输出内容能被 Python 的 json.loads 正确解析。\n"
            "- 结构参考如下示例：\n"
            f"{example_json}\n"
            "- 输出前请再次校验格式。"
        )

    # 构造 prompt
    prompt = _build_prompt(numbers, chart_type)

    # 调用 LLM
    response = llm.invoke(prompt)

    # 解析 JSON
    try:
        config = json.loads(response.content)
        # hct.streamlit_highcharts(config, 640)
    except Exception:
        config = {"error": "Failed to parse LLM output", "raw": response.content}

    return response