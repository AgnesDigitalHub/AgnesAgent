#!/usr/bin/env python3
"""
AgnesAgent - 高度可扩展、跨平台的 AI Agent 基础架构
"""

import asyncio
import logging
import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agnes import (
    VAD,
    AudioRecorder,
    ConfigLoader,
    LocalWhisperProvider,
    OllamaProvider,
    OpenAIProvider,
    OpenAIWhisperProvider,
    OpenVINOProvider,
    get_logger,
)


class AgnesAgent:
    """Agnes Agent 主类"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.config

        # 设置代理环境变量
        self.config_loader.set_proxy_env(self.config)

        # 初始化 logger
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        self.logger = get_logger("agnes", level=log_level, log_file=self.config.log_file)

        self.llm_provider = None
        self.asr_provider = None
        self.audio_recorder = None
        self.vad = None

    async def _init_llm_provider(self):
        """初始化 LLM Provider"""
        provider_type = self.config.llm.provider

        if provider_type == "ollama":
            self.llm_provider = OllamaProvider(
                base_url=self.config.llm.base_url or "http://localhost:11434",
                model=self.config.llm.model,
                proxy=self.config.proxy.http_proxy,
            )
        elif provider_type == "openai":
            if not self.config.llm.api_key:
                raise ValueError("OpenAI API key is required")
            self.llm_provider = OpenAIProvider(
                api_key=self.config.llm.api_key,
                base_url=self.config.llm.base_url or "https://api.openai.com/v1",
                model=self.config.llm.model,
                proxy=self.config.proxy.http_proxy,
            )
        elif provider_type == "openvino":
            self.llm_provider = OpenVINOProvider(model_name_or_path=self.config.llm.model)
        else:
            raise ValueError(f"Unknown LLM provider: {provider_type}")

        self.logger.info(f"Initialized LLM provider: {provider_type}")

    async def _init_asr_provider(self):
        """初始化 ASR Provider"""
        provider_type = self.config.asr.provider

        if provider_type == "local_whisper":
            self.asr_provider = LocalWhisperProvider(
                model_size=self.config.asr.model, use_openvino=self.config.asr.use_openvino
            )
        elif provider_type == "openai_whisper":
            if not self.config.asr.api_key:
                raise ValueError("OpenAI API key is required for ASR")
            self.asr_provider = OpenAIWhisperProvider(
                api_key=self.config.asr.api_key,
                base_url=self.config.asr.base_url or "https://api.openai.com/v1",
                proxy=self.config.proxy.http_proxy,
            )
        else:
            raise ValueError(f"Unknown ASR provider: {provider_type}")

        self.logger.info(f"Initialized ASR provider: {provider_type}")

    def _init_audio(self):
        """初始化音频组件"""
        from agnes.utils.audio import AudioConfig as AudioUtilsConfig

        audio_config = AudioUtilsConfig(
            sample_rate=self.config.audio.sample_rate,
            channels=self.config.audio.channels,
            blocksize=self.config.audio.blocksize,
            device=self.config.audio.device,
        )

        self.audio_recorder = AudioRecorder(audio_config)
        self.vad = VAD(
            sample_rate=self.config.audio.sample_rate,
            silence_threshold=self.config.vad.silence_threshold,
            speech_threshold=self.config.vad.speech_threshold,
            min_speech_frames=self.config.vad.min_speech_frames,
            min_silence_frames=self.config.vad.min_silence_frames,
        )

        self.logger.info("Initialized audio components")

    async def initialize(self):
        """初始化所有组件"""
        self.logger.info("Initializing AgnesAgent...")

        await self._init_llm_provider()
        await self._init_asr_provider()
        self._init_audio()

        self.logger.info("AgnesAgent initialized successfully")

    async def chat(self, user_input: str, system_prompt: str | None = None):
        """
        简单的对话方法

        Args:
            user_input: 用户输入
            system_prompt: 系统提示词

        Returns:
            LLMResponse: 模型响应
        """
        if not self.llm_provider:
            raise RuntimeError("LLM provider not initialized")

        self.logger.info(f"User input: {user_input}")

        response = await self.llm_provider.generate(
            prompt=user_input,
            system_prompt=system_prompt,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
        )

        self.logger.info(f"Assistant response: {response.content}")
        return response

    async def chat_stream(self, user_input: str, system_prompt: str | None = None):
        """
        流式对话方法

        Args:
            user_input: 用户输入
            system_prompt: 系统提示词

        Yields:
            str: 生成的文本片段
        """
        if not self.llm_provider:
            raise RuntimeError("LLM provider not initialized")

        self.logger.info(f"User input (streaming): {user_input}")

        async for token in self.llm_provider.generate_stream(
            prompt=user_input,
            system_prompt=system_prompt,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
        ):
            yield token

    async def listen_and_transcribe(self, duration: float | None = None):
        """
        录音并转录

        Args:
            duration: 录音时长（秒），如果为 None 则使用 VAD 自动检测

        Returns:
            ASRResponse: 转录结果
        """
        if not self.asr_provider or not self.audio_recorder:
            raise RuntimeError("ASR or audio components not initialized")

        self.logger.info("Listening...")

        audio_buffer = []

        with self.audio_recorder:
            if duration:
                await asyncio.sleep(duration)
                while True:
                    chunk = self.audio_recorder.get_audio_chunk(timeout=0.1)
                    if chunk is None:
                        break
                    audio_buffer.append(chunk)
            else:
                self.vad.reset()
                is_speaking = False

                while True:
                    chunk = self.audio_recorder.get_audio_chunk(timeout=0.1)
                    if chunk is None:
                        await asyncio.sleep(0.01)
                        continue

                    in_speech, utterance = self.vad.process_frame(chunk)

                    if in_speech and not is_speaking:
                        self.logger.info("Speech detected...")
                        is_speaking = True

                    if utterance is not None:
                        self.logger.info("Speech ended, transcribing...")
                        import numpy as np

                        audio_data = utterance
                        break

                    audio_buffer.append(chunk)

                if not utterance and audio_buffer:
                    import numpy as np

                    audio_data = np.concatenate(audio_buffer)

        self.logger.info("Transcribing...")
        result = await self.asr_provider.transcribe(
            audio_data, sample_rate=self.config.audio.sample_rate
        )

        self.logger.info(f"Transcribed: {result.text}")
        return result

    async def close(self):
        """关闭所有资源"""
        self.logger.info("Shutting down AgnesAgent...")

        if hasattr(self.llm_provider, "close"):
            await self.llm_provider.close()

        if hasattr(self.asr_provider, "close"):
            await self.asr_provider.close()

        self.logger.info("AgnesAgent shut down")

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


async def main():
    """主函数 - 演示用法"""
    import argparse

    parser = argparse.ArgumentParser(description="AgnesAgent - AI Agent Infrastructure")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--demo", action="store_true", help="Run demo")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Config file not found: {args.config}")
        print(f"Please copy config.yaml.example to {args.config} and edit it.")
        return

    if args.demo:
        async with AgnesAgent(args.config) as agent:
            # 简单文本对话演示
            print("\n=== 文本对话演示 ===")
            response = await agent.chat(
                "你好，请介绍一下你自己。", system_prompt="你是 Agnes，一个友好的 AI 助手。"
            )
            print(f"Agnes: {response.content}")

            # 流式输出演示
            print("\n=== 流式输出演示 ===")
            print("Agnes: ", end="", flush=True)
            async for token in agent.chat_stream("讲一个短故事"):
                print(token, end="", flush=True)
            print()
    else:
        print("AgnesAgent - 高度可扩展、跨平台的 AI Agent 基础架构")
        print("使用 --demo 参数运行演示")
        print("使用 --config 参数指定配置文件")


if __name__ == "__main__":
    asyncio.run(main())
