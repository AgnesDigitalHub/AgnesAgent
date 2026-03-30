"""
配置管理器
"""

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from agnes.utils import get_logger

from .storage import ConfigStorage

logger = get_logger("agnes.config.manager")


@dataclass
class LLMProfile:
    """LLM 配置文件"""

    id: str
    name: str
    description: str = ""
    provider: str = "ollama"
    model: str = ""
    base_url: str | None = None
    api_key: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    enabled_models: list[str] | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "enabled_models": self.enabled_models,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LLMProfile":
        """从字典创建"""
        return cls(
            id=data.get("id", str(uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            provider=data.get("provider", "ollama"),
            model=data.get("model", ""),
            base_url=data.get("base_url"),
            api_key=data.get("api_key"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens"),
            enabled_models=data.get("enabled_models"),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            metadata=data.get("metadata", {}),
        )


class ConfigManager:
    """配置管理器"""

    def __init__(self, storage_dir: str = "config/llm_profiles"):
        """
        初始化配置管理器

        Args:
            storage_dir: 配置存储目录
        """
        self.storage = ConfigStorage(storage_dir)
        self._active_file = self.storage.storage_dir / ".active"
        self._active_profile_id: str | None = self._load_active_id()
        logger.info("Config manager initialized")

    def _load_active_id(self) -> str | None:
        """从磁盘加载上次激活的 Profile ID"""
        try:
            if self._active_file.exists():
                active_id = self._active_file.read_text(encoding="utf-8").strip()
                if active_id and self.storage.load_profile(active_id):
                    return active_id
        except Exception as e:
            logger.warning(f"Failed to load active profile id: {e}")
        return None

    def _save_active_id(self, profile_id: str | None) -> None:
        """将激活的 Profile ID 持久化到磁盘"""
        try:
            if profile_id:
                self._active_file.write_text(profile_id, encoding="utf-8")
            else:
                if self._active_file.exists():
                    self._active_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to save active profile id: {e}")

    def create_profile(
        self,
        name: str | None = None,
        provider: str = "ollama",
        model: str | None = None,
        description: str = "",
        base_url: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        enabled_models: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LLMProfile:
        """
        创建新配置

        Args:
            name: 配置名称
            provider: provider 类型
            model: 模型名称
            description: 配置描述
            base_url: API 地址
            api_key: API Key
            temperature: 温度
            max_tokens: 最大 token 数
            enabled_models: 可用模型列表
            metadata: 额外元数据

        Returns:
            创建的配置文件
        """
        # 如果没有提供name，根据provider自动生成
        if not name:
            name = f"{provider}-{uuid4().hex[:8]}"

        # 默认模型
        if not model:
            default_models = {
                "openai": "gpt-4o",
                "deepseek": "deepseek-chat",
                "gemini": "gemini-pro",
                "anthropic": "claude-3-sonnet-20240229",
                "ollama": "llama3",
                "openvino-server": "",
                "openai-compat": "",
                "local-api": "",
                "generic": "",
            }
            model = default_models.get(provider, "")

        profile = LLMProfile(
            id=str(uuid4()),
            name=name,
            description=description,
            provider=provider,
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            enabled_models=enabled_models,
            metadata=metadata or {},
        )

        self.storage.save_profile(profile.id, profile.to_dict())
        logger.info(f"Profile created: {name} ({profile.id})")
        return profile

    def get_profile(self, profile_id: str) -> LLMProfile | None:
        """
        获取配置

        Args:
            profile_id: 配置 ID

        Returns:
            配置文件，如果不存在返回 None
        """
        data = self.storage.load_profile(profile_id)
        if data:
            return LLMProfile.from_dict(data)
        return None

    def update_profile(self, profile_id: str, **kwargs) -> LLMProfile | None:
        """
        更新配置

        Args:
            profile_id: 配置 ID
            **kwargs: 要更新的字段

        Returns:
            更新后的配置文件，如果不存在返回 None
        """
        profile = self.get_profile(profile_id)
        if not profile:
            return None

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.updated_at = time.time()
        self.storage.save_profile(profile_id, profile.to_dict())
        logger.info(f"Profile updated: {profile_id}")
        return profile

    def delete_profile(self, profile_id: str) -> bool:
        """
        删除配置

        Args:
            profile_id: 配置 ID

        Returns:
            是否删除成功
        """
        # 如果删除的是当前激活的配置，则取消激活
        if self._active_profile_id == profile_id:
            self._active_profile_id = None
            self._save_active_id(None)

        success = self.storage.delete_profile(profile_id)
        if success:
            logger.info(f"Profile deleted: {profile_id}")
        return success

    def list_profiles(self) -> list[LLMProfile]:
        """
        列出所有配置

        Returns:
            配置列表
        """
        data_list = self.storage.list_profiles()
        return [LLMProfile.from_dict(data) for data in data_list]

    def activate_profile(self, profile_id: str) -> bool:
        """
        激活配置

        Args:
            profile_id: 配置 ID

        Returns:
            是否激活成功
        """
        profile = self.get_profile(profile_id)
        if profile:
            self._active_profile_id = profile_id
            self._save_active_id(profile_id)
            logger.info(f"Profile activated: {profile_id}")
            return True
        return False

    def get_active_profile(self) -> LLMProfile | None:
        """
        获取当前激活的配置

        Returns:
            当前激活的配置，如果没有激活返回 None
        """
        if self._active_profile_id:
            return self.get_profile(self._active_profile_id)
        return None

    def export_profile(self, profile_id: str, export_path: str) -> bool:
        """
        导出配置

        Args:
            profile_id: 配置 ID
            export_path: 导出路径

        Returns:
            是否导出成功
        """
        return self.storage.export_profile(profile_id, export_path)

    def import_profile(self, import_path: str) -> LLMProfile | None:
        """
        导入配置

        Args:
            import_path: 导入路径

        Returns:
            导入的配置文件，如果导入失败返回 None
        """
        profile_id = self.storage.import_profile(import_path)
        if profile_id:
            return self.get_profile(profile_id)
        return None
