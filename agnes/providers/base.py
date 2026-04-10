"""
Provider 公共基类
提供通用的 LLM Provider 功能实现，减少重复代码
"""

from collections.abc import AsyncGenerator
from typing import Any

from agnes.core import LLMProvider, LLMResponse


class BaseProvider(LLMProvider):
    """
    Provider 公共基类

    提供通用的 generate/generate_stream 实现，
    子类只需实现 chat 和 chat_stream 方法
    """

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        """生成文本 - 通过构建消息列表调用 chat 方法"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self.chat(messages=messages, temperature=temperature, max_tokens=max_tokens, **kwargs)

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """流式生成文本 - 通过构建消息列表调用 chat_stream 方法"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async for token in self.chat_stream(
            messages=messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        ):
            yield token
