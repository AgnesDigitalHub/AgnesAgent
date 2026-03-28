from .core import (
    ASRProvider,
    ASRResponse,
    ChatHistory,
    ChatMessage,
    LLMProvider,
    LLMResponse,
    PromptTemplate,
    Streamer,
)
from .provider_selector import ProviderSelector
from .providers import (
    LocalWhisperProvider,
    OllamaProvider,
    OpenAIProvider,
    OpenAIWhisperProvider,
    OpenVINOProvider,
)
from .utils import VAD, AudioRecorder, AudioUtils, ConfigLoader, get_logger

__version__ = "0.1.0"
__all__ = [
    "LLMProvider",
    "LLMResponse",
    "ASRProvider",
    "ASRResponse",
    "Streamer",
    "ChatHistory",
    "ChatMessage",
    "PromptTemplate",
    "OllamaProvider",
    "OpenAIProvider",
    "OpenVINOProvider",
    "LocalWhisperProvider",
    "OpenAIWhisperProvider",
    "AudioRecorder",
    "VAD",
    "AudioUtils",
    "get_logger",
    "ConfigLoader",
    "ProviderSelector",
]

# 可选的 Web 模块导入
try:
    from .web_server import start_web_server

    __all__.append("start_web_server")
except ImportError:
    start_web_server = None

# 可选的 Server 模块导入
try:
    from .config import ConfigManager, LLMProfile  # noqa: F401
    from .server import create_app  # noqa: F401

    __all__.extend(["ConfigManager", "LLMProfile", "create_app"])
except ImportError:
    pass
