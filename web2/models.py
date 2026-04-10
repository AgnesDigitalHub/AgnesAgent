"""
数据模型定义 - 模型配置
"""

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from agnes.utils.config_loader import LLMConfig


@dataclass
class LLMProfile:
    """LLM 配置档案"""

    id: str
    name: str
    description: str
    provider: str
    model: str
    base_url: str | None = None
    api_key: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    enabled_models: list[str] | None = None
    is_active: bool = False
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LLMProfile":
        """从字典创建"""
        return cls(**data)

    def to_llm_config(self) -> LLMConfig:
        """转换为 Agnes LLMConfig"""
        return LLMConfig(
            provider=self.provider,
            model=self.model,
            base_url=self.base_url,
            api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )


class ProfileStore:
    """LLM 配置档案存储"""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_file(self) -> dict:
        """读取存储文件"""
        if not self.storage_path.exists():
            return {"profiles": [], "active_id": None}

        with open(self.storage_path, encoding="utf-8") as f:
            return json.load(f)

    def _write_file(self, data: dict) -> None:
        """写入存储文件"""
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_profiles(self) -> list[LLMProfile]:
        """列出所有配置"""
        data = self._read_file()
        profiles = []
        for p_data in data.get("profiles", []):
            profiles.append(LLMProfile.from_dict(p_data))
        return profiles

    def get_profile(self, profile_id: str) -> LLMProfile | None:
        """获取单个配置"""
        profiles = self.list_profiles()
        for p in profiles:
            if p.id == profile_id:
                return p
        return None

    def create_profile(
        self,
        name: str,
        description: str,
        provider: str,
        model: str,
        base_url: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        enabled_models: list[str] | None = None,
    ) -> LLMProfile:
        """创建新配置"""
        now = datetime.now().isoformat()
        profile = LLMProfile(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            provider=provider,
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            enabled_models=enabled_models,
            is_active=False,
            created_at=now,
            updated_at=now,
        )

        data = self._read_file()
        profiles = data.get("profiles", [])
        profiles.append(profile.to_dict())
        data["profiles"] = profiles
        self._write_file(data)

        return profile

    def update_profile(
        self,
        profile_id: str,
        **kwargs,
    ) -> LLMProfile | None:
        """更新配置"""
        data = self._read_file()
        profiles = data.get("profiles", [])

        for i, p_data in enumerate(profiles):
            if p_data["id"] == profile_id:
                # 更新字段
                for key, value in kwargs.items():
                    if value is not None:
                        p_data[key] = value
                p_data["updated_at"] = datetime.now().isoformat()

                profiles[i] = p_data
                data["profiles"] = profiles
                self._write_file(data)

                return LLMProfile.from_dict(p_data)

        return None

    def delete_profile(self, profile_id: str) -> bool:
        """删除配置"""
        data = self._read_file()
        profiles = data.get("profiles", [])

        original_len = len(profiles)
        profiles = [p for p in profiles if p["id"] != profile_id]

        if len(profiles) == original_len:
            return False

        # 如果删除的是激活的，清除激活状态
        if data.get("active_id") == profile_id:
            data["active_id"] = None

        data["profiles"] = profiles
        self._write_file(data)

        return True

    def activate_profile(self, profile_id: str) -> bool:
        """激活配置"""
        data = self._read_file()
        profiles = data.get("profiles", [])

        # 先取消所有激活
        found = False
        for p_data in profiles:
            if p_data["id"] == profile_id:
                p_data["is_active"] = True
                found = True
            else:
                p_data["is_active"] = False

        if not found:
            return False

        data["active_id"] = profile_id
        data["profiles"] = profiles
        self._write_file(data)

        return True

    def get_active_profile(self) -> LLMProfile | None:
        """获取当前激活的配置"""
        data = self._read_file()
        active_id = data.get("active_id")

        if not active_id:
            return None

        return self.get_profile(active_id)

    def get_active_id(self) -> str | None:
        """获取当前激活的 ID"""
        data = self._read_file()
        return data.get("active_id")

    def deactivate_profile(self) -> None:
        """取消激活当前配置"""
        data = self._read_file()
        profiles = data.get("profiles", [])

        # 取消所有配置的激活状态
        for p_data in profiles:
            p_data["is_active"] = False

        data["active_id"] = None
        data["profiles"] = profiles
        self._write_file(data)


# ============ Agent 模型 ============


@dataclass
class Agent:
    """Agent 定义"""

    id: str
    name: str
    description: str
    enabled: bool
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Agent":
        """从字典创建"""
        return cls(**data)


