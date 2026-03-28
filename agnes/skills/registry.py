"""
Skill 注册表（Registry）
统一存储所有可用技能的 schema，支持动态加载和版本管理
"""

import logging
from typing import Any

from agnes.skills.base import BaseSkill, SkillSchema

logger = logging.getLogger(__name__)


class SkillRegistry:
    """Skill 注册表，管理所有已注册的 Skill"""

    def __init__(self):
        self._skills: dict[str, BaseSkill] = {}
        # 版本管理: skill_name -> List[(version, skill)]
        self._versions: dict[str, list[tuple[str, BaseSkill]]] = {}
        # 统计信息
        self._call_count: dict[str, int] = {}
        self._success_count: dict[str, int] = {}
        self._total_execution_time: dict[str, float] = {}
        self._error_stats: dict[str, dict[str, int]] = {}

    def register(self, skill: BaseSkill) -> None:
        """注册一个新 Skill"""
        name = skill.name
        metadata = skill.get_metadata()
        version = metadata.version

        # 如果已存在同名 Skill，检查版本
        if name in self._skills:
            existing = self._skills[name]
            existing_version = existing.get_metadata().version
            logger.warning(f"Skill '{name}' already registered (v{existing_version}), overwriting with v{version}")

        # 注册
        self._skills[name] = skill

        # 保存版本历史
        if name not in self._versions:
            self._versions[name] = []
        self._versions[name].append((version, skill))

        # 初始化统计
        if name not in self._call_count:
            self._call_count[name] = 0
            self._success_count[name] = 0
            self._total_execution_time[name] = 0.0
            self._error_stats[name] = {}

        logger.info(f"Registered skill: {name} v{version}")

    def unregister(self, name: str) -> bool:
        """注销一个 Skill"""
        if name not in self._skills:
            return False

        del self._skills[name]
        # 版本历史保留，但不再对外可见
        logger.info(f"Unregistered skill: {name}")
        return True

    def get(self, name: str) -> BaseSkill | None:
        """获取当前激活版本的 Skill"""
        return self._skills.get(name)

    def get_version(self, name: str, version: str) -> BaseSkill | None:
        """获取特定版本的 Skill"""
        if name not in self._versions:
            return None
        for v, skill in self._versions[name]:
            if v == version:
                return skill
        return None

    def list_skills(self) -> list[BaseSkill]:
        """列出所有当前激活的 Skill"""
        return list(self._skills.values())

    def list_versions(self, name: str) -> list[str]:
        """列出某个 Skill 的所有可用版本"""
        if name not in self._versions:
            return []
        return [v for v, _ in self._versions[name]]

    def get_all_schemas(self) -> list[SkillSchema]:
        """获取所有 Skill 的 Schema 列表，用于 Function Calling"""
        return [skill.get_schema() for skill in self._skills.values()]

    def get_all_openai_functions(self) -> list[dict[str, Any]]:
        """获取 OpenAI Function Calling 格式的工具定义"""
        functions = []
        for skill in self._skills.values():
            schema = skill.get_schema()
            function_def = {
                "type": "function",
                "function": {
                    "name": schema.name,
                    "description": schema.description,
                    "parameters": {"type": "object", "properties": schema.parameters, "required": schema.required},
                },
            }
            functions.append(function_def)
        return functions

    def get_stats(self, name: str) -> dict[str, Any] | None:
        """获取某个 Skill 的统计信息"""
        if name not in self._call_count:
            return None

        total_calls = self._call_count[name]
        success = self._success_count[name]
        total_time = self._total_execution_time[name]

        avg_time = total_time / total_calls if total_calls > 0 else 0.0
        success_rate = success / total_calls if total_calls > 0 else 0.0

        return {
            "name": name,
            "total_calls": total_calls,
            "success_count": success,
            "success_rate": success_rate,
            "average_execution_time_ms": avg_time,
            "total_execution_time_ms": total_time,
            "error_stats": self._error_stats[name].copy(),
        }

    def record_call(self, name: str, success: bool, execution_time_ms: float, error_type: str | None = None) -> None:
        """记录一次调用，用于统计"""
        if name not in self._call_count:
            self._call_count[name] = 0
            self._success_count[name] = 0
            self._total_execution_time[name] = 0.0
            self._error_stats[name] = {}

        self._call_count[name] += 1
        self._total_execution_time[name] += execution_time_ms

        if success:
            self._success_count[name] += 1
        elif error_type:
            self._error_stats[name][error_type] = self._error_stats[name].get(error_type, 0) + 1

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """获取所有 Skill 的统计信息"""
        return {name: self.get_stats(name) for name in self._skills.keys() if name in self._call_count}

    def clear_stats(self, name: str | None = None) -> None:
        """清空统计信息"""
        if name:
            if name in self._call_count:
                self._call_count[name] = 0
                self._success_count[name] = 0
                self._total_execution_time[name] = 0.0
                self._error_stats[name] = {}
        else:
            for name in self._call_count:
                self._call_count[name] = 0
                self._success_count[name] = 0
                self._total_execution_time[name] = 0.0
                self._error_stats[name] = {}

    @property
    def count(self) -> int:
        """获取当前注册的 Skill 数量"""
        return len(self._skills)


# 全局单例
registry = SkillRegistry()
