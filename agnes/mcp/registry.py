"""
MCP 服务器注册表
管理所有已连接的 MCP 服务器和它们暴露的工具
"""
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MCPToolInfo(BaseModel):
    """MCP 工具信息"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    server_id: str


class MCPServerInfo(BaseModel):
    """MCP 服务器信息"""
    id: str
    name: str
    version: str
    transport_type: str  # "stdio" / "http" / "websocket"
    connection_string: str
    tools: List[MCPToolInfo] = Field(default_factory=list)
    connected: bool = False
    last_error: Optional[str] = None


class MCPRegistry:
    """MCP 服务器注册表"""

    def __init__(self):
        self._servers: Dict[str, MCPServerInfo] = {}
        self._tools: Dict[str, Dict[str, MCPToolInfo]] = {}  # server_id -> tool_name -> info

    def register_server(self, server_info: MCPServerInfo) -> None:
        """注册一个 MCP 服务器"""
        self._servers[server_info.id] = server_info
        self._tools[server_info.id] = {}
        for tool in server_info.tools:
            self._tools[server_info.id][tool.name] = tool
        logger.info(f"Registered MCP server: {server_info.id} ({server_info.name}) with {len(server_info.tools)} tools")

    def unregister_server(self, server_id: str) -> bool:
        """注销一个 MCP 服务器"""
        if server_id not in self._servers:
            return False
        del self._servers[server_id]
        if server_id in self._tools:
            del self._tools[server_id]
        logger.info(f"Unregistered MCP server: {server_id}")
        return True

    def get_server(self, server_id: str) -> Optional[MCPServerInfo]:
        """获取服务器信息"""
        return self._servers.get(server_id)

    def list_servers(self) -> List[MCPServerInfo]:
        """列出所有服务器"""
        return list(self._servers.values())

    def get_tool(self, server_id: str, tool_name: str) -> Optional[MCPToolInfo]:
        """获取特定工具信息"""
        if server_id not in self._tools:
            return None
        return self._tools[server_id].get(tool_name)

    def list_all_tools(self) -> List[MCPToolInfo]:
        """列出所有服务器上的所有工具"""
        all_tools = []
        for server_id, tools in self._tools.items():
            all_tools.extend(tools.values())
        return all_tools

    def list_server_tools(self, server_id: str) -> List[MCPToolInfo]:
        """列出特定服务器上的所有工具"""
        if server_id not in self._tools:
            return []
        return list(self._tools[server_id].values())

    def update_connection_status(self, server_id: str, connected: bool, error: Optional[str] = None) -> bool:
        """更新连接状态"""
        if server_id not in self._servers:
            return False
        self._servers[server_id].connected = connected
        self._servers[server_id].last_error = error
        return True

    @property
    def count(self) -> int:
        """服务器数量"""
        return len(self._servers)

    @property
    def tool_count(self) -> int:
        """总工具数量"""
        return sum(len(tools) for tools in self._tools.values())


# 全局单例
mcp_registry = MCPRegistry()