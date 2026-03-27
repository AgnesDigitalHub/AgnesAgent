"""
Web2 Pages - NiceGUI page modules
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
    from pages.agents import show_agents
    from pages.chat import show_chat
    from pages.dashboard import show_dashboard
    from pages.knowledge import show_knowledge
    from pages.logs import show_logs
    from pages.models import show_models
    from pages.prompts import show_prompts
    from pages.publish import show_publish
    from pages.settings import show_settings
    from pages.tools import show_tools
    from pages.users import show_users
    from pages.workflows import show_workflows

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
