"""
Agnes Server - amis Schema 定义
"""

from .agents import get_agents_schema
from .chat import get_chat_schema
from .dashboard import get_dashboard_schema
from .knowledge import get_knowledge_schema
from .logs import get_logs_schema
from .models import get_models_schema
from .prompts import get_prompts_schema
from .publish import get_publish_schema
from .settings import get_settings_schema
from .tools import get_tools_schema
from .users import get_users_schema
from .workflows import get_workflows_schema

__all__ = [
    "get_dashboard_schema",
    "get_chat_schema",
    "get_agents_schema",
    "get_models_schema",
    "get_workflows_schema",
    "get_tools_schema",
    "get_knowledge_schema",
    "get_logs_schema",
    "get_prompts_schema",
    "get_publish_schema",
    "get_users_schema",
    "get_settings_schema",
]
