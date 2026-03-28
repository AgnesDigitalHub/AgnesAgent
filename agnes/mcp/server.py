"""
MCP 服务端
将本地 Skills 暴露为 MCP 工具，供其他 MCP 客户端调用
"""

import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import GetPromptResult, Tool

from agnes.skills.registry import registry as skill_registry

logger = logging.getLogger(__name__)


class AgnesMCPServer:
    """Agnes Skills MCP 服务端，将所有本地 Skill 暴露为 MCP Tools"""

    def __init__(self, server_name: str = "agnes-skills", server_version: str = "1.0.0"):
        self._server = Server(server_name)
        self._server_name = server_name
        self._server_version = server_version

        # 注册处理函数
        self._register_handlers()

    def _register_handlers(self):
        """注册 MCP 请求处理器"""

        @self._server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """列出所有可用工具"""
            tools = []
            for skill in skill_registry.list_skills():
                schema = skill.get_schema()
                mcp_tool = Tool(
                    name=schema.name,
                    description=schema.description,
                    inputSchema={
                        "type": "object",
                        "properties": schema.parameters,
                        "required": schema.required,
                    },
                )
                tools.append(mcp_tool)
            return tools

        @self._server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]):
            """调用工具"""
            from mcp.types import TextContent

            skill = skill_registry.get(name)
            if not skill:
                raise ValueError(f"Tool '{name}' not found")

            result = await skill.execute(arguments)

            if result.success:
                # 如果成功，返回结果
                if result.data:
                    return [TextContent(type="text", text=json.dumps(result.data, ensure_ascii=False, indent=2))]
                else:
                    return [TextContent(type="text", text="ok")]
            else:
                # 错误，抛出异常
                raise RuntimeError(f"{result.error_type}: {result.error_message}")

        # 暂时不需要 prompts 功能
        @self._server.list_prompts()
        async def handle_list_prompts() -> list:
            return []

        @self._server.get_prompt()
        async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> GetPromptResult:
            raise ValueError(f"Prompt '{name}' not found")

    async def run_stdio(self):
        """通过 STDIO 运行服务端（供 MCP Client 调用）"""
        async with stdio_server() as (read_stream, write_stream):
            await self._server.run(read_stream, write_stream, self._server.create_initialization_options())

    @property
    def app(self) -> Server:
        """获取底层 MCP Server 实例"""
        return self._server


def create_default_server() -> AgnesMCPServer:
    """创建默认的 Agnes MCP 服务端"""
    return AgnesMCPServer()


if __name__ == "__main__":
    # 可以直接运行作为独立服务
    import asyncio

    server = create_default_server()
    asyncio.run(server.run_stdio())
