import os
from collections.abc import Iterator
from openai import OpenAI
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

PLACEHOLDER_KEYWORDS = (
    "在这里填入你的真实key",
    "your_real_key",
    "your_api_key",
    "replace_me",
    "your key",
)


def _is_placeholder_key(api_key: str | None) -> bool:
    """判断 Key 是否为空或仍是占位符。"""
    if not api_key or not api_key.strip():
        return True
    normalized = api_key.strip().lower()
    return any(keyword in normalized for keyword in PLACEHOLDER_KEYWORDS)


def ask_qwen_stream(messages: list) -> Iterator[str]:
    """
    将历史对话上下文发送给千问大模型，并流式返回回复片段。
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if _is_placeholder_key(api_key):
        yield "系统提示：大脑未连接，请先在 .env 文件中配置真实的千问 API Key 哦！"
        return

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    try:
        stream = client.chat.completions.create(
            model="qwen3.5-plus",  # 精准指定用户需要的 3.5-plus 模型
            messages=messages,
            stream=True
        )

        has_content = False
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                has_content = True
                yield delta

        if not has_content:
            yield "系统提示：大脑暂时没有返回内容，请稍后重试。"
    except Exception as e:
        yield f"大脑连接异常：{str(e)}"
