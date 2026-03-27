"""
Agnes Web2 - NiceGUI Web Console
"""

import sys
from pathlib import Path

# Add parent directory to path for module imports
web2_dir = Path(__file__).parent
sys.path.insert(0, str(web2_dir))

from nicegui import app as nicegui_app
from nicegui import ui

try:
    from .pages import (
        show_agents,
        show_chat,
        show_dashboard,
        show_knowledge,
        show_logs,
        show_models,
        show_prompts,
        show_publish,
        show_settings,
        show_tools,
        show_users,
        show_workflows,
    )
except ImportError:
    from pages import (
        show_agents,
        show_chat,
        show_dashboard,
        show_knowledge,
        show_logs,
        show_models,
        show_prompts,
        show_publish,
        show_settings,
        show_tools,
        show_users,
        show_workflows,
    )

# Current page state
current_page = {"name": "dashboard"}

# Menu items
menu_items = [
    {"name": "dashboard", "label": "Dashboard", "icon": "home"},
    {"name": "models", "label": "模型管理", "icon": "smart_toy"},
    {"name": "chat", "label": "对话", "icon": "chat"},
    {"name": "agents", "label": "Agent 管理", "icon": "psychology"},
    {"name": "prompts", "label": "Prompt IDE", "icon": "edit_note"},
    {"name": "tools", "label": "工具/插件", "icon": "build"},
    {"name": "knowledge", "label": "知识库/RAG", "icon": "menu_book"},
    {"name": "workflows", "label": "Workflow 编排", "icon": "account_tree"},
    {"name": "logs", "label": "运行日志", "icon": "article"},
    {"name": "publish", "label": "API/集成发布", "icon": "publish"},
    {"name": "users", "label": "用户权限", "icon": "group"},
    {"name": "settings", "label": "系统设置", "icon": "settings"},
]

# Page renderers
page_renderers = {
    "dashboard": show_dashboard,
    "models": show_models,
    "chat": show_chat,
    "agents": show_agents,
    "prompts": show_prompts,
    "tools": show_tools,
    "knowledge": show_knowledge,
    "workflows": show_workflows,
    "logs": show_logs,
    "publish": show_publish,
    "users": show_users,
    "settings": show_settings,
}


def navigate_to(page_name):
    """Navigate to a specific page"""
    current_page["name"] = page_name
    ui.navigate.to(f"/web2/{page_name}")


@ui.page("/web2")
@ui.page("/web2/{page_name}")
def main(page_name: str = "dashboard"):
    """Main application page"""
    current_page["name"] = page_name

    # 先创建 drawer，再在 header 中引��� toggle 方法
    drawer = ui.left_drawer(fixed=True, bordered=True).classes("p-0")
    with drawer:
        with ui.column().classes("w-full h-full"):
            for item in menu_items:
                with (
                    ui.row()
                    .classes("w-full items-center gap-3 px-4 py-3 hover:bg-gray-100 cursor-pointer")
                    .on("click", lambda _, i=item: navigate_to(i["name"]))
                ):
                    ui.icon(item["icon"]).classes("text-xl")
                    ui.label(item["label"]).classes("font-medium")

    with ui.header(elevated=True).classes("items-center px-6"):
        with ui.row().classes("items-center gap-4"):
            ui.button(icon="menu", on_click=drawer.toggle).props("flat round").classes("text-white")
            with ui.row().classes("items-center gap-3"):
                ui.icon("smart_toy").classes("text-2xl")
                ui.label("Agnes Agent").classes("text-2xl font-bold")

    with (
        ui.column()
        .classes("w-full min-h-screen")
        .style("padding-top: 80px; padding-bottom: 40px; padding-left: 20px; padding-right: 20px;")
    ):
        # Render current page
        renderer = page_renderers.get(page_name)
        if renderer:
            renderer()
        else:
            with ui.card().classes("w-full"):
                ui.label("页面未找到").classes("text-2xl font-bold text-red-500")
                ui.label(f"请求的页面: {page_name}").classes("text-gray-500")


def init_nicegui():
    """Initialize NiceGUI application"""
    # Configure NiceGUI
    static_dir = web2_dir / "static"
    if static_dir.exists():
        nicegui_app.add_static_files("/static", str(static_dir))

    # Return the app instance for FastAPI mounting
    return nicegui_app


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Agnes Agent", port=8080)
