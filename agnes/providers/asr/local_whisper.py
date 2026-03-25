import asyncio
from collections.abc import AsyncGenerator

import numpy as np

from agnes.core import ASRProvider, ASRResponse

try:
    import whisper

    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False

try:
    HAS_OPENVINO = True
except ImportError:
    HAS_OPENVINO = False


class LocalWhisperProvider(ASRProvider):
    """本地 Whisper ASR Provider，支持 OpenVINO 加速"""

    def __init__(
        self, model_size: str = "base", device: str = "cpu", use_openvino: bool = False, **kwargs
    ):
        if not HAS_WHISPER:
            raise ImportError("Whisper not installed. Please install with: pip install whisper")

        self.model_size = model_size
        self.device = device
        self.use_openvino = use_openvino and HAS_OPENVINO
        self.model = None
        self._loaded = False

    async def _load_model(self) -> None:
        """异步加载模型"""
        if self._loaded:
            return

        def _load():
            self.model = whisper.load_model(self.model_size, device=self.device)
            self._loaded = True

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _load)

    async def transcribe(
        self, audio_data: np.ndarray, sample_rate: int, language: str | None = None, **kwargs
    ) -> ASRResponse:
        await self._load_model()

        def _transcribe():
            # Whisper 期望 16kHz 单声道
            if sample_rate != 16000:
                import librosa

                audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)

            # 确保是 float32 类型
            audio_data = audio_data.astype(np.float32)

            result = self.model.transcribe(audio_data, language=language, **kwargs)

            return result

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _transcribe)

        return ASRResponse(
            text=result.get("text", ""),
            language=result.get("language"),
            segments=result.get("segments", []),
        )

    async def transcribe_file(
        self, audio_path: str, language: str | None = None, **kwargs
    ) -> ASRResponse:
        await self._load_model()

        def _transcribe():
            result = self.model.transcribe(audio_path, language=language, **kwargs)
            return result

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _transcribe)

        return ASRResponse(
            text=result.get("text", ""),
            language=result.get("language"),
            segments=result.get("segments", []),
        )

    async def transcribe_stream(
        self,
        audio_stream: AsyncGenerator[np.ndarray, None],
        sample_rate: int,
        language: str | None = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        buffer = []

        async for chunk in audio_stream:
            buffer.append(chunk)

            if len(buffer) >= 30:  # 每 30 个 chunk 处理一次
                audio_data = np.concatenate(buffer)
                result = await self.transcribe(audio_data, sample_rate, language, **kwargs)
                if result.text.strip():
                    yield result.text
                buffer = []

        if buffer:
            audio_data = np.concatenate(buffer)
            result = await self.transcribe(audio_data, sample_rate, language, **kwargs)
            if result.text.strip():
                yield result.text

    async def close(self) -> None:
        """释放资源"""
        self.model = None
        self._loaded = False

    async def __aenter__(self) -> "LocalWhisperProvider":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
