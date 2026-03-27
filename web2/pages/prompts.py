"""
Prompt IDE Page (Placeholder)
"""

from nicegui import ui


def show_prompts():
    """Show Prompt IDE page"""
    with ui.card().classes("w-full"):
        ui.label("Prompt IDE").classes("text-2xl font-bold")
        ui.separator()
        ui.label("🚧 此功能正在开发中，敬请期待...").classes("text-lg text-gray-500")
