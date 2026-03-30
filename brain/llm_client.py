import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_client():
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key or api_key == "在这里填入你的真实Key" or api_key.strip() == "":
        return None
    return OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

def ask_qwen_stream(messages: list):
    """流式输出生成器，每次 yield 一个文字片段"""
    client = get_client()
    if not client:
        yield "【系统拦截】：大脑未连接！请先在项目根目录的 .env 文件中配置真实的千问 API Key。"
        return

    try:
        completion = client.chat.completions.create(
            model="qwen3.5-plus",
            messages=messages,
            stream=True  # 开启流式输出
        )
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"【大脑连接异常】：{str(e)}"

def generate_chat_summary(messages: list) -> tuple[str, str]:
    """后台悄悄调用的归档总结功能"""
    client = get_client()
    if not client or not messages:
        return "未命名对话", "暂无摘要内容。"

    prompt = (
        "请阅读以下用户的聊天记录，并为其生成一个标题和摘要。\n"
        "要求：\n"
        "1. 标题不超过10个字。\n"
        "2. 摘要不超过30个字，重点记录用户的偏好、事件或状态。\n"
        "3. 必须严格按照以下格式返回，中间用竖线 '|' 隔开：\n"
        "标题|摘要\n\n"
        f"聊天记录：{str(messages)}"
    )
    try:
        completion = client.chat.completions.create(
            model="qwen3.5-plus",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        result = completion.choices[0].message.content.strip()
        if "|" in result:
            title, summary = result.split("|", 1)
            return title.strip(), summary.strip()
        return "会话归档", result[:30]
    except:
        return "归档失败", "摘要生成异常。"
