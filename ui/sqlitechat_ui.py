import html
import re, json
import streamlit as st
import streamlit_highcharts as hct
from langchain_core.callbacks.base import BaseCallbackHandler


user_url = "https://ts1.tc.mm.bing.net/th/id/R-C.16a2185d7d67a406288ea44d87f6a5b3?rik=cmmDTIeeMtNmxw&riu=http%3a%2f%2fpngimg.com%2fuploads%2fcat%2fcat_PNG50534.png&ehk=vpd0ZKFGuOf2fE7GsKsM7BLwQ%2fXDJqxLpESItKYR%2bqM%3d&risl=&pid=ImgRaw&r=0"
openai_url = "https://www.aiww.com/uploadfile/2024/0522/20240522062019722.png"
qwen_url = "https://www.aiww.com/uploadfile/2024/0522/20240522062019722.png"

def split_json_content(text):
    """
    从文本中提取JSON内容并分割为三部分
    
    参数:
        text: 包含JSON代码块的原始文本
        
    返回:
        如果匹配成功: 包含'before_json', 'json_data', 'after_json'的字典
        如果匹配失败: 原始文本
    """
    # 正则表达式模式
    pattern = r'(.*?)```json\n(.*?)\n```(.*)'
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        # 提取各部分内容
        before_json = match.group(1).strip()
        json_str = match.group(2)
        after_json = match.group(3).strip()
        
        # 解析JSON
        try:
            json_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            json_data = f"JSON解析错误: {str(e)}\n原始JSON字符串: {json_str}"
            
        # 返回分割后的结果
        return {
            'before_json': before_json,
            'json_data': json_data,
            'after_json': after_json
        }
    else:
        # 未匹配到时返回原始文本
        return text

def get_model_url(model_name):
    if "qwen" in model_name.lower():
        return qwen_url
    elif "gpt" in model_name.lower() or "o3" in model_name.lower():
        return openai_url

def format_message(text):
    """
    This function is used to format the messages in the chatbot UI.

    Parameters:
    text (str): The text to be formatted.
    """
    text_blocks = re.split(r"```[\s\S]*?```", text)
    code_blocks = re.findall(r"```([\s\S]*?)```", text)

    text_blocks = [html.escape(block) for block in text_blocks]

    formatted_text = ""
    for i in range(len(text_blocks)):
        formatted_text += text_blocks[i].replace("\n", "<br>")
        if i < len(code_blocks):
            formatted_text += f'<pre style="white-space: pre-wrap; word-wrap: break-word;"><code>{html.escape(code_blocks[i])}</code></pre>'

    return formatted_text


