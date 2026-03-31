import os
import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def get_client():
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key or api_key == "在这里填入你的真实Key" or api_key.strip() == "":
        return None

    # 恢复无代理纯净客户端，防止卡顿 40 秒
    http_client = httpx.Client(
        proxy=None,
        transport=httpx.HTTPTransport(local_address="0.0.0.0"),
    )

    return OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        http_client=http_client,
    )


# 【修复】：增加 model_name: str 参数
def ask_qwen_stream(messages: list, model_name: str):
    client = get_client()
    if not client:
        yield "【系统拦截】：大脑未连接！请检查 API Key。"
        return

    try:
        completion = client.chat.completions.create(
            model=model_name,  # 动态使用菜单传入的模型
            messages=messages,
            stream=True,
        )
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"【大脑连接异常】：{str(e)}"


def generate_chat_summary(messages: list) -> tuple[str, str]:
    client = get_client()
    if not client or not messages:
        return "未命名对话", "暂无摘要。"

    prompt = (
        "请阅读以下用户的聊天记录，为其生成一个标题和摘要。\n"
        "1. 标题不超过10个字。\n"
        "2. 摘要不超过30个字。\n"
        "3. 格式：标题|摘要\n\n"
        f"聊天记录：{str(messages)}"
    )
    try:
        completion = client.chat.completions.create(
            model="qwen3.5-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        result = completion.choices[0].message.content.strip()
        if "|" in result:
            title, summary = result.split("|", 1)
            return title.strip(), summary.strip()
        return "会话归档", result[:30]
    except Exception:
        return "归档失败", "摘要生成异常。"
