"""
Persona 加载器

支持从 YAML、JSON、Markdown 加载角色定义
"""

import json
import re
import uuid
from pathlib import Path
from typing import Any

import yaml

from agnes.persona.core import Persona, PersonaConstraints, PersonaIdentity, PersonaStylistics
from agnes.utils.logger import get_logger

logger = get_logger("agnes.persona")


class PersonaLoader:
    """
    Persona 加载器

    支持多种格式：
    - YAML (.yaml, .yml)
    - JSON (.json)
    - Markdown with YAML frontmatter (.md)
    """

    @classmethod
    def from_file(cls, file_path: str | Path) -> Persona:
        """
        从文件加载 Persona

        Args:
            file_path: 文件路径

        Returns:
            Persona: 角色定义
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Persona file not found: {file_path}")

        suffix = path.suffix.lower()

        if suffix in (".yaml", ".yml"):
            return cls.from_yaml(path)
        elif suffix == ".json":
            return cls.from_json(path)
        elif suffix == ".md":
            return cls.from_markdown(path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> Persona:
        """从 YAML 文件加载"""
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls._parse_data(data, str(yaml_path))

    @classmethod
    def from_json(cls, json_path: str | Path) -> Persona:
        """从 JSON 文件加载"""
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        return cls._parse_data(data, str(json_path))

    @classmethod
    def from_markdown(cls, md_path: str | Path) -> Persona:
        """
        从 Markdown 文件加载

        支持 YAML frontmatter 格式：
        ---
        name: xxx
        ...
        ---
        正文内容作为 system_prompt
        """
        with open(md_path, encoding="utf-8") as f:
            content = f.read()

        return cls.from_markdown_content(content, str(md_path))

    @classmethod
    def from_markdown_content(cls, content: str, source: str = "") -> Persona:
        """从 Markdown 内容解析"""
        # 匹配 YAML frontmatter
        frontmatter_pattern = r"^---\s*$(.*?)^---\s*$"
        match = re.search(frontmatter_pattern, content, re.MULTILINE | re.DOTALL)

        data: dict[str, Any] = {}
        content_start = 0

        if match:
            try:
                yaml_content = match.group(1)
                front_data = yaml.safe_load(yaml_content)
                if front_data and isinstance(front_data, dict):
                    data = front_data
                content_start = match.end()
            except Exception:
                pass

        # 提取剩余内容作为 custom_system_prompt
        system_prompt = content[content_start:].strip()
        if system_prompt:
            data["custom_system_prompt"] = system_prompt

        # 从 source 提取 id
        if source:
            data["id"] = data.get("id", Path(source).stem)

        return cls._parse_data(data, source)

    @classmethod
    def _parse_data(cls, data: dict[str, Any], source: str = "") -> Persona:
        """解析数据字典为 Persona"""
        # 处理旧格式兼容
        data = cls._migrate_old_format(data)

        # 确保 id 存在
        if "id" not in data:
            data["id"] = str(uuid.uuid4())

        # 解析子结构
        identity_data = data.get("identity", {})
        if isinstance(identity_data, dict):
            identity = PersonaIdentity.from_dict(identity_data)
        else:
            identity = PersonaIdentity()

        stylistics_data = data.get("stylistics", {})
        if isinstance(stylistics_data, dict):
            stylistics = PersonaStylistics.from_dict(stylistics_data)
        else:
            stylistics = PersonaStylistics()

        constraints_data = data.get("constraints", {})
        if isinstance(constraints_data, dict):
            constraints = PersonaConstraints.from_dict(constraints_data)
        else:
            constraints = PersonaConstraints()

        return Persona(
            id=data["id"],
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", []),
            identity=identity,
            stylistics=stylistics,
            constraints=constraints,
            custom_system_prompt=data.get("custom_system_prompt", ""),
            llm_profile_id=data.get("llm_profile_id"),
            mcp_servers=data.get("mcp_servers", []),
            skills=data.get("skills", []),
            enabled=data.get("enabled", True),
            metadata={"source": source, **data.get("metadata", {})},
        )

    @classmethod
    def _migrate_old_format(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        迁移旧格式数据

        兼容 web2/persona.py 中的旧格式
        """
        result = data.copy()

        # 旧格式：full_name -> name
        if "full_name" in result and "name" not in result:
            result["name"] = result["full_name"]

        # 旧格式：bio -> description
        if "bio" in result and "description" not in result:
            result["description"] = result["bio"]

        # 旧格式：identity 是字符串
        if "identity" in result and isinstance(result["identity"], str):
            result["identity"] = {"bio": result["identity"]}

        # 旧格式：forbidden_behaviors -> constraints.forbidden_behaviors
        if "forbidden_behaviors" in result and "constraints" not in result:
            result["constraints"] = {"forbidden_behaviors": result["forbidden_behaviors"]}

        # 旧格式：system_prompt -> custom_system_prompt
        if "system_prompt" in result and "custom_system_prompt" not in result:
            result["custom_system_prompt"] = result["system_prompt"]

        return result

    @classmethod
    def save_to_yaml(cls, persona: Persona, yaml_path: str | Path) -> None:
        """保存到 YAML 文件"""
        path = Path(yaml_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(persona.to_dict(), f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    @classmethod
    def save_to_json(cls, persona: Persona, json_path: str | Path) -> None:
        """保存到 JSON 文件"""
        path = Path(json_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(persona.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def save_to_markdown(cls, persona: Persona, md_path: str | Path) -> None:
        """保存到 Markdown 文件（带 YAML frontmatter）"""
        path = Path(md_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = persona.to_dict()
        custom_prompt = data.pop("custom_system_prompt", "")

        with open(path, "w", encoding="utf-8") as f:
            f.write("---\n")
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            f.write("---\n\n")
            if custom_prompt:
                f.write(custom_prompt)

    @classmethod
    def load_all_from_directory(cls, directory: str | Path) -> list[Persona]:
        """
        从目录加载所有 Persona

        Args:
            directory: 目录路径

        Returns:
            list[Persona]: 角色列表
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return []

        personas = []
        for file_path in dir_path.iterdir():
            if file_path.suffix.lower() in (".yaml", ".yml", ".json", ".md"):
                try:
                    persona = cls.from_file(file_path)
                    personas.append(persona)
                except Exception as e:
                    logger.error(f"Failed to load {file_path}: {e}")

        return personas
