import sys
import time
from datetime import datetime
from database.models import create_db_and_tables, save_message, get_recent_context
from brain.llm_client import ask_qwen_stream

# 设定系统初始人设
SYSTEM_PROMPT = {
    "role": "system",
    "content": "你是一个内置在电脑桌面上的AI生活助手，名字叫 MyAIPet。你的性格温柔细心，非常贴心，回答尽量简短自然。"
}


def main():
    print("========================================")
    print(" 🧠 正在唤醒 MyAIPet 核心引擎...")

    # 1. 初始化数据库（安全操作，已有则跳过）
    create_db_and_tables()
    print(" 💾 海马体（记忆系统）加载完毕。")
    print(" 🚀 大脑（qwen3.5-plus）连接就绪。")
    print("========================================")
    print("你可以开始聊天了！(输入 'quit' 或 'exit' 退出)\n")

    while True:
        # 时间戳格式：精确到毫秒
        def ts_now() -> str:
            return datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # 接收用户输入（在“你:”前加时间戳）
        user_input = input(f"[{ts_now()}] 你: ")

        # 退出指令
        if user_input.lower() in ['quit', 'exit']:
            print("MyAIPet: 拜拜，下次见！")
            sys.exit(0)

        if not user_input.strip():
            continue

        # 2. 将用户的发言存入数据库
        save_message("user", user_input)

        # 3. 从数据库捞出最近的 10 条上下文
        context = get_recent_context(limit=10)

        # 4. 组装终极 Prompt：系统人设 + 历史记忆
        messages = [SYSTEM_PROMPT] + context

        # 5. 调用大模型思考（流式输出，像打字机一样逐步显示）
        t_call_start = time.perf_counter()
        t_first_token = None

        # 在“MyAIPet”前加时间戳
        print(f"[{ts_now()}] MyAIPet: ", end="", flush=True)

        response_parts = []
        for chunk in ask_qwen_stream(messages):
            response_parts.append(chunk)
            if t_first_token is None and chunk:
                t_first_token = time.perf_counter()
            # 将每个 chunk 拆成字符逐个输出，制造打字机观感
            for ch in chunk:
                print(ch, end="", flush=True)
        ai_response = "".join(response_parts).strip()

        # 换行，结束本轮流式输出
        t_call_end = time.perf_counter()
        if t_first_token is None:
            print(f"\n（耗时 {int((t_call_end - t_call_start) * 1000)}ms，无首 token 记录）")
        else:
            print(
                f"\n（首 token {int((t_first_token - t_call_start) * 1000)}ms，耗时 {int((t_call_end - t_call_start) * 1000)}ms）"
            )

        # 6. 将 AI 的回复也存入数据库
        save_message("assistant", ai_response)


if __name__ == "__main__":
    main()
