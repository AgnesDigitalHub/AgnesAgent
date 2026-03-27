"""
服务端数据模型
"""

from typing import Any, Literal

from pydantic import BaseModel

# ============================================
# OpenAI 兼容 API 模型
# ============================================


class ChatMessage(BaseModel):
    """聊天消息"""

    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    """聊天完成请求"""

    model: str
    messages: list[ChatMessage]
    temperature: float | None = 1.0
    top_p: float | None = 1.0
    max_tokens: int | None = None
    stream: bool | None = False
    stop: list[str] | None = None


class ChatCompletionChoice(BaseModel):
    """聊天完成选择"""

    index: int
    message: ChatMessage
    finish_reason: str | None = None


class ChatCompletionUsage(BaseModel):
    """Token 使用统计"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    """聊天完成响应"""

    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage


class ChatCompletionChunkChoice(BaseModel):
    """流式聊天完成选择"""

    index: int
    delta: dict[str, Any]
    finish_reason: str | None = None


class ChatCompletionChunk(BaseModel):
    """流式聊天完成响应"""

    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: list[ChatCompletionChunkChoice]


class Model(BaseModel):
    """模型信息"""

    id: str
    object: Literal["model"] = "model"
    created: int
    owned_by: str = "agnes"


class ModelListResponse(BaseModel):
    """模型列表响应"""

    object: Literal["list"] = "list"
    data: list[Model]


# ============================================
# 配置管理 API 模型
# ============================================


class CreateProfileRequest(BaseModel):
    """创建配置请求"""

    name: str
    description: str = ""
    provider: Literal["ollama", "openai", "openvino-server", "local-api"]
    model: str
    base_url: str | None = None
    api_key: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None


class UpdateProfileRequest(BaseModel):
    """更新配置请求"""

    name: str | None = None
    description: str | None = None
    provider: Literal["ollama", "openai", "openvino-server", "local-api"] | None = None
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class ProfileResponse(BaseModel):
    """配置响应"""

    id: str
    name: str
    description: str
    provider: str
    model: str
    base_url: str | None = None
    temperature: float
    max_tokens: int | None = None
    created_at: float
    updated_at: float
    is_active: bool = False


class ProfileListResponse(BaseModel):
    """配置列表响应"""

    profiles: list[ProfileResponse]
    active_profile_id: str | None = None


# ============================================
# 通用响应模型
# ============================================


class SuccessResponse(BaseModel):
    """成功响应"""

    success: bool = True
    message: str | None = None


class ErrorResponse(BaseModel):
    """错误响应"""

    success: bool = False
    error: str
    message: str | None = None


# ============================================
# 状态 API 模型
# ============================================


class StatusResponse(BaseModel):
    """状态响应"""

    llm_provider: str | None = None
    llm_config: dict[str, Any] | None = None
    active_profile_id: str | None = None
    active_profile_name: str | None = None
