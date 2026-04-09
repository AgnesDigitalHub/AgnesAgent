"""
Skills - Agent 技能系统
每个 Skill 封装一个原子能力，Agent 通过 Function Calling 调用它们
"""

# 自动导入所有内置技能
# 这些技能会自动注册到全局注册表
# 使用 try-except 处理可选依赖缺失的情况
import agnes.skills.action  # noqa: F401
import agnes.skills.system  # noqa: F401
from agnes.skills.base import BaseSkill, SkillResult, SkillSchema
from agnes.skills.engine import SkillCallEngine
from agnes.skills.registry import SkillRegistry, registry
from agnes.skills.yaml_loader import (
    YAMLLoadResult,
    YAMLSkillDefinition,
    YAMLSkillLoader,
    get_yaml_loader,
    load_and_register_all,
)

try:
    import agnes.skills.perception  # noqa: F401
except ImportError:
    # perception 需要 gameautomation 可选依赖
    pass

__all__ = [
    "BaseSkill",
    "SkillResult",
    "SkillSchema",
    "SkillRegistry",
    "SkillCallEngine",
    "YAMLSkillLoader",
    "YAMLSkillDefinition",
    "YAMLLoadResult",
    "registry",
    "get_yaml_loader",
    "load_and_register_all",
]
