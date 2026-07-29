from langchain_core.tools import tool
from langgraph.prebuilt import ToolRuntime

from app.agent.tool.builtin_tool.memory_save_tool import Context
from app.component.database.postgres_client import PostgresClient


@tool
async def search_knowledge_base(
    query: str,
    runtime: ToolRuntime[Context],
    top_k: int = 5,
) -> str:
    """
    从当前 Agent 关联的知识库中检索相关文档片段。

    使用场景：
    - 用户询问产品说明、文档内容、政策规定等需要依据资料回答的问题
    - 需要引用知识库原文来回答或核对事实时
    - 对专业知识、内部资料不确定时，先检索再回答

    Args:
        query: 检索用的自然语言问题或关键词
        top_k: 返回的最相关片段数量，默认 5，最大 10

    返回：按相关度排序的文本片段；若无结果会明确说明。
    """
    library_ids = [item for item in (runtime.context.library_ids or []) if item]
    if not library_ids:
        return "当前 Agent 未关联任何知识库，无法检索。"

    vector_store = PostgresClient.vector_store
    if vector_store is None:
        return "向量库未初始化，无法检索。"

    k = max(1, min(int(top_k or 5), 10))
    try:
        results = await vector_store.asimilarity_search_with_score(
            query,
            k=k,
            filter={"library_id": {"$in": library_ids}},
        )
    except Exception as exc:
        return f"知识库检索失败: {exc}"

    if not results:
        return "未检索到与问题相关的知识库内容。"

    parts: list[str] = []
    for index, (doc, score) in enumerate(results, start=1):
        meta = doc.metadata or {}
        content = (doc.page_content or "").strip()
        parts.append(
            "\n".join(
                [
                    f"[{index}] distance={float(score):.4f}",
                    f"library_id={meta.get('library_id')}",
                    f"document_id={meta.get('document_id')}",
                    f"chunk_index={meta.get('chunk_index')}",
                    content or "(空内容)",
                ]
            )
        )
    return "\n\n".join(parts)