def message_func(text, is_user=False, is_df=False, model="gpt"):
    """
    This function displays messages in the chatbot UI, ensuring proper alignment and avatar positioning.

    Parameters:
    text (str): The text to be displayed.
    is_user (bool): Whether the message is from the user or not.
    is_df (bool): Whether the message is a dataframe or not.
    """
    model_url = get_model_url(model)
    avatar_url = user_url if is_user else model_url
    message_bg_color = (
        "linear-gradient(135deg, #00B2FF 0%, #006AFF 100%)" if is_user else "#71797E"
    )
    avatar_class = "user-avatar" if is_user else "bot-avatar"
    alignment = "flex-end" if is_user else "flex-start"
    margin_side = "margin-left" if is_user else "margin-right"
    message_text = text.strip()
    # print(f"This is message_text: {message_text}")

    if message_text:
        if is_user:
            message_text = html.escape(message_text.strip()).replace('\n', '<br>')
            container_html = f"""
            <div style="display:flex; align-items:flex-start; justify-content:flex-end; margin:0; padding:0; margin-bottom:10px;">
                <div style="background:{message_bg_color}; color:white; border-radius:20px; padding:10px; margin-right:5px; max-width:75%; font-size:14px; margin:0; line-height:1.2; word-wrap:break-word;">
                    {message_text}
                </div>
                <img src="{avatar_url}" class="{avatar_class}" alt="avatar" style="width:40px; height:40px; margin:0;" />
            </div>
            """
            st.write(container_html, unsafe_allow_html=True)
        else:
            # 支持多个 Highcharts 图表渲染
            # 匹配所有 ```json ... ``` 代码块
            pattern = r'```json\n(.*?)\n```'
            matches = list(re.finditer(pattern, message_text, re.DOTALL))
            if matches:
                # 依次渲染每个图表，文本分段
                last_end = 0
                for idx, match in enumerate(matches):
                    before_text = message_text[last_end:match.start()].strip()
                    json_str = match.group(1)
                    last_end = match.end()
                    # 自动处理前置文本为安全 HTML
                    if before_text:
                        safe_before_text = html.escape(before_text)
                        before_html = f"""
                        <div style="display:flex; align-items:flex-start; justify-content:flex-start; margin:0; padding:0; margin-bottom:10px;">
                            <img src="{avatar_url}" class="{avatar_class}" alt="avatar" style="width:30px; height:30px; margin:0; margin-right:5px; margin-top:5px;" />
                            <div style="color:black; border-radius:20px; padding:10px; margin-left:5px; max-width:75%; font-size:14px; margin:0; line-height:1.2; word-wrap:break-word;">
                                {safe_before_text}
                            </div>
                        </div>
                        """
                        st.write(before_html, unsafe_allow_html=True)
                    # 渲染图表
                    try:
                        json_data = json.loads(json_str)
                        if isinstance(json_data, dict):
                            hct.streamlit_highcharts(json_data)
                    except json.JSONDecodeError as e:
                        error_html = f"<div style='color:red;'>JSON解析错误: {str(e)}<br>原始JSON字符串: {json_str}</div>"
                        st.write(error_html, unsafe_allow_html=True)
                # 自动处理最后一段文本为安全 HTML
                after_text = message_text[last_end:].strip()
                if after_text:
                    safe_after_text = html.escape(after_text)
                    after_html = f"""
                    <div style="display:flex; align-items:flex-start; justify-content:flex-start; margin:0; padding:0; margin-bottom:10px;">
                        <img src="{avatar_url}" class="{avatar_class}" alt="avatar" style="width:30px; height:30px; margin:0; margin-right:5px; margin-top:5px;" />
                        <div style="color:black; border-radius:20px; padding:10px; margin-left:5px; max-width:75%; font-size:14px; margin:0; line-height:1.2; word-wrap:break-word;">
                            {safe_after_text}
                        </div>
                    </div>
                    """
                    st.write(after_html, unsafe_allow_html=True)
            else:
                # 没有图表时正常渲染文本
                container_html = f"""
                <div style="display:flex; align-items:flex-start; justify-content:flex-start; margin:0; padding:0; margin-bottom:10px;">
                    <img src="{avatar_url}" class="{avatar_class}" alt="avatar" style="width:30px; height:30px; margin:0; margin-right:5px; margin-top:5px;" />
                    <div style="color:black; border-radius:20px; padding:10px; margin-left:5px; max-width:75%; font-size:14px; margin:0; line-height:1.2; word-wrap:break-word;">
                        {message_text}
                    </div>
                </div>
                """
                st.write(container_html, unsafe_allow_html=True)



