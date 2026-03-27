"""
配置存储模块
"""

import json
import os
from pathlib import Path
from typing import Any

from agnes.utils import get_logger

logger = get_logger("agnes.config.storage")


class ConfigStorage:
    """配置存储管理器"""

    def __init__(self, storage_dir: str = "config/llm_profiles"):
        """
        初始化配置存储

        Args:
            storage_dir: 配置存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Config storage initialized at: {self.storage_dir}")

    def _get_profile_path(self, profile_id: str) -> Path:
        """获取配置文件路径"""
        return self.storage_dir / f"{profile_id}.json"

    def save_profile(self, profile_id: str, data: dict[str, Any]) -> bool:
        """
        保存配置

        Args:
            profile_id: 配置 ID
            data: 配置数据

        Returns:
            是否保存成功
        """
        try:
            profile_path = self._get_profile_path(profile_id)
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Profile saved: {profile_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save profile {profile_id}: {e}")
            return False

    def load_profile(self, profile_id: str) -> dict[str, Any] | None:
        """
        加载配置

        Args:
            profile_id: 配置 ID

        Returns:
            配置数据，如果不存在返回 None
        """
        profile_path = self._get_profile_path(profile_id)
        if not profile_path.exists():
            return None

        try:
            with open(profile_path, encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Profile loaded: {profile_id}")
            return data
        except Exception as e:
            logger.error(f"Failed to load profile {profile_id}: {e}")
            return None

    def delete_profile(self, profile_id: str) -> bool:
        """
        删除配置

        Args:
            profile_id: 配置 ID

        Returns:
            是否删除成功
        """
        profile_path = self._get_profile_path(profile_id)
        if not profile_path.exists():
            return False

        try:
            profile_path.unlink()
            logger.info(f"Profile deleted: {profile_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete profile {profile_id}: {e}")
            return False

    def list_profiles(self) -> list[dict[str, Any]]:
        """
        列出所有配置

        Returns:
            配置列表
        """
        profiles = []
        for profile_file in self.storage_dir.glob("*.json"):
            try:
                with open(profile_file, encoding="utf-8") as f:
                    data = json.load(f)
                profiles.append(data)
            except Exception as e:
                logger.warning(f"Failed to load profile {profile_file}: {e}")

        return sorted(profiles, key=lambda x: x.get("updated_at", 0), reverse=True)

    def export_profile(self, profile_id: str, export_path: str) -> bool:
        """
        导出配置

        Args:
            profile_id: 配置 ID
            export_path: 导出路径

        Returns:
            是否导出成功
        """
        data = self.load_profile(profile_id)
        if data is None:
            return False

        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Profile exported: {profile_id} -> {export_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export profile {profile_id}: {e}")
            return False

    def import_profile(self, import_path: str) -> str | None:
        """
        导入配置

        Args:
            import_path: 导入路径

        Returns:
            配置 ID，如果导入失败返回 None
        """
        try:
            with open(import_path, encoding="utf-8") as f:
                data = json.load(f)

            profile_id = data.get("id")
            if not profile_id:
                logger.error("Imported profile missing 'id' field")
                return None

            data["imported_at"] = os.path.getmtime(import_path)
            self.save_profile(profile_id, data)
            logger.info(f"Profile imported: {import_path} -> {profile_id}")
            return profile_id
        except Exception as e:
            logger.error(f"Failed to import profile {import_path}: {e}")
            return None
