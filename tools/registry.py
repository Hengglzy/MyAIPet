import json

from .os_tools import OPEN_APPLICATION_SCHEMA, open_application
from .time_tools import GET_CURRENT_TIME_SCHEMA, get_current_time
from .web_tools import WEB_SEARCH_SCHEMA, web_search

TOOL_REGISTRY = {
    "get_current_time": {"func": get_current_time, "schema": GET_CURRENT_TIME_SCHEMA},
    "web_search": {"func": web_search, "schema": WEB_SEARCH_SCHEMA},
    "open_application": {"func": open_application, "schema": OPEN_APPLICATION_SCHEMA},
}


def get_tool_schemas(tool_names: list):
    return [TOOL_REGISTRY[name]["schema"] for name in tool_names if name in TOOL_REGISTRY]


def execute_tool(tool_name: str, arguments: str):
    tool = TOOL_REGISTRY.get(tool_name)
    if not tool:
        return f"工具不存在：{tool_name}"
    try:
        args_dict = json.loads(arguments) if arguments else {}
        return str(tool["func"](args_dict))
    except Exception as e:
        return f"工具执行异常：{str(e)}"
