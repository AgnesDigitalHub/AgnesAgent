"""
系统设置存储模块 - 分类 JSON 存储
"""

import json
import os
from pathlib import Path
from typing import Any

from agnes.utils import get_logger

logger = get_logger("agnes.config.settings_storage")

# 所有支持的配置分类
SETTINGS_SECTIONS = ["llm", "asr", "audio", "vad", "proxy", "general"]

# 每个分类���默认值
DEFAULT_SETTINGS: dict[str, dict[str, Any]] = {
    "llm": {
        "provider": "ollama",
        "model": "llama2",
        "base_url": "http://localhost:11434",
        "api_key": None,
        "temperature": 0.7,
        "max_tokens": 1024,
    },
    "asr": {
        "provider": "local_whisper",
        "model": "base",
        "api_key": None,
        "base_url": None,
        "use_openvino": False,
    },
    "audio": {
        "sample_rate": 16000,
        "channels": 1,
        "blocksize": 1024,
        "device": None,
    },
    "vad": {
        "silence_threshold": 0.01,
        "speech_threshold": 0.02,
        "min_speech_frames": 10,
        "min_silence_frames": 30,
    },
    "proxy": {
        "http_proxy": None,
        "https_proxy": None,
    },
    "general": {
        "log_level": "INFO",
        "log_file": None,
    },
}


class SettingsStorage:
    """分类 JSON 配置存储"""

    def __init__(self, settings_dir: str = "config/settings"):
        self.settings_dir = Path(settings_dir)
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Settings storage initialized at: {self.settings_dir}")

    def _get_path(self, section: str) -> Path:
        return self.settings_dir / f"{section}.json"

    def load_section(self, section: str) -> dict[str, Any]:
        """加载某分类配置，如不存在���返回默认值"""
        if section not in SETTINGS_SECTIONS:
            raise ValueError(f"Unknown settings section: {section}")

        path = self._get_path(section)
        defaults = DEFAULT_SETTINGS.get(section, {})

        if not path.exists():
            return dict(defaults)

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            # 用默认值填充缺失字段
            merged = dict(defaults)
            merged.update(data)
            return merged
        except Exception as e:
            logger.error(f"Failed to load settings section {section}: {e}")
            return dict(defaults)

    def save_section(self, section: str, data: dict[str, Any]) -> bool:
        """保存某分类配置"""
        if section not in SETTINGS_SECTIONS:
            raise ValueError(f"Unknown settings section: {section}")

        try:
            path = self._get_path(section)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Settings section saved: {section}")
            return True
        except Exception as e:
            logger.error(f"Failed to save settings section {section}: {e}")
            return False

    def load_all(self) -> dict[str, dict[str, Any]]:
        """加载所有分类配置"""
        return {section: self.load_section(section) for section in SETTINGS_SECTIONS}

    def save_all(self, all_data: dict[str, dict[str, Any]]) -> bool:
        """保存所有分类配置"""
        success = True
        for section, data in all_data.items():
            if section in SETTINGS_SECTIONS:
                if not self.save_section(section, data):
                    success = False
        return success

    def sync_from_yaml(self, config_path: str = "config/config.yaml") -> bool:
        """
        从 config.yaml 同步到分类 JSON（初始化时使用）
        """
        try:
            import yaml

            if not os.path.exists(config_path):
                logger.warning(f"config.yaml not found at {config_path}, using defaults")
                return False

            with open(config_path, encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}

            mapping = {
                "llm": "llm",
                "asr": "asr",
                "audio": "audio",
                "vad": "vad",
                "proxy": "proxy",
            }

            for section, yaml_key in mapping.items():
                if yaml_key in raw and raw[yaml_key]:
                    merged = dict(DEFAULT_SETTINGS.get(section, {}))
                    merged.update(raw[yaml_key])
                    self.save_section(section, merged)

            # general
            general = dict(DEFAULT_SETTINGS["general"])
            if "log_level" in raw:
                general["log_level"] = raw["log_level"]
            if "log_file" in raw:
                general["log_file"] = raw["log_file"]
            self.save_section("general", general)

            logger.info("Settings synced from config.yaml")
            return True
        except Exception as e:
            logger.error(f"Failed to sync from yaml: {e}")
            return False
