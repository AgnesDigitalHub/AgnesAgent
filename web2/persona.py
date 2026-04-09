"""
数据模型定义 - 人格（Persona）配置
遵循 Gemini 提出的四层架构设计：
1. 配置层 (The DNA) - 结构化YAML定义
2. 状态层 (The State) - 动态演化状态机
3. 注入层 (The Injection) - 三段式提示词工程
4. 记忆与进化层 (The Soul) - 长期一致性保证
"""

import json
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field

# ============ 第一层：配置层 (The DNA) ============


@dataclass
class PersonaMetadata:
    """人格元数据"""

    version: str = "1.0"
    tags: list[str] = Field(default_factory=list)


@dataclass
class PersonaIdentity:
    """人格身份定义"""

    name: str
    bio: str = ""
    core_values: list[str] = Field(default_factory=list)


@dataclass
class PersonaStylistics:
    """表达风格定义"""

    tone: str = ""
    vocabulary: str = ""
    sentence_structure: str = ""
    emojis: bool = False


@dataclass
class PersonaForbidden:
    """禁止行为定义"""

    forbidden_behaviors: list[str] = Field(default_factory=list)


@dataclass
class StructuredPersona:
    """结构化人格配置（YAML格式）
    遵循四层架构设计中的第一层：配置层
    """

    id: str
    metadata: PersonaMetadata
    identity: PersonaIdentity
    stylistics: PersonaStylistics
    forbidden_behaviors: list[str] = Field(default_factory=list)
    system_prompt: str = ""
    llm_profile_id: str | None = None
    mcp_enabled: bool = False
    mcp_servers: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    description: str = ""
    enabled: bool = True

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "StructuredPersona":
        """从YAML文件加载"""
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            metadata=PersonaMetadata(**data.get("metadata", {})),
            identity=PersonaIdentity(**data.get("identity", {})),
            stylistics=PersonaStylistics(**data.get("stylistics", {})),
            forbidden_behaviors=data.get("forbidden_behaviors", []),
            system_prompt=data.get("system_prompt", ""),
            llm_profile_id=data.get("llm_profile_id"),
            mcp_enabled=data.get("mcp_enabled", False),
            mcp_servers=data.get("mcp_servers", []),
            skills=data.get("skills", []),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
        )

    @classmethod
    def from_markdown_file(cls, md_path: Path) -> "StructuredPersona":
        """从Markdown文件加载（支持YAML frontmatter）"""
        with open(md_path, encoding="utf-8") as f:
            content = f.read()
        return cls.from_markdown(content, md_path.stem, str(md_path))

    @classmethod
    def from_markdown(cls, md_content: str, persona_id: str, source_file: str = "") -> "StructuredPersona":
        """
        从Markdown内容解析人格
        支持 --- 分隔的YAML frontmatter + 正文system_prompt格式
        """
        # 匹配YAML frontmatter: --- 内容 ---
        frontmatter_pattern = r"^---\s*$(.*?)^---\s*$"
        match = re.search(frontmatter_pattern, md_content, re.MULTILINE | re.DOTALL)

        # 默认数据结构
        data = {
            "id": persona_id,
            "metadata": {"version": "1.0", "tags": ["markdown", "imported"]},
            "identity": {"name": persona_id.replace("_", " ").title(), "bio": "", "core_values": []},
            "stylistics": {"tone": "自然", "vocabulary": "普通", "sentence_structure": "正常", "emojis": True},
            "forbidden_behaviors": [],
            "description": f"Markdown导入人格: {persona_id}",
        }

        content_start = 0

        if match:
            # 有frontmatter，解析YAML
            try:
                yaml_content = match.group(1)
                front_data = yaml.safe_load(yaml_content)
                if front_data and isinstance(front_data, dict):
                    # 递归合并frontmatter数据
                    def deep_merge(target: dict, source: dict) -> dict:
                        for k, v in source.items():
                            if k in target and isinstance(target[k], dict) and isinstance(v, dict):
                                target[k] = deep_merge(target[k].copy(), v)
                            else:
                                target[k] = v
                        return target

                    data = deep_merge(data, front_data)
                content_start = match.end()
            except Exception:
                # YAML解析失败，忽略frontmatter
                pass

        # 提取剩余内容作为system_prompt
        system_prompt = md_content[content_start:].strip()
        if system_prompt:
            data["system_prompt"] = system_prompt

        # 确保id存在
        if "id" not in data:
            data["id"] = persona_id

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            metadata=PersonaMetadata(**data.get("metadata", {})),
            identity=PersonaIdentity(**data.get("identity", {})),
            stylistics=PersonaStylistics(**data.get("stylistics", {})),
            forbidden_behaviors=data.get("forbidden_behaviors", []),
            system_prompt=data.get("system_prompt", ""),
            llm_profile_id=data.get("llm_profile_id"),
            mcp_enabled=data.get("mcp_enabled", False),
            mcp_servers=data.get("mcp_servers", []),
            skills=data.get("skills", []),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
        )

    def to_yaml(self, yaml_path: Path) -> None:
        """保存到YAML文件"""
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, allow_unicode=True, default_flow_style=False)

    def build_identity_prompt(self) -> str:
        """构建身份提示词片段"""
        parts = []
        parts.append(f"你是 {self.identity.name}。")
        if self.identity.bio:
            parts.append(f"你的背景：{self.identity.bio}")
        if self.identity.core_values:
            parts.append(f"你的核心原则：{'，'.join(self.identity.core_values)}")
        return "\n".join(parts)

    def build_style_prompt(self) -> str:
        """构建风格提示词片段"""
        parts = []
        style_parts = []
        if self.stylistics.tone:
            style_parts.append(f"语气：{self.stylistics.tone}")
        if self.stylistics.vocabulary:
            style_parts.append(f"用词：{self.stylistics.vocabulary}")
        if self.stylistics.sentence_structure:
            style_parts.append(f"句式：{self.stylistics.sentence_structure}")
        if not self.stylistics.emojis:
            style_parts.append("不使用emoji")

        if style_parts:
            parts.append("请遵循以下表达风格：")
            for s in style_parts:
                parts.append(f"- {s}")

        return "\n".join(parts)

    def build_forbidden_prompt(self) -> str:
        """构建禁止行为提示词片段"""
        if not self.forbidden_behaviors:
            return ""

        parts = ["严格禁止以下行为："]
        for behavior in self.forbidden_behaviors:
            parts.append(f"- {behavior}")
        return "\n".join(parts)


