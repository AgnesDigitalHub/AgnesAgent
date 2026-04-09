"""
Tools Management Page - AMIS Schema
"""

from web2.schemas.tools import get_tools_schema


def get_tools_schema() -> dict:
    """获取工具管理页面 schema"""
    from web2.schemas.tools import get_tools_schema as _get_schema

    return _get_schema()
