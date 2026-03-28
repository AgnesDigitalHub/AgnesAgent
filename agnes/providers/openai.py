from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from agnes.core import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI LLM Provider，支持自定义 base_url"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-3.5-turbo",
        proxy: str | None = None,
        **kwargs,
    ):
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, http_client=None)

        if proxy:
            import httpx

            self.client._client = httpx.AsyncClient(proxies=proxy, timeout=300.0)

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
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
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async for token in self.chat_stream(
            messages=messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        ):
            yield token

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
                **kwargs,
            )

            choice = response.choices[0]
            return LLMResponse(
                content=choice.message.content or "",
                model=self.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }
                if response.usage
                else None,
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI chat failed: {str(e)}")

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise RuntimeError(f"OpenAI chat stream failed: {str(e)}")

    async def close(self) -> None:
        """关闭 client"""
        await self.client.close()

    async def __aenter__(self) -> "OpenAIProvider":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
