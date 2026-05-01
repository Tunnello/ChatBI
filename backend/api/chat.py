"""
聊天 API 路由
支持 SSE 流式输出
"""
import json
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
try:
    from sse_starlette.sse import EventSourceResponse
except ImportError:
    # 如果 sse-starlette 不可用，使用简单的流式响应
    from fastapi.responses import StreamingResponse
    import asyncio

from agent import MessagesState, create_agent
from langchain_core.messages import HumanMessage
from backend.api.callback import StreamingCallbackHandler

router = APIRouter()


class ChatRequest(BaseModel):
    """聊天请求模型"""
    query: str
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    model: str = "qwen-plus"


class ChatResponse(BaseModel):
    """聊天响应模型"""
    request_id: str
    session_id: str
    message: str
    finished: bool


async def stream_agent_response(query: str, session_id: str, request_id: str, model: str):
    """
    流式输出 Agent 响应
    
    Args:
        query: 用户查询
        session_id: 会话 ID
        request_id: 请求 ID
        model: 模型名称
    """
    import asyncio
    import queue
    from queue import Queue
    
    try:
        # 用于存储流式输出的队列
        token_queue = Queue()
        accumulated_message = ""
        
        # 创建回调处理器，实时发送 token
        def on_token(token: str):
            """实时发送 token"""
            print(f"[DEBUG] Received token: {repr(token[:50])}")
            token_queue.put(token)
        
        callback_handler = StreamingCallbackHandler(token_callback=on_token)
        
        # 创建 Agent
        react_graph = create_agent(callback_handler, model)
        
        # 创建消息状态
        messages = [HumanMessage(content=query)]
        state = MessagesState(messages=messages)
        
        # 配置
        config = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": 100  # 增加递归限制，避免复杂任务时过早停止
        }
        
        # 发送初始消息
        yield {
            "event": "message",
            "data": json.dumps({
                "type": "start",
                "request_id": request_id,
                "session_id": session_id,
                "message": "已接收到你的任务，将立即开始处理...",
                "finished": False
            }, ensure_ascii=False)
        }
        
        # 在后台线程执行 Agent
        def run_agent():
            try:
                print(f"[DEBUG] Starting agent execution for query: {query[:50]}...")
                print(f"[DEBUG] Config: {config}")
                # 使用 invoke 方法，递归限制已在 config 中设置
                result = react_graph.invoke(state, config=config)
                print(f"[DEBUG] Agent execution completed. Final message length: {len(callback_handler.final_message)}")
                print(f"[DEBUG] Final message preview: {callback_handler.final_message[:100]}...")
                return result
            except Exception as e:
                error_msg = str(e)
                print(f"[ERROR] Agent execution failed: {error_msg}")
                import traceback
                traceback.print_exc()
                # 如果是递归限制错误，提供更友好的错误信息
                if "recursion_limit" in error_msg.lower():
                    error_msg = f"任务执行步骤过多（超过{config.get('recursion_limit', 100)}步）。这可能是因为任务过于复杂或陷入了循环。请尝试简化您的问题或重新表述。"
                token_queue.put(("error", error_msg))
                return None
        
        # 启动 Agent 执行
        loop = asyncio.get_event_loop()
        agent_future = loop.run_in_executor(None, run_agent)
        
        # 实时发送 token
        agent_done = False
        last_message_sent = ""
        
        while not agent_done:
            try:
                # 尝试获取 token（非阻塞）
                try:
                    token = token_queue.get_nowait()
                    if isinstance(token, tuple) and token[0] == "error":
                        raise Exception(token[1])
                    accumulated_message += token
                    
                    # 只有当消息有变化时才发送
                    if accumulated_message != last_message_sent:
                        last_message_sent = accumulated_message
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "type": "response",
                                "request_id": request_id,
                                "session_id": session_id,
                                "message": accumulated_message,
                                "finished": False
                            }, ensure_ascii=False)
                        }
                except queue.Empty:
                    # 队列为空，检查 Agent 是否完成
                    if agent_future.done():
                        agent_done = True
                        try:
                            result = await agent_future
                        except Exception as e:
                            raise e
                        
                        # 发送剩余的 token
                        while not token_queue.empty():
                            try:
                                token = token_queue.get_nowait()
                                if isinstance(token, tuple) and token[0] == "error":
                                    raise Exception(token[1])
                                accumulated_message += token
                            except queue.Empty:
                                break
                        
                        # 获取最终消息
                        final_message = callback_handler.final_message if callback_handler.final_message else accumulated_message
                        
                        print(f"[DEBUG] Sending final message. Length: {len(final_message)}")
                        print(f"[DEBUG] Accumulated message length: {len(accumulated_message)}")
                        print(f"[DEBUG] Callback handler final message length: {len(callback_handler.final_message) if callback_handler.final_message else 0}")
                        print(f"[DEBUG] Result type: {type(result)}")
                        if result:
                            print(f"[DEBUG] Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
                        
                        # 如果最终消息为空，尝试从 result 中获取
                        if not final_message and result:
                            if isinstance(result, dict) and "messages" in result:
                                messages = result["messages"]
                                print(f"[DEBUG] Found {len(messages)} messages in result")
                                
                                # 检查是否有工具调用（特别是图表工具）
                                from langchain_core.messages import AIMessage, ToolMessage
                                chart_config = None
                                for msg in messages:
                                    if isinstance(msg, ToolMessage):
                                        print(f"[DEBUG] Found ToolMessage: tool_call_id={msg.tool_call_id}")
                                        print(f"[DEBUG] ToolMessage content type: {type(msg.content)}")
                                        print(f"[DEBUG] ToolMessage content preview: {str(msg.content)[:200]}")
                                        # 检查是否是图表工具的返回
                                        if isinstance(msg.content, dict) and "chart_config" in msg.content:
                                            chart_config = msg.content["chart_config"]
                                            print(f"[DEBUG] Found chart_config in ToolMessage!")
                                
                                # 查找最后一个 AI 消息
                                for msg in reversed(messages):
                                    if isinstance(msg, AIMessage):
                                        if hasattr(msg, "content"):
                                            final_message = msg.content
                                            print(f"[DEBUG] Got AI message from result: {len(final_message)} chars")
                                            # 如果有图表配置，添加到消息中
                                            if chart_config:
                                                print(f"[DEBUG] Adding chart_config to final message")
                                                # 将图表配置以 JSON 代码块形式添加到消息中
                                                chart_json = json.dumps(chart_config, ensure_ascii=False, indent=2)
                                                final_message = f"{final_message}\n\n```json\n{chart_json}\n```"
                                            break
                                # 如果没有 AI 消息，尝试获取最后一个消息的内容
                                if not final_message and messages:
                                    last_msg = messages[-1]
                                    if hasattr(last_msg, "content"):
                                        final_message = str(last_msg.content)
                                        print(f"[DEBUG] Got last message content: {len(final_message)} chars")
                        
                        # 如果还是没有消息，至少发送一个提示
                        if not final_message:
                            final_message = "处理完成，但未收到响应内容。"
                            print(f"[WARNING] No message content found!")
                        
                        # 发送最终消息
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "type": "response",
                                "request_id": request_id,
                                "session_id": session_id,
                                "message": final_message,
                                "finished": True
                            }, ensure_ascii=False)
                        }
                        print(f"[DEBUG] Final message sent successfully")
                    else:
                        # 任务未完成，等待一小段时间
                        await asyncio.sleep(0.1)
            except Exception as e:
                agent_done = True
                raise e
        
    except Exception as e:
        # 发送错误消息
        yield {
            "event": "error",
            "data": json.dumps({
                "type": "error",
                "request_id": request_id,
                "session_id": session_id,
                "message": f"处理请求时出错: {str(e)}",
                "finished": True
            }, ensure_ascii=False)
        }


