from typing import List, Dict, Any
from langchain.tools import tool
from langchain_core.language_models import BaseLanguageModel
from langchain.chat_models import init_chat_model
# import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

# 初始化语言模型
llm = init_chat_model(model="qwen-plus", model_provider="openai", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

@tool(
    "high_charts_html",
    description="Use LLM to generate Highcharts chart_html (for Streamlit HTML embedding) from a list of numbers and chart type."
)
def highcharts_html_tool(numbers: List[float], chart_type: str = "pie") -> Dict[str, Any]:
    """
    参数:
        numbers: 数字列表，用于生成图表数据
        chart_type: 图表类型（如 'pie', 'line', 'column', 'bar', 'spline' 等），默认为 'pie'
    返回:
        Highcharts chart_html 片段（可直接嵌入 Streamlit HTML）
    """
    def _build_prompt(numbers: List[float], chart_type: str) -> str:
        """
        构造给大模型的prompt。
        参数:
            numbers: 数字列表
            chart_type: 图表类型
        """
        example_html = '''<div id='container' style='width: 550px; height: 400px; margin: 0 auto'></div>\n<script src='https://code.highcharts.com/highcharts.js'></script>\n<script>\ndocument.addEventListener('DOMContentLoaded', function() {\n   var chart = {\n       plotBackgroundColor: null,\n       plotBorderWidth: null,\n       plotShadow: false\n   };\n   var title = {\n      text: '2014 年各浏览器市场占有比例'\n   };\n   var series= [{\n      type: 'pie',\n      name: 'Browser share',\n      data: [\n         ['Firefox',   45.0],\n         ['IE',       26.8],\n         {name: 'Chrome', y: 12.8, sliced: true, selected: true},\n         ['Safari',    8.5],\n         ['Opera',     6.2],\n         ['Others',   0.7]\n      ]\n   }];\n   var json = {};\n   json.chart = chart;\n   json.title = title;\n   json.series = series;\n   Highcharts.chart('container', json);\n});\n</script>'''
        return (
            f"你是一个前端可视化专家，请根据以下数字列表，生成一个Highcharts的{chart_type}图嵌入HTML片段（只返回chart_html，不要有任何解释，不要返回整个网页，只要图表相关的div和script）。\n"
            f"数字列表: {numbers}\n"
            "要求：\n"
            f"1. 图表类型为{chart_type}。\n"
            "2. x轴为序号（从1开始），y轴为数字。\n"
            "3. 只返回可嵌入Streamlit的chart_html片段，不要有解释。\n"
            "4. 示例：\n"
            f"{example_html}\n"
            f"严格按照示例格式返回，不要添加任何多余内容。"
        )

    # 构造 prompt
    prompt = _build_prompt(numbers, chart_type)

    # 调用 LLM
    response = llm.invoke(prompt)
    # components.html(response, height=450)

    # 返回 chart_html
    return {"chart_html": response}