"""
Web2 Pages - AMIS page modules
"""

try:
    from .agents import show_agents
    from .chat import show_chat
    from .dashboard import show_dashboard
    from .knowledge import show_knowledge
    from .logs import show_logs
    from .models import show_models
    from .prompts import show_prompts
    from .publish import show_publish
    from .settings import show_settings
    from .tools import show_tools
    from .users import show_users
    from .workflows import show_workflows
except ImportError:
    # 如果相对导入失败，使用完整包名
    from web2.pages.agents import show_agents
    from web2.pages.chat import show_chat
    from web2.pages.dashboard import show_dashboard
    from web2.pages.knowledge import show_knowledge
    from web2.pages.logs import show_logs
    from web2.pages.models import show_models
    from web2.pages.prompts import show_prompts
    from web2.pages.publish import show_publish
    from web2.pages.settings import show_settings
    from web2.pages.tools import show_tools
    from web2.pages.users import show_users
    from web2.pages.workflows import show_workflows

__all__ = [
    "show_dashboard",
    "show_models",
    "show_chat",
    "show_agents",
    "show_prompts",
    "show_tools",
    "show_knowledge",
    "show_workflows",
    "show_logs",
    "show_publish",
    "show_users",
    "show_settings",
]
