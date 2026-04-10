"""
Agent 管理页面 schema
从JSON文件加载，优化代码质量
"""

import json
from pathlib import Path

from agnes.utils.logger import get_logger

logger = get_logger("agnes.schemas")


def _load_schema():
    """从JSON文件加载schema"""
    schema_file = Path(__file__).parent / "agents.json"
    try:
        with open(schema_file, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[agents_schema] 加载失败: {e}")
        return {}


def get_agents_schema() -> dict:
    """获取 Agent 管理页面 schema"""
    return _load_schema()
