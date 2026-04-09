"""
Agent 管理页面 schema
从JSON文件加载，优化代码质量
"""

import json
from pathlib import Path


def _load_schema():
    """从JSON文件加载schema"""
    schema_file = Path(__file__).parent / "agents.json"
    try:
        with open(schema_file, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[agents_schema] 加载失败: {e}")
        return {}


def get_agents_schema() -> dict:
    """获取 Agent 管理页面 schema"""
    return _load_schema()
