"""
模型管理页面 Schema - 从JSON文件加载，优化代码质量
"""

import json
from pathlib import Path

from agnes.utils.logger import get_logger

logger = get_logger("agnes.schemas")


def _load_schema():
    """从JSON文件加载schema"""
    schema_file = Path(__file__).parent / "models.json"
    try:
        with open(schema_file, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[models_schema] 加载失败: {e}")
        return {}


def get_models_schema() -> dict:
    """获取模型管理页面 amis Schema"""
    return _load_schema()
