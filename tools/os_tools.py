import os
import json
import platform
import subprocess
from pathlib import Path

# 【核心升级】：动态获取项目根目录，锚定配置文件位置
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "apps_config.json"


def load_apps_config():
    """动态读取或初始化软件配置文件"""
    if not CONFIG_PATH.exists():
        default_config = {
            "wechat": "weixin://",
            "微信": "weixin://",
            "qq": "tencent://message/",
            "网易云音乐": "orpheus://",
            "chrome": "chrome",
            "edge": "msedge",
            "记事本": "notepad",
            "计算器": "calc",
            "画图": "mspaint",
        }
        with open(str(CONFIG_PATH), "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)
        return default_config

    with open(str(CONFIG_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def open_application(args_dict):
    """智能打开软件的核心逻辑"""
    app_name = args_dict.get("app_name", "").lower()
    if not app_name:
        return "执行失败：未提供软件名称"

    try:
        if platform.system() != "Windows":
            return "当前操作系统暂不支持此命令。"

        apps_map = load_apps_config()
        target_path = None

        for key, path in apps_map.items():
            if key in app_name or app_name in key:
                target_path = path
                break

        if not target_path:
            return (
                f"执行失败。请原话回复用户：'抱歉，我还没在配置表里找到【{app_name}】的路径呢。你可以打开项目根目录的 apps_config.json 教我一下吗？'"
            )

        if "://" in target_path or ("\\" not in target_path and "/" not in target_path):
            os.system(f'start "" "{target_path}"')
        else:
            subprocess.Popen(target_path)

        return f"成功：已为您尝试唤起 {app_name}。"

    except Exception as e:
        return f"打开软件发生异常: {str(e)}"


OPEN_APPLICATION_SCHEMA = {
    "type": "function",
    "function": {
        "name": "open_application",
        "description": "打开电脑上的本地应用程序（如：微信、QQ、浏览器、记事本等）。",
        "parameters": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "用户想要打开的软件名称或拼音。",
                }
            },
            "required": ["app_name"],
        },
    },
}