class StreamlitUICallbackHandler(BaseCallbackHandler):
    def __init__(self, model):
        self.token_buffer = []
        self.placeholder = st.empty()
        self.has_streaming_ended = False
        self.has_streaming_started = False
        self.model = model
        self.avatar_url = get_model_url(model)
        self.final_message = ""

    def start_loading_message(self):
        loading_message_content = self._get_bot_message_container("Thinking...")
        self.placeholder.markdown(loading_message_content, unsafe_allow_html=True)

    def on_llm_new_token(self, token, run_id, parent_run_id=None, **kwargs):
        if not self.has_streaming_started:
            self.has_streaming_started = True

        self.token_buffer.append(token)
        complete_message = "".join(self.token_buffer)
        container_content = self._get_bot_message_container(complete_message)
        self.placeholder.markdown(container_content, unsafe_allow_html=True)
        self.final_message = "".join(self.token_buffer)
        # if self.final_message:
        #     # 正则表达式模式
        #     pattern = r'(.*?)```json\n(.*?)\n```(.*)'
        #     match = re.search(pattern, self.final_message, re.DOTALL)
            
        #     if match:
        #         print("------------ Will render Highcharts JSON ------------")
        #         # 提取各部分内容
        #         before_text = match.group(1).strip()
        #         json_str = match.group(2)
        #         after_text = match.group(3).strip()
                
        #         # 封装前后内容为HTML
        #         def wrap_in_html(message_text):
        #             return f"""
        #                 <div style="display:flex; align-items:flex-start; justify-content:flex-start; margin:0; padding:0;">
        #                     <img src="{self.avatar_url}" class="bot-avatar" alt="avatar" style="width:30px; height:30px; margin:0;" />
        #                     <div style="background:#71797E; color:white; border-radius:20px; padding:10px; margin-left:5px; max-width:75%; font-size:14px; line-height:1.2; word-wrap:break-word;">
        #                         {self.final_message}
        #                     </div>
        #                 </div>
        #                 """
                
        #         before_html = wrap_in_html(before_text)
        #         after_html = wrap_in_html(after_text)
                
        #         # 解析JSON
        #         try:
        #             json_data = json.loads(json_str)
        #         except json.JSONDecodeError as e:
        #             json_data = f"JSON解析错误: {str(e)}\n原始JSON字符串: {json_str}"

        #         st.write(before_html, unsafe_allow_html=True)
        #         if isinstance(json_data, dict):
        #             hct.streamlit_highcharts(json_data, 640) #640 is the chart height
        #         st.write(after_html, unsafe_allow_html=True)
        #     else:
        #         container_html = f"""
        #                 <div style="display:flex; align-items:flex-start; justify-content:flex-start; margin:0; padding:0;">
        #                     <img src="{self.avatar_url}" class="bot-avatar" alt="avatar" style="width:30px; height:30px; margin:0;" />
        #                     <div style="background:#71797E; color:white; border-radius:20px; padding:10px; margin-left:5px; max-width:75%; font-size:14px; line-height:1.2; word-wrap:break-word;">
        #                         {self.final_message}
        #                     </div>
        #                 </div>
        #                 """
        #         st.write(container_html, unsafe_allow_html=True)

    def on_llm_end(self, response, run_id, parent_run_id=None, **kwargs):
        self.token_buffer = []
        self.has_streaming_ended = True
        self.has_streaming_started = False

    def _get_bot_message_container(self, text):
        """Generate the bot's message container style for the given text."""
        formatted_text = format_message(text.strip())
        if not formatted_text:  # If no formatted text, show "Thinking..."
            formatted_text = "Thinking..."
        # container_content = f"""
        # <div style="display:flex; align-items:flex-start; justify-content:flex-start; margin:0; padding:0;">
        #     <img src="{self.avatar_url}" class="bot-avatar" alt="avatar" style="width:30px; height:30px; margin:0;" />
        #     <div style="background:#71797E; color:white; border-radius:20px; padding:10px; margin-left:5px; max-width:75%; font-size:14px; line-height:1.2; word-wrap:break-word;">
        #         {formatted_text}
        #     </div>
        # </div>
        # """
        container_content = f"""
        <div style="display:flex; align-items:flex-start; justify-content:flex-start; margin:0; padding:0;">
            <img src="{self.avatar_url}" class="bot-avatar" alt="avatar" style="width:30px; height:30px; margin:0;" />
            <div style="color:black; border-radius:20px; padding:10px; margin-left:5px; max-width:75%; font-size:14px; line-height:1.2; word-wrap:break-word;">
                {formatted_text}
            </div>
        </div>
        """
        return container_content

    def display_dataframe(self, df):
        """
        Display the dataframe in Streamlit UI within the chat container.
        """
        message_alignment = "flex-start"
        avatar_class = "bot-avatar"

        st.write(
            f"""
            <div style="display: flex; align-items: flex-start; margin-bottom: 10px; justify-content: {message_alignment};">
                <img src="{self.avatar_url}" class="{avatar_class}" alt="avatar" style="width: 30px; height: 30px; margin-top: 0;" />
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write(df)


    def __call__(self, *args, **kwargs):
        pass
