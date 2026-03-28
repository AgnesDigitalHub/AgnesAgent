"""
Skills - Agent 技能系统
每个 Skill 封装一个原子能力，Agent 通过 Function Calling 调用它们
"""

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
