import os
from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class LLMConfig:
    provider: str = "ollama"
    model: str = "llama2"
    base_url: str | None = None
    api_key: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None


@dataclass
class ASRConfig:
    provider: str = "local_whisper"
    model: str = "base"
    api_key: str | None = None
    base_url: str | None = None
    use_openvino: bool = False


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    blocksize: int = 1024
    device: int | None = None


@dataclass
class VADConfig:
    silence_threshold: float = 0.01
    speech_threshold: float = 0.02
    min_speech_frames: int = 10
    min_silence_frames: int = 30


@dataclass
class ProxyConfig:
    http_proxy: str | None = None
    https_proxy: str | None = None


@dataclass
class Config:
    llm: LLMConfig = field(default_factory=LLMConfig)
    asr: ASRConfig = field(default_factory=ASRConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    vad: VADConfig = field(default_factory=VADConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    log_level: str = "INFO"
    log_file: str | None = None


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self._config: Config | None = None

    def load(self, config_path: str | None = None) -> Config:
        """
        加载配置文件

        Args:
            config_path: 配置文件路径，如果为 None 则使用初始化时的路径

        Returns:
            Config: 配置对象
        """
        path = config_path or self.config_path

        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        return self._parse_config(config_data)

    def _parse_config(self, data: dict[str, Any]) -> Config:
        """解析配置数据"""
        config = Config()

        if "llm" in data and data["llm"] is not None:
            llm_data = data["llm"]
            config.llm = LLMConfig(
                provider=llm_data.get("provider", config.llm.provider),
                model=llm_data.get("model", config.llm.model),
                base_url=llm_data.get("base_url"),
                api_key=llm_data.get("api_key"),
                temperature=llm_data.get("temperature", config.llm.temperature),
                max_tokens=llm_data.get("max_tokens"),
            )

        if "asr" in data and data["asr"] is not None:
            asr_data = data["asr"]
            config.asr = ASRConfig(
                provider=asr_data.get("provider", config.asr.provider),
                model=asr_data.get("model", config.asr.model),
                api_key=asr_data.get("api_key"),
                base_url=asr_data.get("base_url"),
                use_openvino=asr_data.get("use_openvino", config.asr.use_openvino),
            )

        if "audio" in data and data["audio"] is not None:
            audio_data = data["audio"]
            config.audio = AudioConfig(
                sample_rate=audio_data.get("sample_rate", config.audio.sample_rate),
                channels=audio_data.get("channels", config.audio.channels),
                blocksize=audio_data.get("blocksize", config.audio.blocksize),
                device=audio_data.get("device"),
            )

        if "vad" in data and data["vad"] is not None:
            vad_data = data["vad"]
            config.vad = VADConfig(
                silence_threshold=vad_data.get("silence_threshold", config.vad.silence_threshold),
                speech_threshold=vad_data.get("speech_threshold", config.vad.speech_threshold),
                min_speech_frames=vad_data.get("min_speech_frames", config.vad.min_speech_frames),
                min_silence_frames=vad_data.get(
                    "min_silence_frames", config.vad.min_silence_frames
                ),
            )

        if "proxy" in data and data["proxy"] is not None:
            proxy_data = data["proxy"]
            config.proxy = ProxyConfig(
                http_proxy=proxy_data.get("http_proxy"), https_proxy=proxy_data.get("https_proxy")
            )

        config.log_level = data.get("log_level", config.log_level)
        config.log_file = data.get("log_file")

        return config

    def set_proxy_env(self, config: Config) -> None:
        """设置代理环境变量"""
        if config.proxy.http_proxy:
            os.environ["http_proxy"] = config.proxy.http_proxy
        if config.proxy.https_proxy:
            os.environ["https_proxy"] = config.proxy.https_proxy

    @property
    def config(self) -> Config:
        """获取配置对象"""
        if self._config is None:
            self._config = self.load()
        return self._config
