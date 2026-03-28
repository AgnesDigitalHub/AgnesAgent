"""
Instrumentation - 自动插桩追踪
为 LLM 调用、Skill 调用和 MCP 调用添加自动追踪
"""

from collections.abc import Callable
from functools import wraps
from typing import Any

from agnes.telemetry.tracer import get_current_span, start_span


def instrument_llm_call(
    provider_name: str,
    model: str,
    prompt_tokens: int = 0,
):
    """
    追踪 LLM 调用
    :param provider_name: LLM 供应商名称
    :param model: 模型名称
    :param prompt_tokens: prompt 令牌数
    """
    span = get_current_span()
    span.set_attribute("llm.provider", provider_name)
    span.set_attribute("llm.model", model)
    span.set_attribute("llm.prompt_tokens", prompt_tokens)


def instrument_skill_call(
    skill_name: str,
    parameters: dict[str, Any] = None,
):
    """
    追踪 Skill 调用
    :param skill_name: Skill 名称
    :param parameters: 参数字典（敏感参数会被忽略）
    """
    span = get_current_span()
    span.set_attribute("skill.name", skill_name)
    if parameters:
        # 只记录参数键，不记录敏感值
        span.set_attribute("skill.param_count", len(parameters))
        span.set_attribute("skill.param_keys", ",".join(parameters.keys()))


def instrument_mcp_call(
    server_id: str,
    tool_name: str,
):
    """
    追踪 MCP 工具调用
    :param server_id: 服务器 ID
    :param tool_name: 工具名称
    """
    span = get_current_span()
    span.set_attribute("mcp.server_id", server_id)
    span.set_attribute("mcp.tool_name", tool_name)


def trace_skill_execution(func: Callable) -> Callable:
    """
    装饰 Skill execute 方法，自动添加追踪
    :param func: execute 方法
    :return: 包装后的方法
    """

    @wraps(func)
    async def wrapper(self, parameters: dict[str, Any]):
        skill_name = getattr(self, "name", "unknown")
        with start_span(f"skill.execute.{skill_name}"):
            instrument_skill_call(skill_name, parameters)
            result = await func(self, parameters)
            # 记录执行结果
            span = get_current_span()
            span.set_attribute("skill.success", result.success)
            if not result.success and result.error_message:
                span.set_attribute("skill.error", result.error_message)
            span.set_attribute("skill.execution_time_ms", result.execution_time_ms)
            return result

    return wrapper


def trace_mcp_tool_call(func: Callable) -> Callable:
    """
    装饰 MCP 工具调用方法，自动添加追踪
    :param func: call_tool 方法
    :return: 包装后的方法
    """

    @wraps(func)
    async def wrapper(self, tool_name: str, arguments: dict[str, Any]):
        server_id = getattr(self, "server_id", "unknown")
        with start_span(f"mcp.tool_call.{server_id}.{tool_name}"):
            instrument_mcp_call(server_id, tool_name)
            result = await func(self, tool_name, arguments)
            span = get_current_span()
            span.set_attribute("mcp.success", result is not None)
            return result

    return wrapper
