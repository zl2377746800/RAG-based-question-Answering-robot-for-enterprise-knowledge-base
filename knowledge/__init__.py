# -*- coding: utf-8 -*-
"""知识库模块：文档加载、切分、向量存储与检索。"""
from .loader import load_documents_from_directory
from .vector_store import get_vector_store, build_and_persist_index

__all__ = [
    "load_documents_from_directory",
    "get_vector_store",
    "build_and_persist_index",
]
