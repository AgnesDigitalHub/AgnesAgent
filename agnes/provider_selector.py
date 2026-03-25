"""
Provider Selector - 交互式选择 LLM 和 ASR provider
"""

import os
from typing import Any

from agnes.utils.config_loader import ASRConfig, Config, LLMConfig


class ProviderSelector:
    """Provider 选择器"""

    LLM_PROVIDERS = ["ollama", "openai", "openvino"]
    ASR_PROVIDERS = ["local_whisper", "openai_whisper"]

    @classmethod
    def select_llm_provider(cls, config: Config | None = None) -> LLMConfig:
        """
        交互式选择 LLM provider

        Args:
            config: 现有配置（用于提供默认值）

        Returns:
            LLMConfig: 选择的 LLM 配置
        """
        print("\n" + "=" * 60)
        print("选择 LLM Provider")
        print("=" * 60)

        default_provider = config.llm.provider if config else "ollama"

        for i, provider in enumerate(cls.LLM_PROVIDERS, 1):
            default_mark = " [默认]" if provider == default_provider else ""
            print(f"  {i}. {provider}{default_mark}")

        choice = input(f"\n请选择 [1-{len(cls.LLM_PROVIDERS)}]: ").strip()

        if not choice:
            provider_type = default_provider
        else:
            try:
                idx = int(choice) - 1
                provider_type = cls.LLM_PROVIDERS[idx]
            except (ValueError, IndexError):
                print(f"无效选择，使用默认: {default_provider}")
                provider_type = default_provider

        return cls._configure_llm(provider_type, config)

    @classmethod
    def _configure_llm(cls, provider_type: str, config: Config | None) -> LLMConfig:
        """配置 LLM 参数"""
        llm_config = LLMConfig(provider=provider_type)

        if config:
            llm_config.temperature = config.llm.temperature
            llm_config.max_tokens = config.llm.max_tokens

        print(f"\n配置 {provider_type} provider:")

        if provider_type == "ollama":
            default_model = config.llm.model if config and config.llm.provider == "ollama" else "llama2"
            llm_config.model = input(f"  模型名称 [{default_model}]: ").strip() or default_model

            default_base_url = (
                config.llm.base_url
                if config and config.llm.provider == "ollama"
                else "http://localhost:11434"
            )
            base_url = input(f"  Base URL [{default_base_url}]: ").strip()
            llm_config.base_url = base_url or default_base_url

        elif provider_type == "openai":
            default_model = (
                config.llm.model if config and config.llm.provider == "openai" else "gpt-3.5-turbo"
            )
            llm_config.model = input(f"  模型名称 [{default_model}]: ").strip() or default_model

            default_base_url = (
                config.llm.base_url
                if config and config.llm.provider == "openai"
                else "https://api.openai.com/v1"
            )
            base_url = input(f"  Base URL [{default_base_url}]: ").strip()
            llm_config.base_url = base_url or default_base_url

            current_api_key = config.llm.api_key if config and config.llm.provider == "openai" else ""
            if current_api_key:
                mask = "*" * min(len(current_api_key), 8)
                api_key = input(f"  API Key [{mask}]: ").strip()
                llm_config.api_key = api_key or current_api_key
            else:
                llm_config.api_key = input("  API Key: ").strip()

        elif provider_type == "openvino":
            default_model = (
                config.llm.model if config and config.llm.provider == "openvino" else "llama2"
            )
            llm_config.model = input(f"  模型名称/路径 [{default_model}]: ").strip() or default_model

        return llm_config

    @classmethod
    def select_asr_provider(cls, config: Config | None = None) -> ASRConfig:
        """
        交互式选择 ASR provider

        Args:
            config: 现有配置（用于提供默认值）

        Returns:
            ASRConfig: 选择的 ASR 配置
        """
        print("\n" + "=" * 60)
        print("选择 ASR Provider")
        print("=" * 60)

        default_provider = config.asr.provider if config else "local_whisper"

        for i, provider in enumerate(cls.ASR_PROVIDERS, 1):
            default_mark = " [默认]" if provider == default_provider else ""
            print(f"  {i}. {provider}{default_mark}")

        choice = input(f"\n请选择 [1-{len(cls.ASR_PROVIDERS)}]: ").strip()

        if not choice:
            provider_type = default_provider
        else:
            try:
                idx = int(choice) - 1
                provider_type = cls.ASR_PROVIDERS[idx]
            except (ValueError, IndexError):
                print(f"无效选择，使用默认: {default_provider}")
                provider_type = default_provider

        return cls._configure_asr(provider_type, config)

    @classmethod
    def _configure_asr(cls, provider_type: str, config: Config | None) -> ASRConfig:
        """配置 ASR 参数"""
        asr_config = ASRConfig(provider=provider_type)

        print(f"\n配置 {provider_type} provider:")

        if provider_type == "local_whisper":
            default_model = (
                config.asr.model if config and config.asr.provider == "local_whisper" else "base"
            )
            asr_config.model = input(f"  模型大小 [{default_model}]: ").strip() or default_model

            default_use_openvino = (
                config.asr.use_openvino if config and config.asr.provider == "local_whisper" else False
            )
            use_openvino = input(f"  使用 OpenVINO 加速 (y/n) [{'y' if default_use_openvino else 'n'}]: ").strip().lower()
            asr_config.use_openvino = (use_openvino == "y") if use_openvino else default_use_openvino

        elif provider_type == "openai_whisper":
            default_base_url = (
                config.asr.base_url
                if config and config.asr.provider == "openai_whisper"
                else "https://api.openai.com/v1"
            )
            base_url = input(f"  Base URL [{default_base_url}]: ").strip()
            asr_config.base_url = base_url or default_base_url

            current_api_key = (
                config.asr.api_key if config and config.asr.provider == "openai_whisper" else ""
            )
            if current_api_key:
                mask = "*" * min(len(current_api_key), 8)
                api_key = input(f"  API Key [{mask}]: ").strip()
                asr_config.api_key = api_key or current_api_key
            else:
                asr_config.api_key = input("  API Key: ").strip()

        return asr_config

    @classmethod
    def show_start_menu(cls, config: Config | None = None) -> tuple[LLMConfig | None, ASRConfig | None]:
        """
        显示启动菜单

        Args:
            config: 现有配置

        Returns:
            tuple: (llm_config, asr_config)，如果跳过选择则为 None
        """
        print("\n" + "=" * 60)
        print("AgnesAgent 启动菜单")
        print("=" * 60)
        print("  1. 配置并选择 LLM Provider")
        print("  2. 配置并选择 ASR Provider")
        print("  3. 配置 LLM + ASR")
        print("  4. 使用配置文件中的默认设置")
        print("=" * 60)

        choice = input("\n请选择 [1-4]: ").strip()

        llm_config = None
        asr_config = None

        if choice == "1":
            llm_config = cls.select_llm_provider(config)
        elif choice == "2":
            asr_config = cls.select_asr_provider(config)
        elif choice == "3":
            llm_config = cls.select_llm_provider(config)
            asr_config = cls.select_asr_provider(config)
        elif choice == "4":
            print("\n使用配置文件中的默认设置")
        else:
            print("\n无效选择，使用配置文件中的默认设置")

        return llm_config, asr_config

    @classmethod
    def print_current_providers(cls, llm_provider_name: str | None, asr_provider_name: str | None):
        """打印当前使用的 provider 信息"""
        print("\n" + "-" * 60)
        print("当前 Provider:")
        print(f"  LLM: {llm_provider_name or '未初始化'}")
        print(f"  ASR: {asr_provider_name or '未初始化'}")
        print("-" * 60)