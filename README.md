# MyAIPet

纯 Python 的 AI 桌宠后端雏形：本地 SQLite（SQLModel）存消息与会话元数据，DashScope 千问兼容接口（OpenAI SDK）负责对话与归档摘要；终端 `main.py` 为临时控制器，便于后续接 PyQt。

## 环境

- Python 3.13+（与 `pyproject.toml` 一致）
- 依赖管理：[uv](https://github.com/astral-sh/uv)

## 配置

1. 项目根目录复制或编辑 `.env`：

   ```env
   DASHSCOPE_API_KEY=你的阿里云百炼/灵积 DashScope Key
   ```

2. 数据库：`memory.db` 自动生成于项目根目录（已在 `.gitignore` 中忽略）。

## 运行

```bash
py -m uv run python main.py
```

启动后会话选择：`0` 新建、`1..n` 继续历史会话、`d 序号` 删除某会话；输入 `quit` / `exit` 退出时会自动调用模型生成标题与摘要并写入会话表。

## 模块职责

| 目录/文件 | 说明 |
|-----------|------|
| `database/models.py` | 数据层：`Message`、`SessionMeta`，会话 CRUD 与近期上下文 |
| `brain/llm_client.py` | 逻辑层：API Key 校验、流式对话、会话摘要生成 |
| `main.py` | 临时终端入口：会话选择与聊天循环 |
