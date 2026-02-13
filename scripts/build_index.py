# -*- coding: utf-8 -*-
"""一键重建知识库向量索引（可将此脚本加入定时任务或 CI）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from logger_config import logger
from knowledge import build_and_persist_index

if __name__ == "__main__":
    logger.info("开始重建知识库索引…")
    build_and_persist_index()
    logger.info("索引重建完成。")
