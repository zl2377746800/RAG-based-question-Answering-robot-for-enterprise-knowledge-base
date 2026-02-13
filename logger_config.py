# -*- coding: utf-8 -*-
"""统一日志配置，便于企业环境排查问题。"""
import sys
from pathlib import Path
from loguru import logger

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 移除默认 handler，避免重复
logger.remove()

# 控制台：简洁格式
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO",
)

# 文件：按天轮转，保留 7 天
logger.add(
    LOG_DIR / "rag_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="7 days",
    encoding="utf-8",
    level="DEBUG",
)

__all__ = ["logger"]
