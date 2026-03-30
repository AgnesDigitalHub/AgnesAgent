"""
配置管理模块
"""

from pathlib import Path

from .manager import ConfigManager, LLMProfile
from .settings_storage import DEFAULT_SETTINGS, SETTINGS_SECTIONS, SettingsStorage
from .storage import ConfigStorage


def get_project_root() -> Path:
    """获取项目根目录"""
    # 从当前文件位置向上查找，直到找到项目根目录
    current_file = Path(__file__).resolve()
    # agnes/config/__init__.py -> agnes -> 项目根目录
    return current_file.parent.parent.parent


__all__ = [
    "ConfigManager",
    "ConfigStorage",
    "LLMProfile",
    "SettingsStorage",
    "SETTINGS_SECTIONS",
    "DEFAULT_SETTINGS",
    "get_project_root",
]
