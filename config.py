# -*- coding: utf-8 -*-
"""企业知识库 RAG 应用配置（环境变量 + 默认值）。"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """从环境变量与 .env 加载配置。"""

    # 知识库路径
    knowledge_base_path: str = Field(
        default="knowledge_docs",
        description="知识库文档所在目录（相对项目根）",
    )
    persist_directory: str = Field(
        default="chroma_db",
        description="Chroma 向量库持久化目录",
    )

    # 嵌入模型（本地 sentence-transformers，无需 API Key）
    embedding_model: str = Field(
        default="paraphrase-multilingual-MiniLM-L12-v2",
        description="本地嵌入模型名称",
    )

    # LLM 配置（可选：OpenAI 兼容 API）
    llm_api_base: str | None = Field(default=None, description="LLM API 基地址，如 https://api.openai.com/v1")
    llm_api_key: str | None = Field(default=None, description="LLM API Key")
    llm_model: str = Field(default="gpt-4o-mini", description="调用的模型名")
    llm_temperature: float = Field(default=0.2, ge=0, le=2, description="生成温度")

    # RAG 参数
    chunk_size: int = Field(default=500, ge=100, le=2000, description="文本块大小")
    chunk_overlap: int = Field(default=80, ge=0, le=500, description="块重叠长度")
    top_k: int = Field(default=8, ge=1, le=20, description="检索返回的文档数量")
    score_threshold: float | None = Field(default=None, ge=0, le=1, description="相似度阈值，None 表示不过滤")

    # 服务
    host: str = Field(default="0.0.0.0", description="API 监听地址")
    port: int = Field(default=8000, ge=1, le=65535, description="API 端口")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


def get_settings() -> Settings:
    return Settings()


def get_knowledge_path() -> Path:
    s = get_settings()
    p = PROJECT_ROOT / s.knowledge_base_path
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_chroma_path() -> Path:
    s = get_settings()
    return PROJECT_ROOT / s.persist_directory