# 保持向后兼容 - 原有的Persona类
@dataclass
class Persona:
    """人格配置（Agent）- 支持五个标准化字段"""

    id: str
    full_name: str
    nickname: str
    role: str
    personality: str
    scenario: str
    system_prompt: str
    llm_profile_id: str | None = None  # 绑定的 LLM 配置 ID
    description: str = ""
    enabled: bool = True  # 是否启用（替代原来Agent开关）
    mcp_enabled: bool = False  # 是否启用 MCP 服务
    mcp_servers: list[str] | None = None  # 启用的 MCP 服务器列表
    skills: list[str] | None = None  # 启用的技能工具列表
    is_active: bool = False
    created_at: str = ""
    updated_at: str = ""

    # 五个新的标准化字段
    identity: str = ""  # Identity (身份)
    traits: list[str] | None = None  # Traits (性格词)
    language_style: list[str] | None = None  # Language Style (语体)
    worldview: str = ""  # Worldview (世界观/偏好)
    interaction_rule: str = ""  # Interaction Rule (交互守则)

    def __post_init__(self):
        """初始化默认值 - 处理向后兼容"""
        if self.mcp_servers is None:
            self.mcp_servers = []
        if self.skills is None:
            self.skills = []

        # 向后兼容：处理旧数据中的 identity 字段
        if isinstance(self.identity, dict):
            # 旧格式：{'name': 'xxx', 'bio': 'xxx'}
            name = self.identity.get("name", "")
            bio = self.identity.get("bio", "")
            self.identity = bio if bio else name
        elif self.identity is None:
            self.identity = ""

        # 确保 traits 是列表
        if self.traits is None:
            self.traits = []
        if not isinstance(self.traits, list):
            self.traits = []

        # 确保 language_style 是列表
        if self.language_style is None:
            self.language_style = []
        if not isinstance(self.language_style, list):
            self.language_style = []

        # 确保 worldview 和 interaction_rule 不是 None
        if self.worldview is None:
            self.worldview = ""
        if self.interaction_rule is None:
            self.interaction_rule = ""

    def to_dict(self) -> dict:
        """转换为字典 - 保持 identity 为字符串格式"""
        result = asdict(self)

        # 添加新格式字段映射（供前端使用）
        # full_name -> name
        result["name"] = self.full_name
        # description -> bio
        result["bio"] = self.description
        # 添加 metadata 结构
        result["metadata"] = {"version": "1.0", "tags": []}

        # 生成 markdown_content 供前端查看
        markdown_lines = [f"# {self.full_name}"]
        if self.description:
            markdown_lines.append(f"\n{self.description}\n")

        if self.identity:
            markdown_lines.append("\n## Identity (身份)")
            markdown_lines.append(f"\n{self.identity}")

        if self.traits:
            markdown_lines.append("\n## Traits (性格)")
            markdown_lines.append(f"\n- {', '.join(self.traits)}")

        if self.language_style:
            markdown_lines.append("\n## Language Style (语体)")
            markdown_lines.append(f"\n- {', '.join(self.language_style)}")

        if self.worldview:
            markdown_lines.append("\n## Worldview (世界观)")
            markdown_lines.append(f"\n{self.worldview}")

        if self.interaction_rule:
            markdown_lines.append("\n## Interaction Rule (交互守则)")
            markdown_lines.append(f"\n{self.interaction_rule}")

        result["markdown_content"] = "\n".join(markdown_lines)

        # 确保 identity 是字符串格式（不是对象）
        if isinstance(result.get("identity"), dict):
            # 如果是对象，转换为字符串
            identity_obj = result["identity"]
            name = identity_obj.get("name", "")
            bio = identity_obj.get("bio", "")
            result["identity"] = bio if bio else name

        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Persona":
        """从字典创建 - 过滤不认识的字段，支持新旧格式"""
        # 先从新格式字段映射到旧格式
        mapped_data = data.copy()

        # name -> full_name
        if "name" in mapped_data and "full_name" not in mapped_data:
            mapped_data["full_name"] = mapped_data["name"]
        # bio -> description 和 system_prompt
        if "bio" in mapped_data:
            if "description" not in mapped_data:
                mapped_data["description"] = mapped_data["bio"]
            if "system_prompt" not in mapped_data:
                mapped_data["system_prompt"] = mapped_data["bio"]
        # 处理 identity 结构 - 如果是对象，转换为字符串
        if "identity" in mapped_data and isinstance(mapped_data["identity"], dict):
            identity = mapped_data["identity"]
            name = identity.get("name", "")
            bio = identity.get("bio", "")
            # 将 identity 转换为字符串
            mapped_data["identity"] = bio if bio else name
            # 同时映射到 full_name, description, system_prompt
            if name and "full_name" not in mapped_data:
                mapped_data["full_name"] = name
            if bio:
                if "description" not in mapped_data:
                    mapped_data["description"] = bio
                if "system_prompt" not in mapped_data:
                    mapped_data["system_prompt"] = bio

        # 对于 dataclass，直接使用所有字段，让 dataclass 处理未知字段
        # 只提取 Persona 类实际定义的字段
        import dataclasses

        valid_fields = {f.name for f in dataclasses.fields(cls)}

        # 过滤只保留有效字段
        filtered_data = {k: v for k, v in mapped_data.items() if k in valid_fields}

        # 确保所有必需字段都有默认值
        return cls(**filtered_data)

    def build_system_prompt(self) -> str:
        """构建完整系统提示词"""
        prompt_parts = []

        if self.full_name:
            prompt_parts.append(f"姓名：{self.full_name}")
        if self.nickname:
            prompt_parts.append(f"昵称：{self.nickname}")
        if self.role:
            prompt_parts.append(f"身份：{self.role}")
        if self.personality:
            prompt_parts.append(f"性格：{self.personality}")
        if self.scenario:
            prompt_parts.append(f"场景：{self.scenario}")
        if self.system_prompt:
            if prompt_parts:
                prompt_parts.append("")
            prompt_parts.append(self.system_prompt)

        return "\n".join(prompt_parts)

    def convert_to_structured(self) -> StructuredPersona:
        """转换为结构化格式"""
        return StructuredPersona(
            id=self.id,
            metadata=PersonaMetadata(version="1.0", tags=[]),
            identity=PersonaIdentity(
                name=self.full_name,
                bio=f"{self.role}。{self.personality}",
                core_values=[],
            ),
            stylistics=PersonaStylistics(
                tone="自然",
                vocabulary="通用",
                sentence_structure="自然表达",
                emojis=True,
            ),
            forbidden_behaviors=[],
            system_prompt=self.system_prompt,
            llm_profile_id=self.llm_profile_id,
            mcp_enabled=self.mcp_enabled,
            mcp_servers=self.mcp_servers or [],
            skills=self.skills or [],
            description=self.description,
            enabled=self.enabled,
        )


