"""
Workflows Page (Placeholder)
"""

from nicegui import ui


def show_workflows():
    """Show Workflows page"""
    with ui.card().classes("w-full"):
        ui.label("Workflow 编排").classes("text-2xl font-bold")
        ui.separator()
        ui.label("🚧 此功能正在开发中，敬请期待...").classes("text-lg text-gray-500")
