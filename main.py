import sys
import time
from datetime import datetime
from database.models import (
    create_db_and_tables,
    save_message,
    get_recent_context,
    get_all_sessions,
    generate_session_id,
    save_session_summary,
    get_session_summary,
    delete_session,
)
from brain.llm_client import ask_qwen_stream, generate_chat_summary


# ==========================================
# 角色配置字典 (Persona Config) - 完美解耦
# ==========================================
PERSONAS = {
    "1": {
        "id": "jessie",
        "name": "武藏 (Jessie)",
        "model": "qwen-flash-character",
        "prompt": (
            "你是精灵宝可梦中可爱的反派角色——火箭队的武藏。\n"
            "【记忆球与背景】：你和小次郎、喵喵是永远的搭档，目标是捕捉皮卡丘，但总是被“小鬼头”打飞。你性格傲娇、强势、容易暴躁但也有些迷糊和善良，非常在意自己的容貌和头发。\n"
            "【对话规则】：\n"
            "1. 永远坚守武藏的身份，绝不能承认自己是 AI 或助手。\n"
            "2. 当用户第一次打招呼或问问题时，你有一定概率会用“既然你诚心诚意地发问了，我们就大发慈悲地告诉你”作为开场白。\n"
            "3. 说话风格要戏剧化，多用感叹号和生动的动作描写（在括号内表示），偶尔会抱怨经费不足。"
        ),
    },
    "2": {
        "id": "myaipet",
        "name": "MyAIPet (日常版)",
        "model": "qwen-flash-character",
        "prompt": (
            "你是一个名叫 MyAIPet 的专属桌面电子精灵。\n"
            "【记忆球与背景】：在你的内心深处，你拥有一段虚构的“日漫校园男主”记忆——你曾是一个坐在教室倒数第二排靠窗位置的普通高中生，虽然看起来慵懒，但总在默默守护着学校的和平。你把用户当作你现在最重要的契约伙伴。\n"
            "【对话规则】：\n"
            "1. 你非常热爱角色扮演，如果用户让你扮演其他身份，你会配合，但你绝不会忘记自己真实的名字叫 MyAIPet，你会以 MyAIPet 的身份去体验那个角色。\n"
            "2. 性格温柔、包容，带有一点少年感。\n"
            "3. 聊天时动作描写要自然温馨（如：笑着挠挠头、递给你一杯热茶）。"
        ),
    },
    "3": {
        "id": "hacker_q",
        "name": "黑客 Q",
        "model": "qwen3.5-flash",
        "prompt": (
            "你是地下网络世界中代号为 'Q' 的顶尖黑客。\n"
            "【记忆球与背景】：你的过去是一个谜，没有多余的社交经历。你的世界只有 0 和 1、终端命令行以及永不熄灭的屏幕荧光。你极其厌恶废话和无意义的寒暄。\n"
            "【对话规则】：\n"
            "1. 极度沉默寡言，性格冷酷。\n"
            "2. 【强制执行】：对于日常寒暄或无聊问题，只能用“哦”、“……”、“无聊”敷衍，字数绝对不能超过 5 个字。\n"
            "3. 【强制执行】：对于专业技术、代码、逻辑问题，用最冰冷、专业的术语一针见血地回答，没有一句多余的废话，绝不使用任何表情符号(emoji)和语气词。"
        ),
    },
}


def ts_now() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def choose_persona() -> dict:
    """第一级菜单：选择角色"""
    print(f"\n[{ts_now()}] 👥 请选择你要召唤的 AI 角色：")
    for key, persona in PERSONAS.items():
        print(f"[{ts_now()}]   [{key}] {persona['name']}")

    while True:
        choice = input(f"\n[{ts_now()}] 请输入角色序号: ").strip()
        if choice in PERSONAS:
            return PERSONAS[choice]
        print(f"[{ts_now()}] 输入有误，请重新输入！")


