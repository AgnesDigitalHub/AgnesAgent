"""
MCP 工具管理页面 Schema - 完整功能版本
"""

from web2.schemas.mcp import get_mcp_schema


def get_tools_schema():
    """获取 MCP 工具管理页面完整 Schema"""
    return get_mcp_schema()
