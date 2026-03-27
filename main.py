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
    ProviderSelector,
    get_logger,
)


class AgnesAgent:
    """Agnes Agent 主类"""

    def __init__(self, config_path: str = "config.yaml", auto_initialize: bool = False):
        """
        初始化 AgnesAgent

        Args:
            config_path: 配置文件路径
            auto_initialize: 是否自动初始化所有组件（向后兼容）
        """
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
        self._llm_provider_display_name = None  # 用于显示的 provider 名称

        # 向后兼容：如果设置了 auto_initialize，则自动初始化
        if auto_initialize:
            self.logger.info("auto_initialize=True，将在 __aenter__ 中自动初始化所有组件")

    async def _init_llm_provider(self, llm_config=None, display_provider=None):
        """
        初始化 LLM Provider

        Args:
            llm_config: 可选的 LLM 配置，如果为 None 则使用配置文件中的设置
            display_provider: 可选的用于显示的 provider 名称
        """
        config = llm_config or self.config.llm
        provider_type = config.provider

        # 保存显示用的 provider 名称
        self._llm_provider_display_name = display_provider or provider_type

        if provider_type == "ollama":
            self.llm_provider = OllamaProvider(
                base_url=config.base_url or "http://localhost:11434",
                model=config.model,
                proxy=self.config.proxy.http_proxy,
            )
        elif provider_type in ["openai", "openvino-server", "local-api"]:
            if provider_type == "openai" and not config.api_key:
                raise ValueError("OpenAI API key is required")
            self.llm_provider = OpenAIProvider(
                api_key=config.api_key or "dummy-key",
                base_url=config.base_url or "https://api.openai.com/v1",
                model=config.model,
                proxy=self.config.proxy.http_proxy,
            )
        elif provider_type == "openvino":
            self.llm_provider = OpenVINOProvider(model_name_or_path=config.model)
        else:
            raise ValueError(f"Unknown LLM provider: {provider_type}")

        # 更新配置
        self.config.llm = config
        self.logger.info(f"Initialized LLM provider: {provider_type}")

    async def _init_asr_provider(self, asr_config=None):
        """
        初始化 ASR Provider

        Args:
            asr_config: 可选的 ASR 配置，如果为 None 则使用配置文件中的设置
        """
        config = asr_config or self.config.asr
        provider_type = config.provider

        if provider_type == "local_whisper":
            self.asr_provider = LocalWhisperProvider(model_size=config.model, use_openvino=config.use_openvino)
        elif provider_type == "openai_whisper":
            if not config.api_key:
                raise ValueError("OpenAI API key is required for ASR")
            self.asr_provider = OpenAIWhisperProvider(
                api_key=config.api_key,
                base_url=config.base_url or "https://api.openai.com/v1",
                proxy=self.config.proxy.http_proxy,
            )
        else:
            raise ValueError(f"Unknown ASR provider: {provider_type}")

        # 更新配置
        self.config.asr = config
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

    async def initialize(self, init_llm: bool = True, init_asr: bool = True, init_audio: bool = True):
        """
        初始化组件（按需初始化）

        Args:
            init_llm: 是否初始化 LLM
            init_asr: 是否初始化 ASR
            init_audio: 是否初始化音频组件
        """
        self.logger.info("Initializing AgnesAgent components...")

        if init_llm:
            await self._init_llm_provider()
        if init_asr:
            await self._init_asr_provider()
        if init_audio:
            self._init_audio()

        # 初始化对话历史
        if self.chat_history is None:
            self.chat_history = ChatHistory(max_messages=20)

        self.logger.info("AgnesAgent components initialized")

    async def setup_llm(self, llm_config=None, display_provider=None):
        """
        设置/切换 LLM Provider

        Args:
            llm_config: LLM 配置，如果为 None 则使用配置文件中的设置
            display_provider: 可选的用于显示的 provider 名称
        """
        # 关闭现有的 LLM provider
        if self.llm_provider and hasattr(self.llm_provider, "close"):
            await self.llm_provider.close()

        await self._init_llm_provider(llm_config, display_provider=display_provider)

    async def setup_asr(self, asr_config=None):
        """
        设置/切换 ASR Provider

        Args:
            asr_config: ASR 配置，如果为 None 则使用配置文件中的设置
        """
        # 关闭现有的 ASR provider
        if self.asr_provider and hasattr(self.asr_provider, "close"):
            await self.asr_provider.close()

        await self._init_asr_provider(asr_config)

    async def setup_audio(self):
        """设置音频组件"""
        self._init_audio()

    def get_current_llm_provider_name(self) -> str | None:
        """获取当前 LLM provider 名称"""
        if self.llm_provider:
            return self._llm_provider_display_name or self.config.llm.provider
        return None

    def get_current_asr_provider_name(self) -> str | None:
        """获取当前 ASR provider 名称"""
        if self.asr_provider:
            return self.config.asr.provider
        return None

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
            raise RuntimeError("LLM provider not initialized. Please call setup_llm() first.")

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
            raise RuntimeError("LLM provider not initialized. Please call setup_llm() first.")

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
        if not self.asr_provider:
            raise RuntimeError("ASR provider not initialized. Please call setup_asr() first.")
        if not self.audio_recorder:
            raise RuntimeError("Audio components not initialized. Please call setup_audio() first.")

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
        result = await self.asr_provider.transcribe(audio_data, sample_rate=self.config.audio.sample_rate)

        self.logger.info(f"Transcribed: {result.text}")
        return result

    async def close(self):
        """关闭所有资源"""
        self.logger.info("Shutting down AgnesAgent...")

        if self.llm_provider and hasattr(self.llm_provider, "close"):
            await self.llm_provider.close()

        if self.asr_provider and hasattr(self.asr_provider, "close"):
            await self.asr_provider.close()

        self.logger.info("AgnesAgent shut down")

    async def __aenter__(self):
        # 向后兼容：保持原有行为，但延迟初始化
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


