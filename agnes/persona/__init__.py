"""
Persona 系统 - Agnes Agent 的角色定义与行为管理

提供结构化的角色配置，包括：
- 身份定义 (Identity)
- 表达风格 (Stylistics)
- 行为约束 (Constraints)
- 系统提示词生成
"""

from .core import Persona, PersonaIdentity, PersonaStylistics, PersonaConstraints
from .loader import PersonaLoader
from .builder import PromptBuilder

__all__ = [
    "Persona",
    "PersonaIdentity",
    "PersonaStylistics",
    "PersonaConstraints",
    "PersonaLoader",
    "PromptBuilder",
]
