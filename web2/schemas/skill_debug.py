"""
Skill 调试器页面 Schema - 从JSON文件加载，优化代码质量
在线调试本地 Skill 和 YAML 定义的 Skill
"""

import json
from pathlib import Path


def _load_schema():
    """从JSON文件加载schema"""
    schema_file = Path(__file__).parent / "skill_debug.json"
    try:
        with open(schema_file, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[skill_schema] 加载失败: {e}")
        return {}


def get_skill_debug_schema() -> dict:
    """获取 Skill 调试器页面 amis Schema"""
    return _load_schema()
