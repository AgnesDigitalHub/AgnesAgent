from collections.abc import AsyncGenerator

from agnes.core import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI LLM Provider，支持自定义 base_url 和连接池管理"""

    # 类级别的客户端缓存，用于连接复用
    _client_cache: dict[str, any] = {}

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-3.5-turbo",
        proxy: str | None = None,
        enable_connection_pool: bool = True,
        timeout: float = 300.0,
        max_keepalive_connections: int = 5,
        max_connections: int = 10,
        **kwargs,
    ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.proxy = proxy
        self.enable_connection_pool = enable_connection_pool
        self.timeout = timeout
        self.max_keepalive_connections = max_keepalive_connections
        self.max_connections = max_connections

        # 创建或复用客户端
        self.client = self._get_or_create_client()

    def _get_or_create_client(self) -> any:
        """获取或创建客户端（支持连接池复用）"""
        if not self.enable_connection_pool:
            # 不启用连接池，每次都创建新客户端
            return self._create_client()

        # 使用缓存键来复用连接
        client_key = f"{self.base_url}:{self.api_key[:8]}:{self.proxy or 'no_proxy'}"

        if client_key not in OpenAIProvider._client_cache:
            OpenAIProvider._client_cache[client_key] = self._create_client()

        return OpenAIProvider._client_cache[client_key]

    def _create_client(self) -> any:
        """创建新的 OpenAI 客户端"""
        from openai import AsyncOpenAI
        import httpx

        # 配置连接池
        limits = httpx.Limits(
            max_keepalive_connections=self.max_keepalive_connections,
            max_connections=self.max_connections,
        )

        # 创建 HTTP 客户端
        if self.proxy:
            http_client = httpx.AsyncClient(
                proxies=self.proxy,
                timeout=self.timeout,
                limits=limits,
            )
        else:
            http_client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=limits,
            )

        return AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            http_client=http_client,
        )

    @classmethod
    def clear_client_cache(cls) -> None:
        """清除客户端缓存（用于资源释放）"""
        cls._client_cache.clear()

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
        """关闭 client（仅在非连接池模式下实际关闭）"""
        if not self.enable_connection_pool:
            await self.client.close()

    async def __aenter__(self) -> "OpenAIProvider":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
