"""
MCP 客户端
连接外部 MCP 服务器，将外部工具导入到 Agnes 系统中
"""
import asyncio
import logging
import json
import subprocess
from typing import Any, Dict, List, Optional, Union
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel

from agnes.mcp.registry import mcp_registry, MCPToolInfo, MCPServerInfo

logger = logging.getLogger(__name__)


class MCPServerConnection:
    """MCP 服务器连接管理"""

    def __init__(
        self,
        server_id: str,
        name: str,
        transport_type: str = "stdio",
        connection_string: str = "",
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
    ):
        self.server_id = server_id
        self.name = name
        self.transport_type = transport_type
        self.connection_string = connection_string
        self.command = command
        self.args = args or []
        self.env = env

        self._session: Optional[ClientSession] = None
        self._exit_stack: Optional[AsyncExitStack] = None
        self._connected = False
        self._tools: List[MCPToolInfo] = []
        self._last_error: Optional[str] = None

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def tools(self) -> List[MCPToolInfo]:
        return self._tools

    async def connect(self) -> bool:
        """连接到服务器"""
        try:
            if self._connected:
                return True

            self._exit_stack = AsyncExitStack()

            if self.transport_type == "stdio":
                # STDIO 传输
                if not self.command:
                    raise ValueError("STDIO transport requires command")

                server_params = StdioServerParameters(
                    command=self.command,
                    args=self.args,
                    env=self.env,
                )

                # 创建连接
                read_stream, write_stream = await self._exit_stack.enter_async_context(
                    stdio_client(server_params)
                )

                self._session = await self._exit_stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )

                await self._session.initialize()

                # 获取工具列表
                tools_result = await self._session.list_tools()
                self._tools = []
                for tool in tools_result.tools:
                    mcp_tool = MCPToolInfo(
                        name=tool.name,
                        description=tool.description,
                        input_schema=tool.inputSchema,
                        server_id=self.server_id,
                    )
                    self._tools.append(mcp_tool)

                # 注册到注册表
                server_info = MCPServerInfo(
                    id=self.server_id,
                    name=self.name,
                    version="1.0.0",
                    transport_type=self.transport_type,
                    connection_string=self.connection_string,
                    tools=self._tools,
                    connected=True,
                )
                mcp_registry.register_server(server_info)
                self._connected = True
                logger.info(f"Connected to MCP server '{self.server_id}', discovered {len(self._tools)} tools")
                return True

            else:
                raise ValueError(f"Unsupported transport type: {self.transport_type}")

        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Failed to connect to MCP server '{self.server_id}': {e}")
            mcp_registry.update_connection_status(self.server_id, False, str(e))
            self._connected = False
            if self._exit_stack:
                try:
                    await self._exit_stack.aclose()
                except Exception:
                    pass
                self._exit_stack = None
            self._session = None
            return False

    async def disconnect(self):
        """断开连接"""
        if self._exit_stack:
            try:
                await self._exit_stack.aclose()
            except Exception as e:
                logger.warning(f"Error disconnecting from MCP server '{self.server_id}': {e}")
        self._connected = False
        self._session = None
        self._exit_stack = None
        mcp_registry.update_connection_status(self.server_id, False, None)
        logger.info(f"Disconnected from MCP server '{self.server_id}'")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """调用工具"""
        if not self._connected or not self._session:
            raise RuntimeError(f"Not connected to server '{self.server_id}'")

        result = await self._session.call_tool(tool_name, arguments)

        # 如果结果是文本内容，尝试解析 JSON
        if result.content and len(result.content) > 0:
            first = result.content[0]
            if hasattr(first, "type") and first.type == "text":
                text = first.text
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text

        return result.content

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error


class MCPClient:
    """MCP 客户端，管理多个 MCP 服务器连接"""

    def __init__(self):
        self._connections: Dict[str, MCPServerConnection] = {}

    def add_connection(self, connection: MCPServerConnection) -> None:
        """添加一个连接"""
        self._connections[connection.server_id] = connection

    def remove_connection(self, server_id: str) -> bool:
        """移除一个连接"""
        if server_id not in self._connections:
            return False
        del self._connections[server_id]
        mcp_registry.unregister_server(server_id)
        return True

    def get_connection(self, server_id: str) -> Optional[MCPServerConnection]:
        """获取连接"""
        return self._connections.get(server_id)

    async def connect_all(self) -> Dict[str, bool]:
        """连接所有服务器"""
        results = {}
        for server_id, connection in self._connections.items():
            results[server_id] = await connection.connect()
        return results

    async def disconnect_all(self):
        """断开所有连接"""
        for connection in self._connections.values():
            if connection.connected:
                await connection.disconnect()

    def list_all_connections(self) -> List[MCPServerConnection]:
        """列出所有连接"""
        return list(self._connections.values())

    async def call_global_tool(self, tool_full_name: str, arguments: Dict[str, Any]) -> Any:
        """调用工具，格式为 'server_id/tool_name'"""
        if "/" not in tool_full_name:
            raise ValueError(f"Tool name must be in format 'server_id/tool_name', got: {tool_full_name}")

        server_id, tool_name = tool_full_name.split("/", 1)
        return await self.call_tool(server_id, tool_name, arguments)

    async def call_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """调用远程工具"""
        connection = self.get_connection(server_id)
        if not connection:
            raise ValueError(f"Server '{server_id}' not connected")
        if not connection.connected:
            raise RuntimeError(f"Server '{server_id}' is not connected")
        return await connection.call_tool(tool_name, arguments)


def create_agnes_remote_connection(server_id: str = "agnes-local", command: str = "python", args: Optional[List[str]] = None) -> MCPServerConnection:
    """创建 Agnes 本地 MCP 连接（连接到自身的 STDIO 服务）"""
    if args is None:
        # 默认运行 Agnes MCP 服务器
        args = ["-m", "agnes.mcp.server"]
    return MCPServerConnection(
        server_id=server_id,
        name="Agnes Local Skills",
        transport_type="stdio",
        command=command,
        args=args,
    )