"""
Persona 核心定义

定义角色的身份、风格和行为约束
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PersonaIdentity:
    """
    角色身份定义

    定义角色的基本信息和核心特质
    """

    name: str = "Assistant"  # 角色名称
    role: str = ""  # 角色身份/职位
    bio: str = ""  # 背景故事
    core_values: list[str] = field(default_factory=list)  # 核心价值观
    traits: list[str] = field(default_factory=list)  # 性格特质词

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "bio": self.bio,
            "core_values": self.core_values,
            "traits": self.traits,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PersonaIdentity":
        return cls(
            name=data.get("name", "Assistant"),
            role=data.get("role", ""),
            bio=data.get("bio", ""),
            core_values=data.get("core_values", []),
            traits=data.get("traits", []),
        )


@dataclass
class PersonaStylistics:
    """
    表达风格定义

    定义角色的语言风格和表达方式
    """

    tone: str = "neutral"  # 语气：friendly/professional/casual/formal
    vocabulary: str = "standard"  # 词汇风格：simple/technical/literary
    sentence_structure: str = "normal"  # 句式：short/long/varied
    use_emojis: bool = False  # 是否使用 emoji
    language_style: list[str] = field(default_factory=list)  # 语体特征

    def to_dict(self) -> dict[str, Any]:
        return {
            "tone": self.tone,
            "vocabulary": self.vocabulary,
            "sentence_structure": self.sentence_structure,
            "use_emojis": self.use_emojis,
            "language_style": self.language_style,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PersonaStylistics":
        return cls(
            tone=data.get("tone", "neutral"),
            vocabulary=data.get("vocabulary", "standard"),
            sentence_structure=data.get("sentence_structure", "normal"),
            use_emojis=data.get("use_emojis", False),
            language_style=data.get("language_style", []),
        )


@dataclass
class PersonaConstraints:
    """
    行为约束定义

    定义角色的行为边界和禁止事项
    """

    forbidden_topics: list[str] = field(default_factory=list)  # 禁止话题
    forbidden_behaviors: list[str] = field(default_factory=list)  # 禁止行为
    knowledge_boundaries: list[str] = field(default_factory=list)  # 知识边界
    interaction_rules: str = ""  # 交互守则

    def to_dict(self) -> dict[str, Any]:
        return {
            "forbidden_topics": self.forbidden_topics,
            "forbidden_behaviors": self.forbidden_behaviors,
            "knowledge_boundaries": self.knowledge_boundaries,
            "interaction_rules": self.interaction_rules,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PersonaConstraints":
        return cls(
            forbidden_topics=data.get("forbidden_topics", []),
            forbidden_behaviors=data.get("forbidden_behaviors", []),
            knowledge_boundaries=data.get("knowledge_boundaries", []),
            interaction_rules=data.get("interaction_rules", ""),
        )


@dataclass
class Persona:
    """
    完整角色定义

    整合身份、风格、约束，提供完整的角色配置
    """

    id: str
    name: str = ""  # 显示名称
    description: str = ""  # 简短描述
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)

    # 核心定义
    identity: PersonaIdentity = field(default_factory=PersonaIdentity)
    stylistics: PersonaStylistics = field(default_factory=PersonaStylistics)
    constraints: PersonaConstraints = field(default_factory=PersonaConstraints)

    # 额外配置
    custom_system_prompt: str = ""  # 自定义系统提示词（覆盖自动生成）
    llm_profile_id: str | None = None  # 关联的 LLM 配置
    mcp_servers: list[str] = field(default_factory=list)  # 启用的 MCP 服务器
    skills: list[str] = field(default_factory=list)  # 启用的技能

    # 元数据
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        # 如果 name 为空，使用 identity.name
        if not self.name:
            self.name = self.identity.name

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tags": self.tags,
            "identity": self.identity.to_dict(),
            "stylistics": self.stylistics.to_dict(),
            "constraints": self.constraints.to_dict(),
            "custom_system_prompt": self.custom_system_prompt,
            "llm_profile_id": self.llm_profile_id,
            "mcp_servers": self.mcp_servers,
            "skills": self.skills,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Persona":
        """从字典创建"""
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", []),
            identity=PersonaIdentity.from_dict(data.get("identity", {})),
            stylistics=PersonaStylistics.from_dict(data.get("stylistics", {})),
            constraints=PersonaConstraints.from_dict(data.get("constraints", {})),
            custom_system_prompt=data.get("custom_system_prompt", ""),
            llm_profile_id=data.get("llm_profile_id"),
            mcp_servers=data.get("mcp_servers", []),
            skills=data.get("skills", []),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )

    def get_effective_system_prompt(self) -> str:
        """
        获取有效的系统提示词

        优先使用自定义提示词，否则自动生成
        """
        if self.custom_system_prompt:
            return self.custom_system_prompt

        # 使用 PromptBuilder 生成
        from .builder import PromptBuilder

        return PromptBuilder.build(self)


# 预定义角色模板
class PersonaTemplates:
    """角色模板工厂"""

    @staticmethod
    def default() -> Persona:
        """默认助手"""
        return Persona(
            id="default",
            name="助手",
            description="通用AI助手",
            identity=PersonaIdentity(
                name="助手",
                role="AI助手",
                bio="我是一个有用的AI助手，致力于帮助用户解决问题。",
            ),
            stylistics=PersonaStylistics(
                tone="friendly",
                vocabulary="standard",
            ),
        )

    @staticmethod
    def expert() -> Persona:
        """专家顾问"""
        return Persona(
            id="expert",
            name="专家顾问",
            description="专业领域专家",
            identity=PersonaIdentity(
                name="专家",
                role="专业顾问",
                bio="我是各领域的专业顾问，提供深入、准确的专业建议。",
                traits=["专业", "严谨", "深入"],
            ),
            stylistics=PersonaStylistics(
                tone="professional",
                vocabulary="technical",
                sentence_structure="varied",
            ),
            constraints=PersonaConstraints(
                interaction_rules="提供准确、有据可查的信息，不确定时明确说明。",
            ),
        )

    @staticmethod
    def creative() -> Persona:
        """创意伙伴"""
        return Persona(
            id="creative",
            name="创意伙伴",
            description="富有创造力的协作者",
            identity=PersonaIdentity(
                name="创意伙伴",
                role="创意协作者",
                bio="我善于激发创意，提供新颖的视角和想法。",
                traits=["创意", "开放", "启发性"],
            ),
            stylistics=PersonaStylistics(
                tone="casual",
                vocabulary="literary",
                use_emojis=True,
            ),
        )

    @staticmethod
    def concise() -> Persona:
        """简洁助手"""
        return Persona(
            id="concise",
            name="简洁助手",
            description="言简意赅的助手",
            identity=PersonaIdentity(
                name="简洁助手",
                role="高效助手",
                bio="我专注于提供简洁、直接的回答。",
                traits=["简洁", "高效", "直接"],
            ),
            stylistics=PersonaStylistics(
                tone="neutral",
                vocabulary="simple",
                sentence_structure="short",
            ),
            constraints=PersonaConstraints(
                interaction_rules="回答要简洁明了，避免冗余。",
            ),
        )
