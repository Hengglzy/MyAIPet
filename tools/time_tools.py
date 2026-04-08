from datetime import datetime


def get_current_time(args_dict):
    _ = args_dict
    return datetime.now().strftime("当前时间是 %Y-%m-%d %H:%M:%S")


GET_CURRENT_TIME_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "获取用户本地当前的真实系统时间和日期。",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}
