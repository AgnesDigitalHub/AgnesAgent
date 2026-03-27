"""
web2 - 所有页面 schema 模块
每个页面对应一个模块，每个模块提供 get_xxx_schema() 函数
返回已经使用 Pydantic 构建好的 schema dict
"""
# 所有页面 schema 在这里导出
from web2.schemas.dashboard import get_dashboard_schema
from web2.schemas.settings import get_settings_schema
from web2.schemas.agents import get_agents_schema

__all__ = [
    "get_dashboard_schema",
    "get_settings_schema",
    "get_agents_schema",
]