from tools_execute_sqlite import execute_sqlite_query
import streamlit as st

# 调试用：检查 products 表是否存在，并尝试查询部分数据

def debug_execute_sqlite():
    print("\n--- 检查表结构 ---")
    # 查询 sqlite_master 获取所有表名
    result = execute_sqlite_query("SELECT name FROM sqlite_master WHERE type='table';")
    print("所有表:", result)

    print("\n--- 尝试查询 products 表 ---")
    result = execute_sqlite_query("SELECT * FROM products LIMIT 5;")
    result = execute_sqlite_query("SELECT COUNT(*) FROM products;")
    print("products 表查询结果:", result)

def debug_function_calling():
    from langchain_core.utils.function_calling import convert_to_openai_function
    from langchain_core.messages import HumanMessage
    from langchain.chat_models import init_chat_model
    from tools_execute_sqlite import execute_sqlite_query
    from dotenv import load_dotenv
    load_dotenv()
    
    tools = [execute_sqlite_query]
    llm = init_chat_model(model = st.session_state.get("model", "qwen-plus"), model_provider="openai", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
    # 将我们定义的LangChain工具转换为OpenAI函数描述格式
    functions_for_model = [convert_to_openai_function(t) for t in tools]

    # 示例：询问北京天气
    # 我们期望模型能识别出应该调用 get_weather 工具
    message = HumanMessage(content="帮我执行 SELECT COUNT(*) FROM products;")
    response = llm.invoke([message], functions=functions_for_model)

    print("\n模型对简单函数调用的响应:")
    print(response)

def debug_agent_function_calling():

    from langchain.agents import create_openai_functions_agent
    from langchain.agents import AgentExecutor
    from langchain.chat_models import init_chat_model
    from tools_execute_sqlite import execute_sqlite_query
    from dotenv import load_dotenv
    load_dotenv()

    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    # 创建代理所需的提示模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个有用的AI助手。使用提供的工具来回答用户问题。请一步一步思考，并清晰地说明你打算调用哪个工具以及为什么。"),
        MessagesPlaceholder(variable_name="chat_history"), # 用于存储对话历史
        ("human", "{input}"), # 用户的当前输入
        MessagesPlaceholder(variable_name="agent_scratchpad"), # Agent的中间步骤，如工具调用和结果
    ])

    
    tools = [execute_sqlite_query]
    llm = init_chat_model(model = st.session_state.get("model", "qwen-plus"), model_provider="openai", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

    # 创建Agent
    # 这个agent知道如何使用OpenAI的函数调用特性来决定调用哪个工具
    agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)

    # 创建Agent执行器
    # AgentExecutor负责实际执行Agent的决策，调用工具，并将结果反馈给Agent
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,  # 设置为True可以看到Agent的详细执行过程
        handle_parsing_errors=True # 帮助处理LLM输出不符合预期格式时的错误
    )

    # 调用Agent执行器
    # "input" 是用户的请求
    # "chat_history" 是一个消息列表，用于维护对话上下文（在此例中为空）
    result = agent_executor.invoke({
        "input": '''帮我执行 SELECT COUNT(*) FROM products;，先整合成tools调用的格式，再执行。''',
        "chat_history": []
    })

    print("Agent的最终输出:")
    print(result["output"])



if __name__ == "__main__":
    # debug_execute_sqlite()
    # debug_function_calling()
    # debug_agent_function_calling()
    import os

    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    os.path.join(current_file_dir, "example.db")
    print(current_file_dir)
    print(os.path.join(current_file_dir, "example.db"))