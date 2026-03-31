import os
from datetime import datetime
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class SessionMeta(SQLModel, table=True):
    session_id: str = Field(primary_key=True)
    persona_id: str = Field(default="default", index=True)  # 【核心新增】
    title: str = Field(default="未命名对话")
    summary: str = Field(default="暂无摘要")
    last_updated: datetime = Field(default_factory=datetime.now)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
engine = create_engine(f"sqlite:///{os.path.join(BASE_DIR, 'memory.db')}", echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def generate_session_id() -> str:
    return datetime.now().strftime("chat_%Y%m%d_%H%M%S")


def get_all_sessions(persona_id: str) -> list[dict]:
    """只查询特定角色的历史会话"""
    with Session(engine) as session:
        statement = (
            select(SessionMeta)
            .where(SessionMeta.persona_id == persona_id)
            .order_by(SessionMeta.last_updated.desc())
        )
        results = session.exec(statement).all()
        return [
            {
                "session_id": r.session_id,
                "title": r.title,
                "summary": r.summary,
                "time": r.last_updated.strftime("%m-%d %H:%M"),
            }
            for r in results
        ]


def get_session_summary(session_id: str) -> str:
    with Session(engine) as session:
        meta = session.get(SessionMeta, session_id)
        return meta.summary if meta else ""


def save_message(session_id: str, role: str, content: str, persona_id: str = "default"):
    """存入消息时，绑定角色身份"""
    with Session(engine) as session:
        msg = Message(session_id=session_id, role=role, content=content)
        session.add(msg)

        meta = session.get(SessionMeta, session_id)
        if not meta:
            meta = SessionMeta(session_id=session_id, persona_id=persona_id)
            session.add(meta)
        else:
            meta.last_updated = datetime.now()

        session.commit()
        return msg


def save_session_summary(session_id: str, title: str, summary: str):
    with Session(engine) as session:
        meta = session.get(SessionMeta, session_id)
        if meta:
            meta.title = title
            meta.summary = summary
            session.add(meta)
            session.commit()


def delete_session(session_id: str):
    with Session(engine) as session:
        messages = session.exec(select(Message).where(Message.session_id == session_id)).all()
        for msg in messages:
            session.delete(msg)

        meta = session.get(SessionMeta, session_id)
        if meta:
            session.delete(meta)
        session.commit()


def get_recent_context(session_id: str, limit: int = 10):
    with Session(engine) as session:
        statement = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.id.desc())
            .limit(limit)
        )
        results = session.exec(statement).all()
        return [{"role": msg.role, "content": msg.content} for msg in results[::-1]]