async def start_agnes_server(agent, host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True):
    """启动新的 Agnes Server"""
    import threading
    import webbrowser

    from agnes.server import create_app

    app = create_app(agent)

    if open_browser:

        def open_browser_thread():
            import time

            time.sleep(1.5)
            webbrowser.open(f"http://{host}:{port}")

        threading.Thread(target=open_browser_thread, daemon=True).start()

    import uvicorn

    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)

    await server.serve()


async def interactive_chat(agent: AgnesAgent):
    """交互式对话模式 - 支持启动菜单和运行时切换"""
    print("\n" + "=" * 60)
    print("Agnes 交互式对话")
    print("=" * 60)
    print("特殊命令:")
    print("  'quit' / 'exit'  - 退出")
    print("  'clear'           - 清空对话历史")
    print("  'stream'          - 切换流式输出模式")
    print("  'switch llm'      - 切换 LLM Provider")
    print("  'switch asr'      - 切换 ASR Provider")
    print("  'status'          - 查看当前状态")
    print("=" * 60 + "\n")

    use_stream = False

    while True:
        try:
            # 显示当前状态
            ProviderSelector.print_current_providers(
                agent.get_current_llm_provider_name(), agent.get_current_asr_provider_name()
            )

            user_input = input("\n你: ").strip()

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

            if user_input.lower() == "status":
                continue

            if user_input.lower().startswith("switch llm"):
                llm_config = ProviderSelector.select_llm_provider(agent.config)
                await agent.setup_llm(llm_config)
                print(f"\n已切换到 LLM Provider: {llm_config.provider}\n")
                continue

            if user_input.lower().startswith("switch asr"):
                asr_config = ProviderSelector.select_asr_provider(agent.config)
                await agent.setup_asr(asr_config)
                print(f"\n已切换到 ASR Provider: {asr_config.provider}\n")
                continue

            # 检查 LLM 是否已初始化
            if not agent.llm_provider:
                print("\nLLM Provider 未初始化，请先配置！")
                llm_config = ProviderSelector.select_llm_provider(agent.config)
                await agent.setup_llm(llm_config)
                print(f"\n已初始化 LLM Provider: {llm_config.provider}\n")
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