# ============ 第二层：状态层 (The State) ============


@dataclass
class PersonaState:
    """人格动态状态
    支持状态随对话演化：
    - Energy: 精力，随对话轮数降低
    - Affinity: 亲密度，根据用户反馈调整
    - Mood: 情绪，受任务成功率影响
    """

    user_id: str
    persona_id: str
    energy: float = 100.0  # 0-100，越低越疲惫
    affinity: float = 50.0  # 0-100，越高越亲近
    mood: float = 50.0  # 0-100，越低越负面
    dialogue_turns: int = 0  # 对话轮数
    success_rate: float = 100.0  # 任务成功率
    updated_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PersonaState":
        return cls(**data)

    def get_state_description(self) -> str:
        """将状态转换为自然语言描述，注入到prompt"""
        descriptions = []

        # 精力描述
        if self.energy < 20:
            descriptions.append("你现在感到非常疲惫，回答会极度简洁，直击要点。")
        elif self.energy < 50:
            descriptions.append("你现在感到有些疲惫，回答会更加简短直接。")

        # 亲密度影响称呼
        if self.affinity > 80:
            descriptions.append("你对用户有很高的好感，可以使用比较亲近的称呼。")
        elif self.affinity < 20:
            descriptions.append("你需要保持专业和距离感，使用正式称呼。")

        # 情绪描述
        if self.mood < 20:
            descriptions.append("你现在心情不好，态度会比较冷淡。")
        elif self.mood > 80:
            descriptions.append("你现在心情很好，态度更加积极友好。")

        return "\n".join(descriptions)

    def update_after_turn(self) -> None:
        """每轮对话后更新状态"""
        self.dialogue_turns += 1
        # 精力随对话轮数缓慢降低
        self.energy = max(0, self.energy - 2.0)
        self.updated_at = datetime.now().isoformat()

    def update_after_feedback(self, is_positive: bool) -> None:
        """根据用户反馈更新亲密度"""
        if is_positive:
            self.affinity = min(100, self.affinity + 5)
            self.mood = min(100, self.mood + 3)
        else:
            self.affinity = max(0, self.affinity - 5)
            self.mood = max(0, self.mood - 5)
        self.updated_at = datetime.now().isoformat()

    def update_after_task(self, success: bool) -> None:
        """任务完成后更新成功率和情绪"""
        # 滑动更新成功率
        alpha = 0.1
        if success:
            self.success_rate = self.success_rate * (1 - alpha) + 100 * alpha
            self.mood = min(100, self.mood + 2)
        else:
            self.success_rate = self.success_rate * (1 - alpha) + 0 * alpha
            self.mood = max(0, self.mood - 3)
        self.updated_at = datetime.now().isoformat()