@router.post("/query")
async def chat_query(request: ChatRequest):
    """
    聊天查询接口（SSE 流式输出）
    
    Args:
        request: 聊天请求
        
    Returns:
        SSE 流式响应
    """
    session_id = request.session_id or "default"
    request_id = request.request_id or str(uuid.uuid4())
    
    try:
        from sse_starlette.sse import EventSourceResponse
        return EventSourceResponse(
            stream_agent_response(
                query=request.query,
                session_id=session_id,
                request_id=request_id,
                model=request.model
            )
        )
    except ImportError:
        # 如果 sse-starlette 不可用，使用 StreamingResponse
        from fastapi.responses import StreamingResponse
        import asyncio
        
        async def generate():
            async for event in stream_agent_response(
                query=request.query,
                session_id=session_id,
                request_id=request_id,
                model=request.model
            ):
                yield f"event: {event['event']}\ndata: {event['data']}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "ChatBI API"}


@router.get("/models")
async def get_all_models():
    """
    获取所有可用的模型/数据库信息
    
    Returns:
        模型列表，包含模型名称和 schema 信息
    """
    # 从 agent.py 获取可用的模型配置
    from agent import get_model_configurations
    
    model_configurations = get_model_configurations()
    
    # 返回模型列表（暂时不包含 schema 信息，因为需要查询数据库）
    models = []
    for model_name in model_configurations.keys():
        models.append({
            "modelName": model_name,
            "modelCode": model_name,
            "schemaList": []  # 暂时返回空数组，后续可以添加数据库 schema 查询
        })
    
    return models

