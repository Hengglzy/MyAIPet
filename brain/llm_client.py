import os
import httpx
from openai import OpenAI
from dotenv import load_dotenv
from tools.registry import execute_tool

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


def ask_qwen_stream(messages: list, model_name: str, tool_schemas: list = None):
    client = get_client()
    if not client:
        yield "【系统拦截】：大脑未连接！请检查 API Key。"
        return

    try:
        request_kwargs = {
            "model": model_name,
            "messages": messages,
            "stream": True,
        }
        if tool_schemas:
            request_kwargs["tools"] = tool_schemas

        completion = client.chat.completions.create(
            **request_kwargs
        )

        pending_tool_calls = {}
        for chunk in completion:
            delta = chunk.choices[0].delta

            if delta.content is not None:
                yield delta.content

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in pending_tool_calls:
                        pending_tool_calls[idx] = {"id": "", "name": "", "arguments": ""}
                    if tc.id:
                        pending_tool_calls[idx]["id"] = tc.id
                    if tc.function and tc.function.name:
                        pending_tool_calls[idx]["name"] = tc.function.name
                    if tc.function and tc.function.arguments:
                        pending_tool_calls[idx]["arguments"] += tc.function.arguments

        if pending_tool_calls:
            ordered_calls = [pending_tool_calls[i] for i in sorted(pending_tool_calls.keys())]

            assistant_tool_calls = []
            tool_result_messages = []
            for call in ordered_calls:
                tool_name = call["name"]
                tool_args = call["arguments"]
                tool_id = call["id"] or f"call_{tool_name}"

                if tool_name == "get_current_time":
                    yield "\n[⚙️ AIPet 007 正在偷偷看表...]\n"
                elif tool_name == "web_search":
                    yield "\n[⚙️ AIPet 007 正在疯狂敲键盘上网冲浪查资料...]\n"
                elif tool_name == "open_application":
                    yield f"\n[⚙️ AIPet 007 正在接管鼠标，尝试帮您打开 {tool_args} ...]\n"
                else:
                    yield f"\n[⚙️ AIPet 007 正在使用超能力: {tool_name}...]\n"

                assistant_tool_calls.append(
                    {
                        "id": tool_id,
                        "type": "function",
                        "function": {"name": tool_name, "arguments": tool_args},
                    }
                )

                tool_result = execute_tool(tool_name, tool_args)
                tool_result_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "name": tool_name,
                        "content": tool_result,
                    }
                )

            next_messages = messages + [
                {"role": "assistant", "content": "", "tool_calls": assistant_tool_calls}
            ] + tool_result_messages

            yield from ask_qwen_stream(next_messages, model_name, tool_schemas)
            return
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