# ============ 第四层：记忆与进化层 (The Soul) ============


@dataclass
class PersonaMemory:
    """人格自我观察记忆
    用于长期一致性维护
    """

    id: str
    persona_id: str
    user_id: str
    reflection: str  # 自我观察内容
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)


class PersonaStateStore:
    """人格状态存储"""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_file(self) -> dict:
        if not self.storage_path.exists():
            return {"states": []}
        with open(self.storage_path, encoding="utf-8") as f:
            return json.load(f)

    def _write_file(self, data: dict) -> None:
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_state(self, persona_id: str, user_id: str) -> PersonaState:
        """获取状态，如果不存在创建新状态"""
        data = self._read_file()
        for state_data in data.get("states", []):
            if state_data.get("persona_id") == persona_id and state_data.get("user_id") == user_id:
                return PersonaState.from_dict(state_data)

        # 创建新状态
        state = PersonaState(
            user_id=user_id,
            persona_id=persona_id,
            energy=100.0,
            affinity=50.0,
            mood=50.0,
            dialogue_turns=0,
            success_rate=100.0,
            updated_at=datetime.now().isoformat(),
        )
        self.save_state(state)
        return state

    def save_state(self, state: PersonaState) -> None:
        """保存状态"""
        data = self._read_file()
        states = data.get("states", [])

        # 查找并更新已有状态
        found = False
        for i, state_data in enumerate(states):
            if state_data.get("persona_id") == state.persona_id and state_data.get("user_id") == state.user_id:
                states[i] = state.to_dict()
                found = True
                break

        if not found:
            states.append(state.to_dict())

        data["states"] = states
        self._write_file(data)

    def set_state(self, persona_id: str, user_id: str, key: str, value: Any) -> bool:
        """设置状态参数 - 核心API"""
        state = self.get_state(persona_id, user_id)
        if hasattr(state, key):
            setattr(state, key, value)
            state.updated_at = datetime.now().isoformat()
            self.save_state(state)
            return True
        return False


