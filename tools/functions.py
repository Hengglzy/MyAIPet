import json
from datetime import datetime

from ddgs import DDGS


def get_current_time(args_dict):
    """获取当前真实时间并返回友好格式字符串。"""
    _ = args_dict  # 当前工具不需要参数，预留统一签名
    return datetime.now().strftime("当前时间是 %Y-%m-%d %H:%M:%S")


GET_CURRENT_TIME_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "获取用户本地当前的真实系统时间和日期。",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


def web_search(args_dict):
    """使用 DuckDuckGo 进行网页搜索并返回摘要"""
    query = args_dict.get("query")
    if not query:
        return "搜索失败：缺少关键词参数(query)"

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        if not results:
            return "未找到相关搜索结果。"

        formatted_results = []
        for idx, res in enumerate(results):
            formatted_results.append(
                f"【结果 {idx + 1}】\n标题: {res.get('title')}\n摘要: {res.get('body')}\n来源: {res.get('href')}"
            )
        return "\n\n".join(formatted_results)
    except Exception as e:
        return f"搜索引擎调用失败: {str(e)}"


WEB_SEARCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "进行全网实时搜索。当用户询问最新新闻、时事、未知概念、实时数据等大模型无法确定的信息时，必须调用此工具获取外部知识。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "要搜索的关键词，请提取用户问题中最核心的搜索词。",
                }
            },
            "required": ["query"],
        },
    },
}


TOOL_REGISTRY = {
    "get_current_time": {
        "func": get_current_time,
        "schema": GET_CURRENT_TIME_SCHEMA,
    },
    "web_search": {
        "func": web_search,
        "schema": WEB_SEARCH_SCHEMA,
    },
}


def get_tool_schemas(tool_names: list):
    """根据工具名列表返回可用于 LLM 调用的 JSON Schema 列表。"""
    schemas = []
    for name in tool_names:
        tool = TOOL_REGISTRY.get(name)
        if tool:
            schemas.append(tool["schema"])
    return schemas


def execute_tool(tool_name: str, arguments: str):
    """解析 JSON 参数并执行指定工具，返回字符串结果。"""
    tool = TOOL_REGISTRY.get(tool_name)
    if not tool:
        return f"工具不存在：{tool_name}"

    try:
        args_dict = json.loads(arguments) if arguments else {}
        if not isinstance(args_dict, dict):
            return "工具参数格式错误：必须是 JSON object。"
    except json.JSONDecodeError:
        return "工具参数解析失败：不是合法 JSON。"

    try:
        result = tool["func"](args_dict)
        return str(result)
    except Exception as e:
        return f"工具执行异常：{str(e)}"
