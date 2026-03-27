"""
Models Management Page - AstrBot style
"""

from typing import Any

import httpx
from nicegui import ui

PROVIDER_TEMPLATES = {
    "openai": {
        "label": "OpenAI",
        "icon": "smart_toy",
        "default_model": "gpt-3.5-turbo",
        "default_base_url": "https://api.openai.com/v1",
        "description": "OpenAI API 配置",
        "color": "#10a37f",
    },
    "ollama": {
        "label": "Ollama",
        "icon": "computer",
        "default_model": "llama2",
        "default_base_url": "http://localhost:11434/v1",
        "description": "本地 Ollama 配置",
        "color": "#000000",
    },
    "openvino-server": {
        "label": "OpenVINO Server",
        "icon": "memory",
        "default_model": "meta-llama/Llama-2-7b-chat-hf",
        "default_base_url": "http://localhost:8080/v1",
        "description": "OpenVINO 模型服务器",
        "color": "#0068b5",
    },
    "local-api": {
        "label": "其他本地模型",
        "icon": "api",
        "default_model": "local-model",
        "default_base_url": "http://localhost:11434/v1",
        "description": "兼容 OpenAI 格式的本地 API",
        "color": "#6366f1",
    },
}


async def load_profiles() -> dict[str, Any] | None:
    """Load profiles from API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8000/api/profiles")
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"Failed to load profiles: {e}")
    return None


async def load_profile(profile_id: str) -> dict[str, Any] | None:
    """Load a single profile from API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://127.0.0.1:8000/api/profiles/{profile_id}")
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"Failed to load profile: {e}")
    return None


async def create_profile(data: dict[str, Any]) -> bool:
    """Create a new profile"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://127.0.0.1:8000/api/profiles", json=data)
            if response.status_code == 200:
                ui.notify("配置创建成功!", type="positive")
                return True
            else:
                ui.notify("创建失败", type="negative")
                return False
    except Exception as e:
        ui.notify(f"创建失败: {e}", type="negative")
        return False


async def update_profile(profile_id: str, data: dict[str, Any]) -> bool:
    """Update a profile"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(f"http://127.0.0.1:8000/api/profiles/{profile_id}", json=data)
            if response.status_code == 200:
                ui.notify("配置更新成功!", type="positive")
                return True
            else:
                ui.notify("更新失败", type="negative")
                return False
    except Exception as e:
        ui.notify(f"更新失败: {e}", type="negative")
        return False


