"""
Agent Management Page - AMIS Schema
"""


def get_agents_schema() -> dict:
    """获取 Agent 管理页面 schema"""
    from web2.schemas.agents import get_agents_schema as _get_schema

    return _get_schema()
