import json
from collections.abc import AsyncGenerator

import aiohttp

from agnes.core import LLMProvider, LLMResponse

chat_url = "v1/chat/completions"


class OllamaProvider(LLMProvider):
    """Ollama LLM Provider，支持本地模型调用"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama2",
        proxy: str | None = None,
        **kwargs,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.proxy = proxy
        self.session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 aiohttp session"""
        if self.session is None or self.session.closed:
            connector = None
            if self.proxy:
                connector = aiohttp.TCPConnector()
            self.session = aiohttp.ClientSession(connector=connector, trust_env=True)
        return self.session

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        session = await self._get_session()

        try:
            url = f"{self.base_url}/{chat_url}"
            async with session.post(
                url,
                json=payload,
                proxy=self.proxy,
                timeout=aiohttp.ClientTimeout(total=300),
            ) as response:
                response.raise_for_status()
                data = await response.json()

                return LLMResponse(
                    content=data.get("response", ""),
                    model=self.model,
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                    },
                )
        except Exception as e:
            raise RuntimeError(f"Ollama generation failed: {str(e)}")

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        session = await self._get_session()

        try:
            url = f"{self.base_url}/{chat_url}"
            async with session.post(
                url,
                json=payload,
                proxy=self.proxy,
                timeout=aiohttp.ClientTimeout(total=300),
            ) as response:
                response.raise_for_status()
                async for line in response.content:
                    if line.strip():
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done", False):
                            break
        except Exception as e:
            raise RuntimeError(f"Ollama stream generation failed: {str(e)}")

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        session = await self._get_session()

        try:
            url = f"{self.base_url}/api/chat"
            async with session.post(
                url,
                json=payload,
                proxy=self.proxy,
                timeout=aiohttp.ClientTimeout(total=300),
            ) as response:
                response.raise_for_status()
                data = await response.json()

                message = data.get("message", {})
                return LLMResponse(
                    content=message.get("content", ""),
                    model=self.model,
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                    },
                )
        except Exception as e:
            raise RuntimeError(f"Ollama chat failed: {str(e)}")

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        session = await self._get_session()

        try:
            url = f"{self.base_url}/api/chat"
            async with session.post(
                url,
                json=payload,
                proxy=self.proxy,
                timeout=aiohttp.ClientTimeout(total=300),
            ) as response:
                response.raise_for_status()
                async for line in response.content:
                    if line.strip():
                        data = json.loads(line)
                        message = data.get("message", {})
                        if "content" in message:
                            yield message["content"]
                        if data.get("done", False):
                            break
        except Exception as e:
            raise RuntimeError(f"Ollama chat stream failed: {str(e)}")

    async def close(self) -> None:
        """关闭 session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self) -> "OllamaProvider":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
