import io
from collections.abc import AsyncGenerator

import numpy as np
import soundfile as sf
from openai import AsyncOpenAI

from agnes.core import ASRProvider, ASRResponse


class OpenAIWhisperProvider(ASRProvider):
    """OpenAI Whisper ASR Provider，API 调用"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "whisper-1",
        proxy: str | None = None,
        **kwargs,
    ):
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        if proxy:
            import httpx

            self.client._client = httpx.AsyncClient(proxies=proxy, timeout=300.0)

    async def transcribe(
        self, audio_data: np.ndarray, sample_rate: int, language: str | None = None, **kwargs
    ) -> ASRResponse:
        # 将 numpy 数组转换为 WAV 格式
        buffer = io.BytesIO()
        sf.write(buffer, audio_data, sample_rate, format="WAV")
        buffer.seek(0)

        try:
            transcript = await self.client.audio.transcriptions.create(
                model=self.model,
                file=("audio.wav", buffer, "audio/wav"),
                language=language,
                response_format="verbose_json",
                **kwargs,
            )

            return ASRResponse(
                text=transcript.text,
                language=getattr(transcript, "language", language),
                segments=getattr(transcript, "segments", []),
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI Whisper transcription failed: {str(e)}")

    async def transcribe_file(
        self, audio_path: str, language: str | None = None, **kwargs
    ) -> ASRResponse:
        try:
            with open(audio_path, "rb") as f:
                transcript = await self.client.audio.transcriptions.create(
                    model=self.model,
                    file=f,
                    language=language,
                    response_format="verbose_json",
                    **kwargs,
                )

            return ASRResponse(
                text=transcript.text,
                language=getattr(transcript, "language", language),
                segments=getattr(transcript, "segments", []),
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI Whisper file transcription failed: {str(e)}")

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

            if len(buffer) >= 50:  # 每 50 个 chunk 处理一次
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
        """关闭 client"""
        await self.client.close()

    async def __aenter__(self) -> "OpenAIWhisperProvider":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