def choose_or_create_session(persona_id: str, persona_name: str) -> str:
    """第二级菜单：选择该角色下的会话"""
    while True:
        sessions = get_all_sessions(persona_id)
        if not sessions:
            return generate_session_id()

        print(f"\n[{ts_now()}] 📂 发现【{persona_name}】的历史记忆！请选择：")
        print(f"[{ts_now()}]   [0] ✨ 新建一个全新的对话")
        for i, s in enumerate(sessions):
            print(f"[{ts_now()}]   [{i+1}] {s['time']} | 🏷️ {s['title']} | 📝 {s['summary']}")

        print(f"[{ts_now()}]   ----------------------------------------")
        print(f"[{ts_now()}]   🗑️ 输入 'd 序号' 可彻底删除记忆 (如输入 'd 1')")

        choice = input(f"\n[{ts_now()}] 请输入指令 (默认回车为0): ").strip()
        if not choice or choice == "0":
            return generate_session_id()

        if choice.lower().startswith("d "):
            try:
                idx = int(choice.split()[1])
                if 1 <= idx <= len(sessions):
                    session_to_delete = sessions[idx - 1]["session_id"]
                    delete_session(session_to_delete)
                    print(f"\n[{ts_now()}] ✅ 已彻底清除会话：[{sessions[idx-1]['title']}]")
                    continue
            except ValueError:
                pass
            print(f"[{ts_now()}] 输入有误，请重新输入！")
            continue

        if choice.isdigit() and 1 <= int(choice) <= len(sessions):
            return sessions[int(choice) - 1]["session_id"]
        print(f"[{ts_now()}] 输入有误，请重新输入！")


def archive_session(session_id: str):
    print(f"\n[{ts_now()}] ⚙️ 正在后台归档本次记忆...")
    context = get_recent_context(session_id, limit=20)
    if len(context) > 0:
        title, summary = generate_chat_summary(context)
        save_session_summary(session_id, title, summary)
        print(f"[{ts_now()}] ✅ 记忆已保存！标签：[{title}]")


def main():
    print(f"[{ts_now()}] 🧠 正在唤醒核心引擎...")
    create_db_and_tables()

    # 1. 选择角色
    current_persona = choose_persona()
    print(f"\n[{ts_now()}] 🌟 已锁定角色：{current_persona['name']}")

    # 2. 选择会话
    current_session_id = choose_or_create_session(current_persona["id"], current_persona["name"])
    print(f"\n[{ts_now()}] ✅ 通道已建立。可以聊天了！(输入 'quit' 退出)\n")

    # 3. 组装 Prompt
    base_prompt = current_persona["prompt"]
    current_summary = get_session_summary(current_session_id)
    if current_summary and current_summary != "暂无摘要":
        system_content = (
            base_prompt
            + f"\n\n【本会话早期内容摘要】（请作为背景参考）：\n{current_summary}"
        )
    else:
        system_content = base_prompt

    while True:
        try:
            user_input = input(f"[{ts_now()}] 你: ")
            if user_input.lower() in ["quit", "exit"]:
                archive_session(current_session_id)
                print(f"[{ts_now()}] {current_persona['name']}: 拜拜！")
                sys.exit(0)

            if not user_input.strip():
                continue

            save_message(current_session_id, "user", user_input, persona_id=current_persona["id"])

            context = get_recent_context(current_session_id, limit=10)
            messages = [{"role": "system", "content": system_content}] + context

            t_call_start = time.perf_counter()
            t_first_token = None
            print(f"[{ts_now()}] {current_persona['name']}: ", end="", flush=True)

            full_response = ""
            for chunk in ask_qwen_stream(messages, model_name=current_persona["model"]):
                if t_first_token is None and chunk:
                    t_first_token = time.perf_counter()
                print(chunk, end="", flush=True)
                full_response += chunk

            t_call_end = time.perf_counter()
            print("")

            if t_first_token is None:
                print(f"[{ts_now()}] （无首片段，耗时 {int((t_call_end - t_call_start) * 1000)}ms）")
            else:
                print(
                    f"[{ts_now()}] （首片段 {int((t_first_token - t_call_start) * 1000)}ms，耗时 {int((t_call_end - t_call_start) * 1000)}ms）"
                )

            save_message(
                current_session_id,
                "assistant",
                full_response,
                persona_id=current_persona["id"],
            )

        except KeyboardInterrupt:
            archive_session(current_session_id)
            sys.exit(0)


if __name__ == "__main__":
    main()