class AgentStore:
    """Agent 存储"""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_file(self) -> dict:
        """读取存储文件"""
        if not self.storage_path.exists():
            return {"agents": []}

        with open(self.storage_path, encoding="utf-8") as f:
            return json.load(f)

    def _write_file(self, data: dict) -> None:
        """写入存储文件"""
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_agents(self) -> list[Agent]:
        """列出所有 Agent"""
        data = self._read_file()
        agents = []
        for a_data in data.get("agents", []):
            agents.append(Agent.from_dict(a_data))
        return agents

    def get_agent(self, agent_id: str) -> Agent | None:
        """获取单个 Agent"""
        agents = self.list_agents()
        for a in agents:
            if a.id == agent_id:
                return a
        return None

    def create_agent(
        self,
        name: str,
        description: str,
        enabled: bool = True,
    ) -> Agent:
        """创建新 Agent"""
        now = datetime.now().isoformat()
        agent = Agent(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            enabled=enabled,
            created_at=now,
            updated_at=now,
        )

        data = self._read_file()
        agents = data.get("agents", [])
        agents.append(agent.to_dict())
        data["agents"] = agents
        self._write_file(data)

        return agent

    def update_agent(
        self,
        agent_id: str,
        **kwargs,
    ) -> Agent | None:
        """更新 Agent"""
        data = self._read_file()
        agents = data.get("agents", [])

        for i, a_data in enumerate(agents):
            if a_data["id"] == agent_id:
                # 更新字段
                for key, value in kwargs.items():
                    if value is not None:
                        a_data[key] = value
                a_data["updated_at"] = datetime.now().isoformat()

                agents[i] = a_data
                data["agents"] = agents
                self._write_file(data)

                return Agent.from_dict(a_data)

        return None

    def delete_agent(self, agent_id: str) -> bool:
        """删除 Agent"""
        data = self._read_file()
        agents = data.get("agents", [])

        original_len = len(agents)
        agents = [a for a in agents if a["id"] != agent_id]

        if len(agents) == original_len:
            return False

        data["agents"] = agents
        self._write_file(data)

        return True

    def bulk_delete_agents(self, agent_ids: list[str]) -> int:
        """批量删除 Agent"""
        data = self._read_file()
        agents = data.get("agents", [])

        original_len = len(agents)
        agents = [a for a in agents if a["id"] not in agent_ids]
        deleted_count = original_len - len(agents)

        if deleted_count > 0:
            data["agents"] = agents
            self._write_file(data)

        return deleted_count


@dataclass
class PromptTemplate:
    """Prompt 模板"""

    id: str
    name: str
    description: str
    content: str
    variables: list[str]
    version: int
    created_at: str
    updated_at: str
    tags: list[str]
    is_builtin: bool

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PromptTemplate":
        """从字典创建"""
        return cls(**data)

    def extract_variables(self) -> list[str]:
        """从 content 中提取 {{variable}} 变量"""
        import re
        pattern = r"\{\{(\w+)\}\}"
        return list(set(re.findall(pattern, self.content)))


class PromptStore:
    """Prompt 模板存储"""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_file(self) -> dict:
        """读取存储文件"""
        if not self.storage_path.exists():
            return {"prompts": [], "version": 1}

        with open(self.storage_path, encoding="utf-8") as f:
            return json.load(f)

    def _write_file(self, data: dict) -> None:
        """写入存储文件"""
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_prompts(self) -> list[PromptTemplate]:
        """列出所有 Prompt"""
        data = self._read_file()
        prompts = []
        for p_data in data.get("prompts", []):
            prompts.append(PromptTemplate.from_dict(p_data))
        return prompts

    def get_prompt(self, prompt_id: str) -> PromptTemplate | None:
        """获取单个 Prompt"""
        prompts = self.list_prompts()
        for p in prompts:
            if p.id == prompt_id:
                return p
        return None

    def create_prompt(
        self,
        name: str,
        description: str,
        content: str,
        tags: list[str] | None = None,
    ) -> PromptTemplate:
        """创建新 Prompt"""
        now = datetime.now().isoformat()
        prompt = PromptTemplate(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            content=content,
            variables=[],  # 创建时自动提取
            version=1,
            created_at=now,
            updated_at=now,
            tags=tags or [],
            is_builtin=False,
        )
        # 自动提取变量
        prompt.variables = prompt.extract_variables()

        data = self._read_file()
        data["prompts"].append(prompt.to_dict())
        self._write_file(data)
        return prompt

    def update_prompt(
        self,
        prompt_id: str,
        name: str | None = None,
        description: str | None = None,
        content: str | None = None,
        tags: list[str] | None = None,
    ) -> PromptTemplate | None:
        """更新 Prompt"""
        data = self._read_file()
        prompts = data.get("prompts", [])

        for i, p_data in enumerate(prompts):
            if p_data["id"] == prompt_id:
                if name is not None:
                    p_data["name"] = name
                if description is not None:
                    p_data["description"] = description
                if content is not None:
                    p_data["content"] = content
                    # 重新提取变量
                    import re
                    pattern = r"\{\{(\w+)\}\}"
                    p_data["variables"] = list(set(re.findall(pattern, content)))
                if tags is not None:
                    p_data["tags"] = tags

                p_data["version"] = p_data.get("version", 1) + 1
                p_data["updated_at"] = datetime.now().isoformat()

                data["prompts"] = prompts
                self._write_file(data)
                return PromptTemplate.from_dict(p_data)

        return None

    def delete_prompt(self, prompt_id: str) -> bool:
        """删除 Prompt"""
        data = self._read_file()
        prompts = data.get("prompts", [])

        original_len = len(prompts)
        prompts = [p for p in prompts if p["id"] != prompt_id]

        if len(prompts) < original_len:
            data["prompts"] = prompts
            self._write_file(data)
            return True
        return False

    def search_prompts(self, query: str, tags: list[str] | None = None) -> list[PromptTemplate]:
        """搜索 Prompt"""
        prompts = self.list_prompts()
        results = []

        for p in prompts:
            # 名称或描述匹配
            if query.lower() in p.name.lower() or query.lower() in p.description.lower():
                # 标签过滤
                if tags:
                    if any(tag in p.tags for tag in tags):
                        results.append(p)
                else:
                    results.append(p)

        return results
