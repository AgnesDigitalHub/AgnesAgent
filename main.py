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
    ChatHistory,
    ConfigLoader,
    LocalWhisperProvider,
    OllamaProvider,
    OpenAIProvider,
    OpenAIWhisperProvider,
    OpenVINOProvider,
    PromptTemplates,
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
        self.chat_history = None

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

        # 初始化对话历史
        self.chat_history = ChatHistory(max_messages=20)

        self.logger.info("AgnesAgent initialized successfully")

    def set_system_prompt(self, system_prompt: str):
        """设置系统提示词"""
        if self.chat_history:
            self.chat_history.add_system_message(system_prompt)

    async def chat(self, user_input: str, use_history: bool = True):
        """
        对话方法（支持对话历史）

        Args:
            user_input: 用户输入
            use_history: 是否使用对话历史

        Returns:
            LLMResponse: 模型响应
        """
        if not self.llm_provider:
            raise RuntimeError("LLM provider not initialized")

        self.logger.info(f"User input: {user_input}")

        if use_history and self.chat_history:
            self.chat_history.add_user_message(user_input)
            messages = self.chat_history.to_openai_format()
            response = await self.llm_provider.chat(
                messages=messages,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
            )
            self.chat_history.add_assistant_message(response.content)
        else:
            response = await self.llm_provider.generate(
                prompt=user_input,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
            )

        self.logger.info(f"Assistant response: {response.content}")
        return response

    async def chat_stream(self, user_input: str, use_history: bool = True):
        """
        流式对话方法（支持对话历史）

        Args:
            user_input: 用户输入
            use_history: 是否使用对话历史

        Yields:
            str: 生成的文本片段
        """
        if not self.llm_provider:
            raise RuntimeError("LLM provider not initialized")

        self.logger.info(f"User input (streaming): {user_input}")

        full_response = []

        if use_history and self.chat_history:
            self.chat_history.add_user_message(user_input)
            messages = self.chat_history.to_openai_format()
            async for token in self.llm_provider.chat_stream(
                messages=messages,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
            ):
                full_response.append(token)
                yield token
            self.chat_history.add_assistant_message("".join(full_response))
        else:
            async for token in self.llm_provider.generate_stream(
                prompt=user_input,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
            ):
                yield token

    def clear_history(self):
        """清空对话历史"""
        if self.chat_history:
            self.chat_history.clear()
            self.logger.info("Chat history cleared")

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


async def interactive_chat(agent: AgnesAgent):
    """交互式对话模式"""
    print("\n" + "=" * 50)
    print("Agnes 交互式对话")
    print("=" * 50)
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'clear' 清空对话历史")
    print("输入 'stream' 切换流式输出模式")
    print("=" * 50 + "\n")

    use_stream = False

    while True:
        try:
            user_input = input("你: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit"]:
                print("再见！")
                break

            if user_input.lower() == "clear":
                agent.clear_history()
                print("对话历史已清空\n")
                continue

            if user_input.lower() == "stream":
                use_stream = not use_stream
                print(f"流式输出: {'开启' if use_stream else '关闭'}\n")
                continue

            print("Agnes: ", end="", flush=True)

            if use_stream:
                async for token in agent.chat_stream(user_input):
                    print(token, end="", flush=True)
                print()
            else:
                response = await agent.chat(user_input)
                print(response.content)
            print()

        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n错误: {e}\n")


async def run_demo(agent: AgnesAgent):
    """运行演示"""
    print("\n" + "=" * 50)
    print("AgnesAgent 演示")
    print("=" * 50)

    # 设置默认系统提示词
    agent.set_system_prompt(PromptTemplates.DEFAULT_ASSISTANT.template)

    # 演示 1: 简单对话
    print("\n[演示 1] 简单对话")
    print("-" * 50)
    response = await agent.chat("你好，请介绍一下你自己。", use_history=False)
    print("你: 你好，请介绍一下你自己。")
    print(f"Agnes: {response.content}")

    # 演示 2: 多轮对话
    print("\n[演示 2] 多轮对话（使用历史记录）")
    print("-" * 50)
    agent.clear_history()
    agent.set_system_prompt(PromptTemplates.DEFAULT_ASSISTANT.template)

    response1 = await agent.chat("我叫小明")
    print("你: 我叫小明")
    print(f"Agnes: {response1.content}")

    response2 = await agent.chat("我叫什么名字？")
    print("你: 我叫什么名字？")
    print(f"Agnes: {response2.content}")

    # 演示 3: 流式输出
    print("\n[演示 3] 流式输出")
    print("-" * 50)
    agent.clear_history()
    print("你: 讲一个关于机器人的短故事")
    print("Agnes: ", end="", flush=True)
    async for token in agent.chat_stream("讲一个关于机器人的短故事"):
        print(token, end="", flush=True)
    print()

    # 演示 4: 角色模板
    print("\n[演示 4] 使用角色模板 - 编程专家")
    print("-" * 50)
    agent.clear_history()
    agent.set_system_prompt(PromptTemplates.CODE_EXPERT.template)
    response = await agent.chat("用 Python 写一个快速排序算法")
    print("你: 用 Python 写一个快速排序算法")
    print(f"Agnes:\n{response.content}")

    print("\n" + "=" * 50)
    print("演示完成！")
    print("=" * 50)


async def main():
    """主函数 - 演示用法"""
    import argparse

    parser = argparse.ArgumentParser(description="AgnesAgent - AI Agent Infrastructure")
    parser.add_argument("--config", default="config/config.yaml", help="Path to config file")
    parser.add_argument("--demo", action="store_true", help="Run demo")
    parser.add_argument("--chat", action="store_true", help="Interactive chat mode")
    parser.add_argument(
        "--list-templates", action="store_true", help="List available prompt templates"
    )
    args = parser.parse_args()

    if args.list_templates:
        print("可用的提示词模板:\n")
        for template in PromptTemplates.list_templates():
            print(f"  - {template.name}: {template.description}")
        return

    if not os.path.exists(args.config):
        print(f"Config file not found: {args.config}")
        print(f"Please copy config/config.yaml.example to {args.config} and edit it.")
        return

    async with AgnesAgent(args.config) as agent:
        if args.demo:
            await run_demo(agent)
        elif args.chat:
            await interactive_chat(agent)
        else:
            print("AgnesAgent - 高度可扩展、跨平台的 AI Agent 基础架构")
            print()
            print("使用方式:")
            print("  --demo           运行演示")
            print("  --chat           交互式对话模式")
            print("  --list-templates 列出可用的提示词模板")
            print("  --config FILE    指定配置文件")


if __name__ == "__main__":
    asyncio.run(main())
