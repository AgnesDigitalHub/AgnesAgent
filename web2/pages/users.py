"""
Users Page (Placeholder)
"""

from nicegui import ui


def show_users():
    """Show Users page"""
    with ui.card().classes("w-full"):
        ui.label("用户权限").classes("text-2xl font-bold")
        ui.separator()
        ui.label("🚧 此功能正在开发中，敬请期待...").classes("text-lg text-gray-500")