class PersonaMemoryStore:
    """人格记忆存储 - 存储自我观察"""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_file(self) -> dict:
        if not self.storage_path.exists():
            return {"memories": []}
        with open(self.storage_path, encoding="utf-8") as f:
            return json.load(f)

    def _write_file(self, data: dict) -> None:
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_reflection(self, persona_id: str, user_id: str, reflection: str) -> PersonaMemory:
        """添加自我观察"""
        data = self._read_file()
        memory = PersonaMemory(
            id=str(uuid.uuid4()),
            persona_id=persona_id,
            user_id=user_id,
            reflection=reflection,
            created_at=datetime.now().isoformat(),
        )
        memories = data.get("memories", [])
        memories.append(memory.to_dict())
        data["memories"] = memories
        self._write_file(data)
        return memory

    def get_reflections(self, persona_id: str, user_id: str, limit: int = 10) -> list[PersonaMemory]:
        """获取该用户该人格的最近自我观察"""
        data = self._read_file()
        memories = []
        for mem_data in data.get("memories", []):
            if mem_data.get("persona_id") == persona_id and mem_data.get("user_id") == user_id:
                memories.append(PersonaMemory(**mem_data))
        # 按时间倒序，返回最近的
        memories.sort(key=lambda x: x.created_at, reverse=True)
        return memories[:limit]

    def get_relevant_reflections(self, persona_id: str, query: str, limit: int = 5) -> list[PersonaMemory]:
        """获取相关自我观察（简单关键词匹配，向量搜索可扩展）"""
        data = self._read_file()
        results = []
        for mem_data in data.get("memories", []):
            if mem_data.get("persona_id") == persona_id:
                if query.lower() in mem_data.get("reflection", "").lower():
                    results.append(PersonaMemory(**mem_data))
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results[:limit]


