"""
聊天页面 Schema - 从 JSON 文件加载
"""

import json
from pathlib import Path


def get_chat_schema() -> dict:
    """获取聊天页面 amis Schema"""
    current_dir = Path(__file__).parent
    json_path = current_dir / "chat.json"

    with open(json_path, encoding="utf-8") as f:
        return json.load(f)
