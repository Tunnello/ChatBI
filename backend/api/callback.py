"""
流式输出回调处理器
用于 SSE 流式输出
"""
from typing import Any, Callable, List, Optional
import queue
import threading

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.messages import BaseMessage


def _extract_text(token: Any) -> str:
    """
    自適應解析不同類型的 token，回傳文字內容。
    """
    if token is None:
        return ""
    if isinstance(token, str):
        return token

    # LangChain 0.3 ChatOpenAI 會傳遞 AIMessageChunk / ChatGenerationChunk
    if hasattr(token, "content"):
        content = token.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts: List[str] = []
            for item in content:
                if isinstance(item, dict):
                    text_parts.append(item.get("text") or "")
                else:
                    text_parts.append(str(item))
            return "".join(text_parts)

    # OpenAI Delta 結構
    if hasattr(token, "delta"):
        delta = token.delta
        if isinstance(delta, dict):
            return delta.get("content", "")

    # 其他情況 fallback
    return str(token)


class StreamingCallbackHandler(BaseCallbackHandler):
    """流式输出回调处理器"""
    
    def __init__(self, token_callback: Optional[Callable[[str], None]] = None):
        self.token_buffer: List[str] = []
        self.final_message: str = ""
        self.has_streaming_started: bool = False
        self.has_streaming_ended: bool = False
        self.token_callback = token_callback  # 用于实时发送 token 的回调函数
        self.token_queue = queue.Queue()  # 用于存储待发送的 token
    
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """处理新的 token"""
        extracted = _extract_text(token)
        if not extracted:
            return

        if not self.has_streaming_started:
            self.has_streaming_started = True
        
        self.token_buffer.append(extracted)
        self.final_message = "".join(self.token_buffer)
        
        # 如果有回调函数，实时发送 token
        if self.token_callback:
            try:
                self.token_callback(extracted)
            except Exception as e:
                print(f"Error in token callback: {e}")
    
    def on_llm_end(self, response, **kwargs) -> None:
        """LLM 输出结束"""
        self.has_streaming_ended = True
        self.has_streaming_started = False
    
    def on_llm_error(self, error: Exception, **kwargs) -> None:
        """LLM 错误处理"""
        self.final_message = f"错误: {str(error)}"
        self.has_streaming_ended = True

