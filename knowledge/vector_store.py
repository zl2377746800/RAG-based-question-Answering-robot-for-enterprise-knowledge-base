# -*- coding: utf-8 -*-
"""向量存储：使用 Chroma + 本地 Embedding，支持持久化与检索。"""
import warnings
from pathlib import Path
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import get_settings, get_chroma_path, get_knowledge_path
from logger_config import logger
from .loader import load_documents_from_directory

# 单例缓存：进程内只加载一次嵌入模型与向量库，避免每次请求重复加载
_embeddings_instance = None
_vector_store_instance = None


def _get_embeddings():
    """获取本地 HuggingFace 嵌入模型（单例，仅加载一次）。"""
    global _embeddings_instance
    if _embeddings_instance is not None:
        return _embeddings_instance
    s = get_settings()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        try:
            from langchain_huggingface.embeddings import HuggingFaceEmbeddings
        except ImportError:
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
            except ImportError:
                from langchain_community.embeddings import HuggingFaceEmbeddings
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=s.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    logger.info("嵌入模型已加载（仅此一次）")
    return _embeddings_instance


def _get_text_splitter():
    s = get_settings()
    return RecursiveCharacterTextSplitter(
        chunk_size=s.chunk_size,
        chunk_overlap=s.chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
    )


def get_vector_store(allow_create: bool = True) -> Chroma:
    """
    获取或创建 Chroma 向量库（单例缓存，进程内复用）。
    allow_create: 若持久化目录不存在是否从知识库重建索引。
    """
    global _vector_store_instance
    if _vector_store_instance is not None:
        return _vector_store_instance

    persist_dir = get_chroma_path()
    embeddings = _get_embeddings()
    collection_name = "enterprise_knowledge"

    if (persist_dir / "chroma.sqlite3").exists():
        _vector_store_instance = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(persist_dir),
        )
        logger.info(f"已加载已有向量库: {persist_dir}")
        return _vector_store_instance

    if allow_create:
        logger.info("未发现已有向量库，将从头构建索引")
        _vector_store_instance = build_and_persist_index()
        return _vector_store_instance

    _vector_store_instance = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(persist_dir),
    )
    return _vector_store_instance


def build_and_persist_index(docs: list[Document] | None = None) -> Chroma:
    """
    从知识库目录加载文档、切分、向量化并持久化到 Chroma。
    若未传入 docs，则从配置的 knowledge_base_path 加载。
    重建后会更新全局向量库单例。
    """
    global _vector_store_instance
    if docs is None:
        knowledge_path = get_knowledge_path()
        docs = load_documents_from_directory(knowledge_path)
    if not docs:
        logger.warning("没有可索引的文档，请检查 knowledge_docs 下是否有 .pdf/.txt/.md/.docx 且加载无报错")
        persist_dir = get_chroma_path()
        persist_dir.mkdir(parents=True, exist_ok=True)
        embeddings = _get_embeddings()
        collection_name = "enterprise_knowledge"
        # Chroma 不接受空文档列表，改为创建空库并复用
        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(persist_dir),
        )
        _vector_store_instance = vector_store
        return vector_store

    splitter = _get_text_splitter()
    splits = splitter.split_documents(docs)
    logger.info(f"切分后共 {len(splits)} 个文本块")

    persist_dir = get_chroma_path()
    persist_dir.mkdir(parents=True, exist_ok=True)
    embeddings = _get_embeddings()
    collection_name = "enterprise_knowledge"

    vector_store = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=str(persist_dir),
    )
    logger.info(f"向量库已构建并持久化到 {persist_dir}")
    _vector_store_instance = vector_store
    return vector_store
