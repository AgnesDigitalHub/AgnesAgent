"""
Publish Page (Placeholder)
"""

from nicegui import ui


def show_publish():
    """Show Publish page"""
    with ui.card().classes("w-full"):
        ui.label("API/集成发布").classes("text-2xl font-bold")
        ui.separator()
        ui.label("🚧 此功能正在开发中，敬请期待...").classes("text-lg text-gray-500")
