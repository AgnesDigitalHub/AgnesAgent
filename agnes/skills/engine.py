"""
Skill 调用引擎
解析 LLM Function Calling 输出，调度 Skill 执行，处理结果
支持本地 Skills 和远程 MCP 工具调用
"""

import asyncio
import time
from typing import Any

from agnes.mcp.client import MCPClient
from agnes.skills.base import SkillResult
from agnes.skills.registry import SkillRegistry, registry
from agnes.utils.logger import get_logger

logger = get_logger(__name__)


class SkillCallEngine:
    """Skill 调用引擎，处理 Function Calling 解析和执行
    支持本地 Skills 和远程 MCP 工具调用
    """

    def __init__(
        self,
        skill_registry: SkillRegistry = registry,
        mcp_client: MCPClient | None = None,
        default_timeout: float = 30.0,
        max_retries: int = 1,
    ):
        self.registry = skill_registry
        self.mcp_client = mcp_client
        self.default_timeout = default_timeout
        self.max_retries = max_retries

    def set_mcp_client(self, client: MCPClient):
        """设置 MCP 客户端"""
        self.mcp_client = client

    async def call(
        self,
        skill_name: str,
        parameters: dict[str, Any],
        timeout: float | None = None,
        retries: int | None = None,
    ) -> SkillResult:
        """调用单个 Skill，自动判断是本地还是远程 MCP
        远程格式: server_id/tool_name
        """
        # 判断是否是 MCP 工具
        if "/" in skill_name and self.mcp_client is not None:
            return await self._call_mcp_tool(skill_name, parameters, timeout, retries)

        # 本地 Skill
        skill = self.registry.get(skill_name)
        if not skill:
            return SkillResult.error(
                "skill_not_found",
                f"Skill '{skill_name}' not found in registry",
            )

        timeout = timeout if timeout is not None else self.default_timeout
        retries = retries if retries is not None else self.max_retries

        start_time = time.time()
        last_error = None
        error_type = None

        for attempt in range(retries + 1):
            try:
                # 执行，带超时
                result = await asyncio.wait_for(skill.execute(parameters), timeout=timeout)
                execution_time = (time.time() - start_time) * 1000

                # 记录统计
                self.registry.record_call(
                    skill_name, result.success, result.execution_time_ms or execution_time, result.error_type
                )

                if not result.execution_time_ms:
                    result.execution_time_ms = execution_time

                return result

            except TimeoutError:
                last_error = "Execution timed out"
                error_type = "timeout"
            except Exception as e:
                last_error = str(e)
                error_type = "exception"

            # 如果还有重试机会，继续
            if attempt < retries:
                await asyncio.sleep(0.1 * (attempt + 1))

        # 所有重试都失败了
        execution_time = (time.time() - start_time) * 1000
        self.registry.record_call(skill_name, False, execution_time, error_type)
        return SkillResult.error(error_type, last_error or "Unknown error", execution_time)

    async def _call_mcp_tool(
        self,
        full_name: str,
        parameters: dict[str, Any],
        timeout: float | None = None,
        retries: int | None = None,
    ) -> SkillResult:
        """调用 MCP 工具"""
        timeout = timeout if timeout is not None else self.default_timeout
        retries = retries if retries is not None else self.max_retries

        start_time = time.time()
        last_error = None
        error_type = None

        for attempt in range(retries + 1):
            try:
                result = await asyncio.wait_for(
                    self.mcp_client.call_global_tool(full_name, parameters), timeout=timeout
                )
                execution_time = (time.time() - start_time) * 1000

                if isinstance(result, dict):
                    return SkillResult.ok(result, execution_time_ms=execution_time)
                elif isinstance(result, str):
                    return SkillResult.ok({"text": result}, execution_time_ms=execution_time)
                else:
                    return SkillResult.ok({"result": result}, execution_time_ms=execution_time)

            except TimeoutError:
                last_error = "MCP tool execution timed out"
                error_type = "timeout"
            except Exception as e:
                last_error = str(e)
                error_type = "exception"

            if attempt < retries:
                await asyncio.sleep(0.1 * (attempt + 1))

        execution_time = (time.time() - start_time) * 1000
        return SkillResult.error(error_type, last_error or "Unknown MCP error", execution_time)

    async def call_parallel(
        self,
        calls: list[tuple[str, dict[str, Any]]],
        timeout: float | None = None,
    ) -> list[SkillResult]:
        """并行调用多个 Skill"""
        tasks = []
        for skill_name, parameters in calls:
            tasks.append(self.call(skill_name, parameters, timeout=timeout))

        results = await asyncio.gather(*tasks, return_exceptions=False)
        return list(results)

    async def call_chain(
        self,
        chain: list[tuple[str, dict[str, Any], str | None]],
    ) -> list[SkillResult]:
        """
        调用链 - 前一个 Skill 的输出可以作为后一个的输入
        每个条目: (skill_name, parameters, output_to_input_var)
        如果 output_to_input_var 设置了，则将结果放到上下文中，后续参数可以用 {var} 引用
        """
        context: dict[str, Any] = {}
        results: list[SkillResult] = []

        for skill_name, parameters, output_var in chain:
            # 替换参数中的上下文变量
            resolved_params = self._resolve_parameters(parameters, context)

            # 调用
            result = await self.call(skill_name, resolved_params)
            results.append(result)

            # 如果需要保存输出到上下文
            if output_var and result.success:
                context[output_var] = result.data

            # 如果失败，中断链
            if not result.success:
                break

        return results

    def _resolve_parameters(self, params: Any, context: dict[str, Any]) -> Any:
        """递归解析参数中的 {var} 占位符"""
        if isinstance(params, str):
            # 替换 {var} 格式的占位符
            import string

            return string.Formatter().vformat(params, [], context)
        elif isinstance(params, dict):
            return {k: self._resolve_parameters(v, context) for k, v in params.items()}
        elif isinstance(params, list):
            return [self._resolve_parameters(item, context) for item in params]
        else:
            return params

    def parse_llm_function_call(self, llm_output: str) -> list[tuple[str, dict[str, Any]]]:
        """
        从 LLM 输出中解析 Function Call
        这里假设 LLM 输出了正确的 JSON 格式，实际使用时需要处理各种异常情况
        对于支持原生 Function Calling 的 LLM，这一步由 LLM API 完成
        """
        import json
        import re

        # 查找所有 ```json ... ``` 块
        json_blocks = re.findall(r"```json\s*(.*?)\s*```", llm_output, re.DOTALL)

        calls = []

        for block in json_blocks:
            try:
                data = json.loads(block.strip())
                if isinstance(data, list):
                    for item in data:
                        if "name" in item or "function" in item:
                            name = item.get("name") or item.get("function", "")
                            params = item.get("parameters") or item.get("arguments", {})
                            calls.append((name, params))
                elif isinstance(data, dict):
                    if "name" in data or "function" in data:
                        name = data.get("name") or data.get("function", "")
                        params = data.get("parameters") or data.get("arguments", {})
                        calls.append((name, params))
            except json.JSONDecodeError:
                continue

        # 如果没有找到代码块，尝试直接解析整个输出
        if not calls:
            try:
                data = json.loads(llm_output.strip())
                if isinstance(data, list):
                    for item in data:
                        if "name" in item or "function" in item:
                            name = item.get("name") or item.get("function", "")
                            params = item.get("parameters") or item.get("arguments", {})
                            calls.append((name, params))
                elif isinstance(data, dict):
                    if "name" in data or "function" in data:
                        name = data.get("name") or data.get("function", "")
                        params = data.get("parameters") or data.get("arguments", {})
                        calls.append((name, params))
            except json.JSONDecodeError:
                pass

        return calls


# 全局默认引擎
default_engine = SkillCallEngine()
