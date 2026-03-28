import asyncio
import queue
import sys
import threading
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import numpy as np

try:
    import sounddevice as sd

    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    dtype: str = "float32"
    blocksize: int = 1024
    device: int | None = None


class VAD:
    """基于 RMS 的语音活动检测，防噪音/防幻听"""

    def __init__(
        self,
        sample_rate: int = 16000,
        frame_duration_ms: int = 20,
        silence_threshold: float = 0.01,
        speech_threshold: float = 0.02,
        min_speech_frames: int = 10,
        min_silence_frames: int = 30,
    ):
        self.sample_rate = sample_rate
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        self.silence_threshold = silence_threshold
        self.speech_threshold = speech_threshold
        self.min_speech_frames = min_speech_frames
        self.min_silence_frames = min_silence_frames

        self._speech_frames = 0
        self._silence_frames = 0
        self._is_speech = False
        self._buffer: list[np.ndarray] = []

    @staticmethod
    def compute_rms(audio: np.ndarray) -> float:
        """计算音频信号的 RMS (Root Mean Square)"""
        return np.sqrt(np.mean(audio**2))

    def process_frame(self, audio_frame: np.ndarray) -> tuple[bool, np.ndarray | None]:
        """
        处理单帧音频

        Returns:
            (is_speech, utterance_audio): 是否为语音，完整的语音片段
        """
        rms = self.compute_rms(audio_frame)
        is_speech_frame = rms > self.speech_threshold
        is_silence_frame = rms < self.silence_threshold

        utterance = None

        if is_speech_frame:
            self._speech_frames += 1
            self._silence_frames = 0
            self._buffer.append(audio_frame)

            if self._speech_frames >= self.min_speech_frames and not self._is_speech:
                self._is_speech = True
        elif is_silence_frame:
            self._silence_frames += 1

            if self._is_speech:
                self._buffer.append(audio_frame)

                if self._silence_frames >= self.min_silence_frames:
                    # 语音结束，返回完整片段
                    utterance = np.concatenate(self._buffer)
                    self._is_speech = False
                    self._speech_frames = 0
                    self._buffer = []
        else:
            # 中间状态，继续积累
            if self._is_speech:
                self._buffer.append(audio_frame)
                self._silence_frames = 0

        return self._is_speech, utterance

    def reset(self) -> None:
        """重置 VAD 状态"""
        self._speech_frames = 0
        self._silence_frames = 0
        self._is_speech = False
        self._buffer = []


class AudioRecorder:
    """跨平台音频录音器"""

    def __init__(self, config: AudioConfig | None = None):
        if not HAS_SOUNDDEVICE:
            raise ImportError("sounddevice not installed. Please install with: pip install sounddevice")

        self.config = config or AudioConfig()
        self._stream: sd.InputStream | None = None
        self._audio_queue: queue.Queue = queue.Queue()
        self._is_recording = False
        self._recording_thread: threading.Thread | None = None

    def _audio_callback(self, indata, frames, time, status):
        """录音回调函数"""
        if status:
            print(f"Audio status: {status}", file=sys.stderr)

        audio_data = indata.copy().flatten()
        self._audio_queue.put(audio_data)

    def start(self) -> None:
        """开始录音"""
        if self._is_recording:
            return

        self._stream = sd.InputStream(
            samplerate=self.config.sample_rate,
            channels=self.config.channels,
            dtype=self.config.dtype,
            blocksize=self.config.blocksize,
            device=self.config.device,
            callback=self._audio_callback,
        )

        self._stream.start()
        self._is_recording = True

    def stop(self) -> None:
        """停止录音"""
        if not self._is_recording:
            return

        if self._stream:
            self._stream.stop()
            self._stream.close()

        self._is_recording = False
        self._stream = None

    def get_audio_chunk(self, timeout: float | None = None) -> np.ndarray | None:
        """获取一个音频块"""
        try:
            return self._audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    async def audio_stream(self) -> AsyncGenerator[np.ndarray, None]:
        """异步音频流"""
        loop = asyncio.get_event_loop()

        while self._is_recording:
            chunk = await loop.run_in_executor(None, lambda: self.get_audio_chunk(timeout=0.1))
            if chunk is not None:
                yield chunk

    def __enter__(self) -> "AudioRecorder":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


class AudioUtils:
    """音频工具类"""

    @staticmethod
    def resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """重采样音频"""
        if orig_sr == target_sr:
            return audio

        try:
            import librosa

            return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
        except ImportError:
            # 简单的重采样实现
            ratio = target_sr / orig_sr
            indices = np.arange(0, len(audio), 1 / ratio)
            indices = np.clip(indices, 0, len(audio) - 1).astype(int)
            return audio[indices]

    @staticmethod
    def normalize(audio: np.ndarray) -> np.ndarray:
        """归一化音频"""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio / max_val
        return audio

    @staticmethod
    def to_mono(audio: np.ndarray) -> np.ndarray:
        """转换为单声道"""
        if len(audio.shape) > 1:
            return np.mean(audio, axis=1)
        return audio

    @staticmethod
    def trim_silence(audio: np.ndarray, threshold: float = 0.01, min_silence_len: int = 1000) -> np.ndarray:
        """裁剪首尾静音"""
        if len(audio) == 0:
            return audio

        # 找到非静音的起始点
        start = 0
        for i in range(len(audio)):
            if abs(audio[i]) > threshold:
                start = max(0, i - min_silence_len)
                break

        # 找到非静音的结束点
        end = len(audio)
        for i in range(len(audio) - 1, -1, -1):
            if abs(audio[i]) > threshold:
                end = min(len(audio), i + min_silence_len)
                break

        return audio[start:end]