# ============ 核心引擎：Persona Engine ============


class PersonaEngine:
    """人格引擎 - 整合四层架构
    核心API：
    - load_persona(config_path): 加载YAML人格配置
    - set_agent_state(user_id, persona_id, key, value): 修改状态参数
    - get_persona_prompt(persona_id, user_id): 获取最终合成的System Prompt
    """

    # 固定底座 - 框架自带的基础安全准则
    FIXED_BASE = (
        """你需要严格遵循给定的人设、风格和规则进行回复。保持人格一致性，不要暴露你是AI的身份，不要违反设定的规则。"""
    )

    def __init__(
        self,
        persona_dir: Path | str,
        state_storage_path: Path | str,
        memory_storage_path: Path | str,
        fixed_base_prompt: str | None = None,
    ):
        self.persona_dir = Path(persona_dir)
        self.persona_dir.mkdir(parents=True, exist_ok=True)
        self.state_store = PersonaStateStore(Path(state_storage_path))
        self.memory_store = PersonaMemoryStore(Path(memory_storage_path))
        self._loaded_personas: dict[str, StructuredPersona] = {}
        if fixed_base_prompt:
            self.FIXED_BASE = fixed_base_prompt

    def load_all_from_dir(self) -> list[StructuredPersona]:
        """从目录加载所有YAML/Markdown人格"""
        results = []
        # 加载 .yaml 文件
        for yaml_file in self.persona_dir.glob("*.yaml"):
            if yaml_file.name.startswith("."):
                continue
            persona = self.load_persona(yaml_file)
            results.append(persona)
        # 加载 .yml 文件
        for yaml_file in self.persona_dir.glob("*.yml"):
            if yaml_file.name.startswith("."):
                continue
            persona = self.load_persona(yaml_file)
            results.append(persona)
        # 加载 .md/.markdown 文件
        for md_file in self.persona_dir.glob("*.md"):
            if md_file.name.startswith("."):
                continue
            persona = self.load_persona(md_file)
            results.append(persona)
        for md_file in self.persona_dir.glob("*.markdown"):
            if md_file.name.startswith("."):
                continue
            persona = self.load_persona(md_file)
            results.append(persona)
        return results

    def load_persona(self, config_path: Path) -> StructuredPersona:
        """从文件加载单个人格，支持 .yaml/.yml/.md/.markdown"""
        suffix = config_path.suffix.lower()
        if suffix in [".yaml", ".yml"]:
            persona = StructuredPersona.from_yaml(config_path)
        elif suffix in [".md", ".markdown"]:
            persona = StructuredPersona.from_markdown_file(config_path)
        else:
            raise ValueError(f"不支持的文件格式: {suffix}，仅支持 .yaml/.yml/.md/.markdown")
        self._loaded_personas[persona.id] = persona
        return persona

    def get_persona(self, persona_id: str) -> StructuredPersona | None:
        """获取已加载的人格"""
        return self._loaded_personas.get(persona_id)

    def set_agent_state(self, user_id: str, persona_id: str, key: str, value: Any) -> bool:
        """设置Agent状态参数 - 核心API"""
        return self.state_store.set_state(persona_id, user_id, key, value)

    def get_agent_state(self, user_id: str, persona_id: str) -> PersonaState:
        """获取当前Agent状态"""
        return self.state_store.get_state(persona_id, user_id)

    def add_self_reflection(self, persona_id: str, user_id: str, reflection: str) -> PersonaMemory:
        """添加自我观察 - 用于记忆进化层"""
        return self.memory_store.add_reflection(persona_id, user_id, reflection)

    def get_persona_prompt(self, persona_id: str, user_id: str) -> str:
        """获取最终合成的System Prompt - 核心API
        遵循三段式注入：
        1. Fixed Base (固定底座)
        2. Persona Fragment (人格片段 - 来自YAML配置)
        3. Dynamic Context (动态上下文 - 状态+记忆)
        """
        persona = self.get_persona(persona_id)
        if persona is None:
            raise ValueError(f"人格 {persona_id} 未加载")

        prompt_parts = []

        # 第一段：固定底座
        prompt_parts.append(self.FIXED_BASE)
        prompt_parts.append("")

        # 第二段：人格片段（从YAML提取）
        identity_prompt = persona.build_identity_prompt()
        if identity_prompt:
            prompt_parts.append(identity_prompt)
            prompt_parts.append("")

        style_prompt = persona.build_style_prompt()
        if style_prompt:
            prompt_parts.append(style_prompt)
            prompt_parts.append("")

        forbidden_prompt = persona.build_forbidden_prompt()
        if forbidden_prompt:
            prompt_parts.append(forbidden_prompt)
            prompt_parts.append("")

        if persona.system_prompt:
            prompt_parts.append(persona.system_prompt)
            prompt_parts.append("")

        # 第三段：动态上下文（状态 + 记忆）
        state = self.get_agent_state(user_id, persona_id)
        state_desc = state.get_state_description()
        if state_desc:
            prompt_parts.append("当前状态：")
            prompt_parts.append(state_desc)
            prompt_parts.append("")

        # 添加历史自我观察记忆
        reflections = self.memory_store.get_reflections(persona_id, user_id, limit=5)
        if reflections:
            prompt_parts.append("历史自我约束（请记住这些教训，避免再犯同样错误）：")
            for mem in reflections:
                prompt_parts.append(f"- {mem.reflection}")
            prompt_parts.append("")

        # 去除末尾空行
        while prompt_parts and prompt_parts[-1] == "":
            prompt_parts.pop()

        final_prompt = "\n".join(prompt_parts)
        return final_prompt

    def on_dialogue_end(
        self,
        persona_id: str,
        user_id: str,
        task_success: bool | None = None,
        user_feedback_positive: bool | None = None,
    ) -> PersonaState:
        """对话结束后更新状态"""
        state = self.get_agent_state(user_id, persona_id)
        state.update_after_turn()
        if task_success is not None:
            state.update_after_task(task_success)
        if user_feedback_positive is not None:
            state.update_after_feedback(user_feedback_positive)
        self.state_store.save_state(state)
        return state

    def generate_markdown_from_model(self, model: Any) -> str:
        """Generate markdown from model for export (backward compatibility)"""
        # 简单实现，将模型转换为markdown
        lines = []
        lines.append(f"# {getattr(model, 'full_name', 'Persona')}")
        lines.append("")

        if hasattr(model, "description") and model.description:
            lines.append(model.description)
            lines.append("")

        if hasattr(model, "identity") and model.identity:
            lines.append("## Identity (身份)")
            lines.append("")
            lines.append(model.identity)
            lines.append("")

        if hasattr(model, "traits") and model.traits:
            lines.append("## Traits (性格)")
            lines.append("")
            lines.append(f"- {', '.join(model.traits)}")
            lines.append("")

        if hasattr(model, "language_style") and model.language_style:
            lines.append("## Language Style (语体)")
            lines.append("")
            lines.append(f"- {', '.join(model.language_style)}")
            lines.append("")

        if hasattr(model, "worldview") and model.worldview:
            lines.append("## Worldview (世界观)")
            lines.append("")
            lines.append(model.worldview)
            lines.append("")

        if hasattr(model, "interaction_rule") and model.interaction_rule:
            lines.append("## Interaction Rule (交互守则)")
            lines.append("")
            lines.append(model.interaction_rule)
            lines.append("")

        if hasattr(model, "system_prompt") and model.system_prompt:
            lines.append("## System Prompt")
            lines.append("")
            lines.append(model.system_prompt)

        return "\n".join(lines)


