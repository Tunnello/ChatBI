from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_core.language_models import BaseLanguageModel
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import json
import os
# import streamlit_highcharts as hct

load_dotenv()

# 初始化语言模型（不再依赖 streamlit session_state）
# 使用环境变量或默认值
default_model = os.getenv("DEFAULT_MODEL", "qwen-plus")
llm = init_chat_model(
    model=default_model, 
    model_provider="openai", 
    base_url=os.getenv("OPENAI_API_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
)


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
        print(f"[DEBUG] Highcharts config generated successfully, chart_type: {chart_type}")
        return {"chart_config": config, "chart_type": chart_type, "status": "success"}
    except Exception as e:
        print(f"[ERROR] Failed to parse Highcharts JSON: {e}")
        print(f"[ERROR] Raw response: {response.content[:200]}")
        # 尝试提取 JSON 代码块
        try:
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response.content, re.DOTALL)
            if json_match:
                config = json.loads(json_match.group(1))
                return {"chart_config": config, "chart_type": chart_type, "status": "success"}
        except:
            pass
        return {"error": "Failed to parse LLM output", "raw": response.content, "status": "error"}