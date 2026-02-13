# -*- coding: utf-8 -*-
"""RAG 检索与 LLM 问答链：企业知识库问答核心逻辑。"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, SystemMessage

from config import get_settings
from logger_config import logger
from knowledge import get_vector_store

# 企业场景下的系统提示：优先依据参考文档作答，仅在文档真正无关时才说明无法回答
SYSTEM_PROMPT = """你是企业内部知识库问答助手。请严格依据下面「参考文档」的内容回答问题。

规则：
1. 只要参考文档中有与问题相关的内容（如涉及请假、考勤、制度、流程、天数、审批等），就必须根据该内容直接作答，不要误判为「无法回答」。
2. 仅当参考文档为空或内容与问题完全无关时，才回答：「根据现有知识库无法完整回答该问题」，并建议联系相关部门或补充文档。
3. 回答要简洁、专业。制度、流程、数字等请按文档原文表述，不要擅自改写关键条款。
4. 不要编造文档中不存在的信息；若文档未提及某细节，可说明「文档中未具体说明」。
"""


def _format_docs(docs):
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


_llm_instance = None


def _get_llm():
    """获取 LLM（单例）：若配置了 API 则用 OpenAI 兼容接口，否则返回 None（仅检索模式）。"""
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance
    s = get_settings()
    if not s.llm_api_base or not s.llm_api_key:
        logger.warning("未配置 LLM_API_BASE 或 LLM_API_KEY，将仅返回检索到的文档片段")
        return None
    try:
        from langchain_openai import ChatOpenAI
        _llm_instance = ChatOpenAI(
            base_url=s.llm_api_base,
            api_key=s.llm_api_key,
            model=s.llm_model,
            temperature=s.llm_temperature,
        )
        return _llm_instance
    except Exception as e:
        logger.warning(f"初始化 LLM 失败: {e}")
        return None


def answer_question(question: str, top_k: int | None = None) -> dict:
    """
    基于 RAG 回答一个问题。
    返回: { "answer": str, "sources": list[dict], "retrieved_only": bool }
    """
    s = get_settings()
    k = top_k if top_k is not None else s.top_k
    vector_store = get_vector_store()

    # 检索
    search_kwargs = {"k": k}
    if s.score_threshold is not None:
        search_kwargs["score_threshold"] = s.score_threshold

    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs=search_kwargs)
    docs = retriever.invoke(question)
    context = _format_docs(docs) if docs else "（未检索到相关文档）"
    sources = [{"content": d.page_content[:200] + "..." if len(d.page_content) > 200 else d.page_content, "source": d.metadata.get("source", ""), "filename": d.metadata.get("filename", "")} for d in docs]

    llm = _get_llm()
    if llm is None:
        return {
            "answer": f"当前未配置大模型 API，仅展示检索到的相关内容：\n\n{context}",
            "sources": sources,
            "retrieved_only": True,
        }

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "【参考文档】\n{context}\n\n【用户问题】{question}\n\n请仅根据上述参考文档回答用户问题；若文档中有相关内容请务必归纳后作答。"),
    ])
    chain = (
        {"context": lambda _: context, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    answer = chain.invoke(question)
    return {
        "answer": answer,
        "sources": sources,
        "retrieved_only": False,
    }


def rebuild_index() -> dict:
    """重建向量库索引（从知识库目录重新加载并写入 Chroma）。"""
    from knowledge import build_and_persist_index
    build_and_persist_index()
    return {"status": "ok", "message": "知识库索引已重建"}
