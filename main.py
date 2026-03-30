import sys
import time
from datetime import datetime
from database.models import (
    create_db_and_tables, save_message, get_recent_context,
    get_all_sessions, generate_session_id, save_session_summary,
    get_session_summary, delete_session
)
from brain.llm_client import ask_qwen_stream, generate_chat_summary

def ts_now() -> str:
    """当前时间戳，精确到毫秒，用于终端可观测性。"""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def choose_or_create_session() -> str:
    while True:
        sessions = get_all_sessions()
        if not sessions:
            return generate_session_id()

        print(f"\n[{ts_now()}] 📂 发现历史记忆！请选择你要继续的对话：")
        print(f"[{ts_now()}]   [0] ✨ 新建一个全新的对话")
        for i, s in enumerate(sessions):
            print(f"[{ts_now()}]   [{i+1}] {s['time']} | 🏷️ {s['title']} | 📝 {s['summary']}")

        print(f"[{ts_now()}]   ----------------------------------------")
        print(f"[{ts_now()}]   🗑️ 输入 'd 序号' 可彻底删除记忆 (如输入 'd 1')")

        choice = input(f"\n[{ts_now()}] 请输入指令 (默认回车为0): ").strip()
        if not choice or choice == "0":
            return generate_session_id()

        if choice.lower().startswith('d '):
            try:
                idx = int(choice.split()[1])
                if 1 <= idx <= len(sessions):
                    session_to_delete = sessions[idx-1]["session_id"]
                    delete_session(session_to_delete)
                    print(f"\n[{ts_now()}] ✅ 已彻底清除会话：[{sessions[idx-1]['title']}]")
                    continue
            except ValueError:
                pass
            print(f"[{ts_now()}] 输入有误，请重新输入！")
            continue

        if choice.isdigit() and 1 <= int(choice) <= len(sessions):
            return sessions[int(choice)-1]["session_id"]
        print(f"[{ts_now()}] 输入有误，请重新输入！")

def archive_session(session_id: str):
    print(f"\n[{ts_now()}] ⚙️ MyAIPet 正在后台浓缩本次对话记忆...")
    context = get_recent_context(session_id, limit=20)
    if len(context) > 0:
        title, summary = generate_chat_summary(context)
        save_session_summary(session_id, title, summary)
        print(f"[{ts_now()}] ✅ 记忆已保存！标签：[{title}]")

def main():
    print(f"[{ts_now()}] 🧠 正在唤醒 MyAIPet 核心引擎...")
    create_db_and_tables()

    current_session_id = choose_or_create_session()
    print(f"\n[{ts_now()}] ✅ 当前会话通道已建立。")
    print(f"[{ts_now()}] 你可以开始聊天了！(输入 'quit' 或 'exit' 退出并保存记忆)\n")

    base_prompt = "你是一个内置在电脑桌面上的AI生活助手，名字叫 MyAIPet。性格温柔贴心，回答简短自然。"

    current_summary = get_session_summary(current_session_id)
    if current_summary and current_summary != "暂无摘要":
        system_content = base_prompt + f"\n\n【本会话早期内容摘要】（请作为背景参考）：\n{current_summary}"
    else:
        system_content = base_prompt

    while True:
        try:
            user_input = input(f"[{ts_now()}] 你: ")
            if user_input.lower() in ['quit', 'exit']:
                archive_session(current_session_id)
                print(f"[{ts_now()}] MyAIPet: 拜拜，下次见！")
                sys.exit(0)

            if not user_input.strip():
                continue

            save_message(current_session_id, "user", user_input)

            context = get_recent_context(current_session_id, limit=10)
            messages = [{"role": "system", "content": system_content}] + context

            t_call_start = time.perf_counter()
            t_first_token = None
            print(f"[{ts_now()}] MyAIPet: ", end="", flush=True)

            # 接收流式输出并拼接完整回复
            full_response = ""
            for chunk in ask_qwen_stream(messages):
                if t_first_token is None and chunk:
                    t_first_token = time.perf_counter()
                print(chunk, end="", flush=True)
                full_response += chunk
            t_call_end = time.perf_counter()
            print("")
            if t_first_token is None:
                print(f"[{ts_now()}] （无首片段记录，耗时 {int((t_call_end - t_call_start) * 1000)}ms）")
            else:
                print(
                    f"[{ts_now()}] （首片段 {int((t_first_token - t_call_start) * 1000)}ms，耗时 {int((t_call_end - t_call_start) * 1000)}ms）"
                )

            # 将完整回复存入数据库
            save_message(current_session_id, "assistant", full_response)

        except KeyboardInterrupt:
            archive_session(current_session_id)
            sys.exit(0)

if __name__ == "__main__":
    main()