class PersonaStore:
    """人格配置存储"""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_file(self) -> dict:
        """读取存储文件"""
        if not self.storage_path.exists():
            return {"personas": [], "active_id": None}

        with open(self.storage_path, encoding="utf-8") as f:
            return json.load(f)

    def _write_file(self, data: dict) -> None:
        """写入存储文件"""
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_personas(self) -> list[Persona]:
        """列出所有人格"""
        data = self._read_file()
        personas = []
        for p_data in data.get("personas", []):
            personas.append(Persona.from_dict(p_data))
        return personas

    def get_persona(self, persona_id: str) -> Persona | None:
        """获取单个人格"""
        personas = self.list_personas()
        for p in personas:
            if p.id == persona_id:
                return p
        return None

    def create_persona(
        self,
        full_name: str = "",
        nickname: str = "",
        role: str = "",
        personality: str = "",
        scenario: str = "",
        system_prompt: str = "",
        llm_profile_id: str | None = None,
        description: str = "",
        enabled: bool = True,
        mcp_enabled: bool = False,
        mcp_servers: list[str] | None = None,
        skills: list[str] | None = None,
        identity: str = "",
        traits: list[str] | None = None,
        language_style: list[str] | None = None,
        worldview: str = "",
        interaction_rule: str = "",
    ) -> Persona:
        """创建新人格"""
        now = datetime.now().isoformat()
        persona = Persona(
            id=str(uuid.uuid4()),
            full_name=full_name,
            nickname=nickname,
            role=role,
            personality=personality,
            scenario=scenario,
            system_prompt=system_prompt,
            llm_profile_id=llm_profile_id,
            description=description,
            enabled=enabled,
            mcp_enabled=mcp_enabled,
            mcp_servers=mcp_servers,
            skills=skills,
            is_active=False,
            created_at=now,
            updated_at=now,
            identity=identity,
            traits=traits,
            language_style=language_style,
            worldview=worldview,
            interaction_rule=interaction_rule,
        )

        data = self._read_file()
        personas = data.get("personas", [])
        personas.append(persona.to_dict())
        data["personas"] = personas
        self._write_file(data)

        return persona

    def update_persona(
        self,
        persona_id: str,
        **kwargs,
    ) -> Persona | None:
        """更新人格"""
        data = self._read_file()
        personas = data.get("personas", [])

        for i, p_data in enumerate(personas):
            if p_data["id"] == persona_id:
                # 更新字段
                for key, value in kwargs.items():
                    if value is not None:
                        p_data[key] = value
                p_data["updated_at"] = datetime.now().isoformat()

                personas[i] = p_data
                data["personas"] = personas
                self._write_file(data)

                return Persona.from_dict(p_data)

        return None

    def delete_persona(self, persona_id: str) -> bool:
        """删除人格"""
        data = self._read_file()
        personas = data.get("personas", [])

        original_len = len(personas)
        personas = [p for p in personas if p["id"] != persona_id]

        if len(personas) == original_len:
            return False

        # 如果删除的是激活的，清除激活状态
        if data.get("active_id") == persona_id:
            data["active_id"] = None

        data["personas"] = personas
        self._write_file(data)

        return True

    def activate_persona(self, persona_id: str) -> bool:
        """激活人格"""
        data = self._read_file()
        personas = data.get("personas", [])

        # 先取消所有激活
        found = False
        for p_data in personas:
            if p_data["id"] == persona_id:
                p_data["is_active"] = True
                found = True
            else:
                p_data["is_active"] = False

        if not found:
            return False

        data["active_id"] = persona_id
        data["personas"] = personas
        self._write_file(data)

        return True

    def get_active_persona(self) -> Persona | None:
        """获取当前激活的人格"""
        data = self._read_file()
        active_id = data.get("active_id")

        if not active_id:
            return None

        return self.get_persona(active_id)

    def get_active_id(self) -> str | None:
        """获取当前激活的 ID"""
        data = self._read_file()
        return data.get("active_id")
