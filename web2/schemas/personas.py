"""
结构化人格管理页面 schema
从JSON文件加载
"""

import json
from pathlib import Path

from agnes.utils.logger import get_logger

logger = get_logger("agnes.schemas")


def _load_schema():
    """从JSON文件加载schema"""
    schema_file = Path(__file__).parent / "personas.json"
    try:
        with open(schema_file, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[personas_schema] 加载失败: {e}")
        return {}


def get_personas_schema() -> dict:
    """获取人格管理页面 schema"""
    return _load_schema()