async def activate_profile(profile_id: str, refresh_func) -> None:
    """Activate a profile"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"http://127.0.0.1:8000/api/profiles/{profile_id}/activate")
            if response.status_code == 200:
                ui.notify("配置已激活!", type="positive")
                await refresh_func()
            else:
                ui.notify("激活失败", type="negative")
    except Exception as e:
        ui.notify(f"激活失败: {e}", type="negative")


async def delete_profile(profile_id: str, refresh_func) -> None:
    """Delete a profile with confirmation"""
    with ui.dialog() as dialog, ui.card().style("border-radius: 18px;"):
        ui.label("确认删除").classes("text-xl font-bold")
        ui.label("确定要删除此配置吗？").classes("text-gray-600")
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("取消", on_click=dialog.close).props("flat")
            ui.button("确定删除", on_click=lambda: confirm_delete(dialog, profile_id, refresh_func)).classes(
                "bg-red-500"
            ).style("border-radius: 50px;")

    dialog.open()


async def confirm_delete(dialog, profile_id: str, refresh_func) -> None:
    """Confirm and execute deletion"""
    dialog.close()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"http://127.0.0.1:8000/api/profiles/{profile_id}")
            if response.status_code == 200:
                ui.notify("配置已删除!", type="positive")
                await refresh_func()
            else:
                ui.notify("删除失败", type="negative")
    except Exception as e:
        ui.notify(f"删除失败: {e}", type="negative")


def show_template_selection_dialog(refresh_func):
    """Show provider template selection dialog - AstrBot style"""
    with ui.dialog() as dialog, ui.card().classes("w-[500px]").style("border-radius: 18px;"):
        ui.label("选择 Provider 模板").classes("text-2xl font-bold mb-4")
        ui.label("选择一个 Provider 模板来快速创建配置").classes("text-gray-600 mb-4")

        with ui.column().classes("w-full gap-4"):
            for provider_key, template in PROVIDER_TEMPLATES.items():
                with (
                    ui.card()
                    .classes("w-full cursor-pointer hover:shadow-lg transition-shadow")
                    .style("border-radius: 18px;")
                    .on(
                        "click",
                        lambda p=provider_key: show_create_from_template_dialog(p, dialog, refresh_func),
                    )
                ):
                    with ui.row().classes("w-full items-center gap-4"):
                        # Provider icon with background color
                        with ui.element("div").style(
                            f"width: 56px; height: 56px; border-radius: 16px; background-color: {template.get('color', '#e0e0e0')}20; display: flex; align-items: center; justify-content: center;"
                        ):
                            ui.icon(template["icon"]).style(f"font-size: 28px; color: {template.get('color', '#666')};")

                        with ui.column().classes("flex-1"):
                            ui.label(template["label"]).classes("text-xl font-bold")
                            ui.label(template["description"]).classes("text-gray-500 text-sm")

                        ui.icon("chevron_right").classes("text-gray-400")

        with ui.row().classes("w-full justify-end mt-4"):
            ui.button("取消", on_click=dialog.close).props("flat")

    dialog.open()


def show_create_from_template_dialog(provider_key: str, parent_dialog, refresh_func):
    """Show create profile dialog with template pre-filled - AstrBot style"""
    parent_dialog.close()
    template = PROVIDER_TEMPLATES.get(provider_key, {})

    with ui.dialog() as dialog, ui.card().classes("w-[450px]").style("border-radius: 18px;"):
        ui.label(f"新增 {template.get('label', '模型')} 配置").classes("text-xl font-bold mb-4")

        with ui.column().classes("w-full gap-4"):
            name_input = ui.input(
                "名称", placeholder="请输入配置名称", value=f"{template.get('label', 'My')} Config"
            ).props("outlined required")
            desc_input = ui.input("描述", placeholder="请输入描述", value=template.get("description", "")).props(
                "outlined"
            )

            # Provider is fixed from template
            with ui.row().classes("items-center gap-2"):
                ui.label("Provider:").classes("text-gray-600")
                ui.label(template.get("label", "")).classes("font-bold")

            model_input = ui.input(
                "Model", placeholder="请输入模型名称", value=template.get("default_model", "")
            ).props("outlined required")
            base_url_input = ui.input(
                "Base URL", placeholder="请输入Base URL", value=template.get("default_base_url", "")
            ).props("outlined")
            api_key_input = ui.input(
                "API Key", placeholder="请输入API Key", password=True, password_toggle_button=True
            ).props("outlined")
            temp_input = ui.number("Temperature", value=0.7, min=0, max=2, step=0.1).props("outlined")
            max_tokens_input = ui.number("Max Tokens", placeholder="请输入Max Tokens").props("outlined")

        with ui.row().classes("w-full justify-end gap-2 mt-6"):
            ui.button("取消", on_click=dialog.close).props("flat")

            async def on_create():
                data = {
                    "name": name_input.value,
                    "description": desc_input.value or "",
                    "provider": provider_key,
                    "model": model_input.value,
                    "base_url": base_url_input.value or None,
                    "api_key": api_key_input.value or None,
                    "temperature": temp_input.value if temp_input.value is not None else 0.7,
                    "max_tokens": max_tokens_input.value,
                }

                if not data["name"] or not data["model"]:
                    ui.notify("请填写必填字段", type="warning")
                    return

                success = await create_profile(data)
                if success:
                    dialog.close()
                    await refresh_func()

            ui.button("创建", on_click=on_create).classes("bg-blue-500").style("border-radius: 50px;")

    dialog.open()


def show_edit_dialog(profile_id: str, refresh_func):
    """Show edit profile dialog - AstrBot style"""
    with ui.dialog() as dialog, ui.card().classes("w-[450px]").style("border-radius: 18px;"):
        ui.label("编辑模型配置").classes("text-xl font-bold mb-4")

        # Placeholders for inputs
        name_input = ui.input("名称").props("outlined required")
        desc_input = ui.input("描述").props("outlined")

        # Display provider (not editable)
        provider_display = ui.label("").classes("text-gray-600")

        model_input = ui.input("Model").props("outlined required")
        base_url_input = ui.input("Base URL").props("outlined")
        api_key_input = ui.input("API Key", password=True, password_toggle_button=True).props("outlined")
        temp_input = ui.number("Temperature", min=0, max=2, step=0.1).props("outlined")
        max_tokens_input = ui.number("Max Tokens").props("outlined")

        with ui.row().classes("w-full justify-end gap-2 mt-6"):
            ui.button("取消", on_click=dialog.close).props("flat")

            async def on_update():
                # Get the original provider from the profile
                profile = await load_profile(profile_id)
                original_provider = profile.get("provider", "openai") if profile else "openai"

                data = {
                    "name": name_input.value,
                    "description": desc_input.value,
                    "provider": original_provider,  # Keep original provider
                    "model": model_input.value,
                    "base_url": base_url_input.value,
                    "api_key": api_key_input.value,
                    "temperature": temp_input.value,
                    "max_tokens": max_tokens_input.value,
                }

                # Remove None values
                data = {k: v for k, v in data.items() if v is not None}

                if not data.get("name") or not data.get("model"):
                    ui.notify("请填写必填字段", type="warning")
                    return

                success = await update_profile(profile_id, data)
                if success:
                    dialog.close()
                    await refresh_func()

            ui.button("保存", on_click=on_update).classes("bg-blue-500").style("border-radius: 50px;")

        async def load_data():
            profile = await load_profile(profile_id)
            if profile:
                name_input.value = profile.get("name", "")
                desc_input.value = profile.get("description", "")
                provider_label = PROVIDER_TEMPLATES.get(profile.get("provider", "openai"), {}).get(
                    "label", profile.get("provider", "")
                )
                provider_display.text = f"Provider: {provider_label}"
                model_input.value = profile.get("model", "")
                base_url_input.value = profile.get("base_url", "")
                temp_input.value = profile.get("temperature")
                max_tokens_input.value = profile.get("max_tokens")

        ui.timer(0.1, load_data, once=True)

    dialog.open()


def create_profile_card(profile, is_active, refresh_func):
    """Create an AstrBot-style profile card"""
    template = PROVIDER_TEMPLATES.get(profile["provider"], {})
    provider_color = template.get("color", "#666")

    with (
        ui.card()
        .classes("w-full hover:shadow-lg transition-all cursor-pointer")
        .style("border-radius: 18px; padding: 4px; min-height: 220px;")
    ):
        # Card Header - Title and Active Status
        with ui.row().classes("w-full justify-between items-center pt-3 px-3 pb-1"):
            with ui.row().classes("items-center gap-2"):
                ui.label(profile["name"]).classes("text-2xl font-bold truncate")

            # Active indicator
            if is_active:
                with ui.element("div").style("display: flex; align-items: center; gap: 8px;"):
                    ui.element("div").style("width: 8px; height: 8px; border-radius: 50%; background-color: #4caf50;")
                    ui.label("激活中").classes("text-green-600 font-bold text-sm")

        # Card Content
        with ui.column().classes("px-3"):
            with ui.column().classes("w-full gap-2"):
                # Provider info with icon
                with ui.row().classes("items-center gap-2"):
                    with ui.element("div").style(
                        f"width: 32px; height: 32px; border-radius: 10px; background-color: {provider_color}20; display: flex; align-items: center; justify-content: center;"
                    ):
                        ui.icon(template.get("icon", "settings")).style(f"font-size: 18px; color: {provider_color};")

                    provider_label = template.get("label", profile["provider"])
                    ui.label(f"{provider_label} - {profile['model']}").classes("text-gray-600")

                if profile.get("description"):
                    ui.label(profile["description"]).classes("text-gray-500 text-sm")

                if profile.get("updated_at"):
                    ui.label(f"更新时间: {profile['updated_at']}").classes("text-gray-400 text-xs mt-1")

        # Card Actions - AstrBot style
        with ui.row().classes("w-full justify-between items-center px-3 py-3"):
            with ui.row().classes("gap-2"):
                ui.button("删除", on_click=lambda p=profile["id"]: delete_profile(p, refresh_func)).props(
                    "outlined size=small"
                ).classes("text-red-500 border-red-500").style("border-radius: 50px;")

                ui.button("编辑", on_click=lambda p=profile["id"]: show_edit_dialog(p, refresh_func)).props(
                    "tonal size=small"
                ).classes("bg-blue-100 text-blue-600").style("border-radius: 50px;")

            with ui.row().classes("gap-2"):
                if not is_active:
                    ui.button("激活", on_click=lambda p=profile["id"]: activate_profile(p, refresh_func)).props(
                        "tonal size=small"
                    ).classes("bg-green-100 text-green-600").style("border-radius: 50px;")


def show_models():
    """Show Models Management page - AstrBot style"""
    with ui.element("div").classes("w-full").style("padding: 20px; padding-top: 8px; padding-bottom: 40px;"):
        # Page Header - AstrBot style
        with ui.row().classes("w-full justify-between items-center px-4 py-3 pb-4"):
            with ui.column():
                with ui.row().classes("items-center gap-2"):
                    ui.icon("memory").classes("text-black")
                    ui.label("模型配置").classes("text-h4 font-bold")
                ui.label("管理和配置你的模型提供商").classes("text-subtitle-1 text-medium-emphasis")

            ui.button(
                "新增 Provider",
                icon="add",
                on_click=lambda: show_template_selection_dialog(refresh_content),
            ).props("tonal rounded=xl size=x-large").classes("bg-blue-100 text-blue-600")

        # Content area
        content_area = ui.row().classes("w-full px-4")

        async def refresh_content():
            content_area.clear()
            with content_area:
                data = await load_profiles()
                if data and data.get("profiles"):
                    with (
                        ui.grid()
                        .classes("w-full gap-4")
                        .style("grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));")
                    ):
                        for profile in data["profiles"]:
                            is_active = profile["id"] == data.get("active")
                            create_profile_card(profile, is_active, refresh_content)
                else:
                    with ui.column().classes("w-full items-center justify-center py-16"):
                        ui.icon("api_off").props("size=64").classes("text-grey-lighten-1")
                        ui.label("还没有配置任何模型").classes("text-grey mt-4")

        # Load initial data
        ui.timer(0.1, refresh_content, once=True)
