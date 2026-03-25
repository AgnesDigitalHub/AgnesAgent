from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class ASRResponse:
    text: str
    language: str | None = None
    confidence: float | None = None
    segments: list | None = None
    metadata: dict[str, Any] | None = None


class ASRProvider(ABC):
    """ASR Provider 抽象基类"""

    @abstractmethod
    async def transcribe(
        self, audio_data: np.ndarray, sample_rate: int, language: str | None = None, **kwargs
    ) -> ASRResponse:
        pass

    @abstractmethod
    async def transcribe_file(
        self, audio_path: str, language: str | None = None, **kwargs
    ) -> ASRResponse:
        pass

    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: AsyncGenerator[np.ndarray, None],
        sample_rate: int,
        language: str | None = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        pass
