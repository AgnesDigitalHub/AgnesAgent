"""
MCP (Model Context Protocol) 集成模块
提供 MCP 服务端和客户端功能，将 Skills 暴露为 MCP Tools，同时支持连接外部 MCP 服务
"""

from agnes.mcp.client import MCPClient, MCPServerConnection
from agnes.mcp.manager import (
    DependencyInstaller,
    EncryptedSecretManager,
    HealthStatus,
    MCPEnhancedManager,
    MCPSecurityConfig,
    ToolCallRecord,
    enhanced_manager,
)
from agnes.mcp.registry import MCPRegistry, mcp_registry
from agnes.mcp.server import AgnesMCPServer, create_default_server

__all__ = [
    "AgnesMCPServer",
    "MCPClient",
    "MCPServerConnection",
    "MCPRegistry",
    "create_default_server",
    "mcp_registry",
    # Enhanced management
    "MCPEnhancedManager",
    "MCPSecurityConfig",
    "HealthStatus",
    "DependencyInstaller",
    "EncryptedSecretManager",
    "ToolCallRecord",
    "enhanced_manager",
]
