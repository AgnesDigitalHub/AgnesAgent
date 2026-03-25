import asyncio
from collections.abc import AsyncGenerator

from agnes.core import LLMProvider, LLMResponse

try:
    import openvino as ov
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    HAS_OPENVINO = True
except ImportError:
    HAS_OPENVINO = False


class OpenVINOProvider(LLMProvider):
    """OpenVINO LLM Provider，本地推理加速"""

    def __init__(self, model_name_or_path: str, device: str = "AUTO", **kwargs):
        if not HAS_OPENVINO:
            raise ImportError(
                "OpenVINO dependencies not installed. "
                "Please install with: pip install openvino transformers torch"
            )

        self.model_name_or_path = model_name_or_path
        self.device = device
        self.tokenizer = None
        self.model = None
        self.compiled_model = None
        self._loaded = False

    async def _load_model(self) -> None:
        """异步加载模型"""
        if self._loaded:
            return

        def _load():
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name_or_path)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            _ = ov.Core()
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name_or_path,
                torch_dtype=torch.float32,
                export=True,
                trust_remote_code=True,
            )

            # 转换为 OpenVINO 模型 (简化示例)
            # 实际使用可能需要更复杂的转换逻辑
            self.model = model
            self._loaded = True

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _load)

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        await self._load_model()

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        def _generate():
            inputs = self.tokenizer(
                full_prompt, return_tensors="pt", truncation=True, max_length=2048
            )

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    temperature=temperature,
                    max_new_tokens=max_tokens or 512,
                    do_sample=temperature > 0,
                    pad_token_id=self.tokenizer.eos_token_id,
                )

            generated_text = self.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
            )

            return generated_text

        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(None, _generate)

        return LLMResponse(content=content, model=self.model_name_or_path)

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        response = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        for char in response.content:
            yield char
            await asyncio.sleep(0.01)

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        await self._load_model()

        # 构建对话提示
        formatted_prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            formatted_prompt += f"{role}: {content}\n"
        formatted_prompt += "assistant: "

        return await self.generate(
            prompt=formatted_prompt, temperature=temperature, max_tokens=max_tokens, **kwargs
        )

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        response = await self.chat(
            messages=messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        )

        for char in response.content:
            yield char
            await asyncio.sleep(0.01)

    async def close(self) -> None:
        """释放资源"""
        self.model = None
        self.tokenizer = None
        self.compiled_model = None
        self._loaded = False

    async def __aenter__(self) -> "OpenVINOProvider":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
