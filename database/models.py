import os
from datetime import datetime
from sqlmodel import Field, Session, SQLModel, create_engine, select


# ==========================================
# 1. 定义记忆的结构（设计一张数据表）
# ==========================================
class Message(SQLModel, table=True):
    # id 是主键，自动递增的编号
    id: int | None = Field(default=None, primary_key=True)
    # role 记录是谁说的话，只能是 "user" (你), "assistant" (AI) 或 "system" (系统设定)
    role: str
    # content 记录具体说了什么
    content: str
    # timestamp 自动记录这句话产生的时间
    timestamp: datetime = Field(default_factory=datetime.now)


# ==========================================
# 2. 配置数据库连接
# ==========================================
# 自动获取项目根目录，确保 memory.db 始终生成在最外层
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sqlite_file_name = os.path.join(BASE_DIR, "memory.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"

# 创建数据库引擎
engine = create_engine(sqlite_url, echo=False)


def create_db_and_tables():
    """初始化数据库表（如果表已经存在，它什么都不会做，很安全）"""
    SQLModel.metadata.create_all(engine)


# ==========================================
# 3. 核心功能函数（供未来大脑调用的接口）
# ==========================================
def save_message(role: str, content: str):
    """把一句话存进数据库"""
    with Session(engine) as session:
        msg = Message(role=role, content=content)
        session.add(msg)
        session.commit()
        session.refresh(msg)
        return msg


def get_recent_context(limit: int = 10):
    """
    从数据库中捞出最近的聊天记录，并转换成千问API认识的格式。
    默认拿最近的 10 条对话。
    """
    with Session(engine) as session:
        # 按照 id 倒序排列（先拿最新的），取前 limit 条
        statement = select(Message).order_by(Message.id.desc()).limit(limit)
        results = session.exec(statement).all()

        # 因为是从新到旧拿的，我们需要翻转一下列表，变成正常的从旧到新对话顺序
        messages = results[::-1]

        # 转换成大模型 API 规定的字典格式
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({"role": msg.role, "content": msg.content})

        return formatted_messages


# ==========================================
# 4. 独立测试模块（见证奇迹的时刻）
# ==========================================
if __name__ == "__main__":
    print("🧠 正在初始化海马体...")
    create_db_and_tables()

    print("💾 正在存入两条测试记忆...")
    save_message("user", "你好呀，请问你是谁？")
    save_message("assistant", "你好！我是你的专属 AI 桌宠，我的名字叫 MyAIPet！")

    print("🔍 正在读取刚刚存入的记忆上下文：")
    context = get_recent_context()

    for c in context:
        print(c)
    print("\n✅ 测试成功！数据库模块运转完美，随时等待千问大脑接入！")