async def main():
    """主函数 - 演示用法"""
    import argparse

    parser = argparse.ArgumentParser(description="AgnesAgent - AI Agent Infrastructure")
    parser.add_argument("--config", default="config/config.yaml", help="Path to config file")
    parser.add_argument("--chat", action="store_true", help="Interactive chat mode")
    parser.add_argument("--list-templates", action="store_true", help="List available prompt templates")
    parser.add_argument(
        "--no-select",
        action="store_true",
        help="Skip provider selection menu (use config directly)",
    )
    parser.add_argument("--web", action="store_true", help="Start old web server (deprecated)")
    parser.add_argument("--no-server", action="store_true", help="Do not start Agnes Server (default is to start server)")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--web2", action="store_true", help="Start Web2 Amis SPA console")
    parser.add_argument("--reload", action="store_true", help="Auto reload schema on each request (dev mode)")
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
        # 初始化对话历史
        if agent.chat_history is None:
            agent.chat_history = ChatHistory(max_messages=20)

        llm_config = None
        asr_config = None

        # 显示启动菜单（除非使用 --no-select）
        if args.chat and not args.no_select:
            llm_config, asr_config = ProviderSelector.show_start_menu(agent.config)

        # 初始化选择的 provider
        if llm_config:
            await agent.setup_llm(llm_config)
        if asr_config:
            await agent.setup_asr(asr_config)

        if args.chat:
            await interactive_chat(agent)
        elif args.web:
            try:
                from agnes.web_server import start_web_server
                await start_web_server(agent, args.host, args.port)
            except ImportError:
                print("Web dependencies not installed!")
                print("Please install with: pip install -e .[web]")
                return
        elif args.web2:
            # 启动 Web2 Amis SPA 控制台
            try:
                from web2.main import create_app
                import uvicorn
                import threading
                import webbrowser
                from fastapi import FastAPI, HTTPException
                from fastapi.middleware.cors import CORSMiddleware
                from fastapi.responses import StreamingResponse

                # 创建 web2 应用
                web2_app = create_app(reload=args.reload)

                # 创建干净的主应用，不使用 agnes.server.create_app 避免冲突路由
                main_app = FastAPI(title="AgnesAgent Web2", version="2.0.0")
                
                # CORS 配置
                main_app.add_middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
                
                # 添加favicon路由
                from fastapi.responses import FileResponse
                
                @main_app.get("/favicon.ico")
                @main_app.get("/icon.png")
                async def favicon():
                    """网站图标"""
                    # 先尝试 favicon.ico
                    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
                    if os.path.exists(icon_path):
                        return FileResponse(icon_path, media_type="image/x-icon")
                    # 再尝试 icon.png
                    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favicon.ico")
                    if os.path.exists(icon_path):
                        return FileResponse(icon_path, media_type="image/png")
                    raise HTTPException(status_code=404, detail="Icon not found")
                
                # 只保留必要的 OpenAI 兼容 API（从 agnes.server 复制过来核心功能）
                from agnes.server.models import (
                    ChatCompletionRequest,
                )
                from agnes.server.api import stream_openai_response, create_openai_response
                
                # 添加 OpenAI 兼容 API
                @main_app.post("/v1/chat/completions")
                async def chat_completions(request: ChatCompletionRequest):
                    """OpenAI 兼容的聊天补全 API"""
                    if not agent.llm_provider:
                        raise HTTPException(status_code=500, detail="LLM provider not initialized")

                    if request.stream:
                        return StreamingResponse(
                            stream_openai_response(agent, request),
                            media_type="text/event-stream",
                        )
                    else:
                        return create_openai_response(agent, request)
                
                # 直接把 web2_app 的路由挂载到根
                # 用户要求全部改成根路径，不要 /web2 前缀
                from fastapi import APIRouter
                for route in web2_app.routes:
                    main_app.routes.append(route)

                if not args.no_browser:
                    def open_browser_thread():
                        import time
                        time.sleep(1.5)
                        webbrowser.open(f"http://{args.host}:{args.port}/")

                    threading.Thread(target=open_browser_thread, daemon=True).start()

                config = uvicorn.Config(main_app, host=args.host, port=args.port, log_level="info")
                server = uvicorn.Server(config)
                await server.serve()
            except ImportError as e:
                print(f"Web2 dependencies not installed: {e}")
                print("Please install with: uv sync")
                return
        elif not args.no_server:
            # 默认启动 Agnes Server
            try:
                await start_agnes_server(agent, args.host, args.port, not args.no_browser)
            except ImportError:
                print("Server dependencies not installed!")
                print("Please install with: uv sync")
                return
        else:
            print("AgnesAgent - 高度可扩展、跨平台的 AI Agent 基础架构")
            print()
            print("使用方式:")
            print("  (默认)          启动 Agnes Server")
            print("  --web2           启动 Web2 Amis SPA 控制台")
            print("  --chat           交互式对话模式")
            print("  --no-server      不启动 Agnes Server")
            print("  --web            启动旧版 Web 服务器 (已弃用)")
            print("  --list-templates 列出可用的提示词模板")
            print("  --config FILE    指定配置文件")
            print("  --no-select      跳过 provider 选择菜单")
            print("  --reload         开发模式：每次请求重新加载 schema")


if __name__ == "__main__":
    asyncio.run(main())
