from ddgs import DDGS


def web_search(args_dict):
    query = args_dict.get("query")
    if not query:
        return "搜索失败：缺少关键词参数"
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        if not results:
            return "未找到相关搜索结果。"
        return "\n\n".join(
            [f"标题: {res.get('title')}\n摘要: {res.get('body')}" for res in results]
        )
    except Exception as e:
        return f"搜索引擎调用失败: {str(e)}"


WEB_SEARCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "进行全网实时搜索。当用户询问未知概念、新闻、天气等外部信息时必须调用。",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "搜索关键词"}},
            "required": ["query"],
        },
    },
}
