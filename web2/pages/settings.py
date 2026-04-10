"""
Settings Page - 系统设置（全量分类配置）
"""

from typing import Any

import httpx
from nicegui import ui

from agnes.utils.logger import get_logger

logger = get_logger("agnes.web2.settings")

API_BASE = "http://127.0.0.1:8000"


# API helpers


async def _get_section(section: str) -> dict[str, Any] | None:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{API_BASE}/api/settings/{section}")
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        logger.error(f"Failed to load settings/{section}: {e}")
    return None


async def _put_section(section: str, data: dict[str, Any]) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.put(f"{API_BASE}/api/settings/{section}", json=data)
            return r.status_code == 200
    except Exception as e:
        logger.error(f"Failed to save settings/{section}: {e}")
    return False


async def _sync_from_yaml() -> bool:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{API_BASE}/api/settings/sync-from-yaml")
            return r.status_code == 200
    except Exception as e:
        logger.error(f"Failed to sync from yaml: {e}")
    return False


# Tab builders


def _build_llm_tab(container):
    """LLM 配置 Tab"""
    container.clear()
    with container:
        ui.spinner(size="lg").classes("self-center")

    async def load():
        data = await _get_section("llm")
        container.clear()
        with container:
            if data is None:
                ui.label("加载失败").classes("text-red-500")
                return

            with ui.column().classes("w-full gap-4 max-w-2xl"):
                provider_opts = ["ollama", "openai", "openvino-server", "local-api"]
                provider_sel = (
                    ui.select(
                        label="Provider",
                        options=provider_opts,
                        value=data.get("provider", "ollama"),
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                model_in = (
                    ui.input(
                        "Model",
                        value=str(data.get("model", "")),
                        placeholder="例如 llama2 / gpt-4o",
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                base_url_in = (
                    ui.input(
                        "Base URL",
                        value=str(data.get("base_url", "") or ""),
                        placeholder="http://localhost:11434",
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                api_key_in = (
                    ui.input(
                        "API Key",
                        value=str(data.get("api_key", "") or ""),
                        password=True,
                        password_toggle_button=True,
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                temp_in = (
                    ui.number(
                        "Temperature",
                        value=float(data.get("temperature", 0.7)),
                        min=0,
                        max=2,
                        step=0.05,
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                max_tokens_in = (
                    ui.number(
                        "Max Tokens",
                        value=data.get("max_tokens") or None,
                        placeholder="留空表示不限制",
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                async def save_llm():
                    payload = {
                        "provider": provider_sel.value,
                        "model": model_in.value,
                        "base_url": base_url_in.value or None,
                        "api_key": api_key_in.value or None,
                        "temperature": temp_in.value if temp_in.value is not None else 0.7,
                        "max_tokens": int(max_tokens_in.value) if max_tokens_in.value else None,
                    }
                    ok = await _put_section("llm", payload)
                    if ok:
                        ui.notify("LLM 配置已保存", type="positive")
                    else:
                        ui.notify("保存失败", type="negative")

                ui.button("保存 LLM 配置", icon="save", on_click=save_llm).props("unelevated").classes(
                    "bg-blue-600 text-white"
                ).style("border-radius:8px;")

    ui.timer(0.1, load, once=True)


def _build_asr_tab(container):
    """ASR 配置 Tab"""
    container.clear()
    with container:
        ui.spinner(size="lg").classes("self-center")

    async def load():
        data = await _get_section("asr")
        container.clear()
        with container:
            if data is None:
                ui.label("加载失败").classes("text-red-500")
                return

            with ui.column().classes("w-full gap-4 max-w-2xl"):
                provider_opts = ["local_whisper", "openai_whisper"]
                provider_sel = (
                    ui.select(
                        label="Provider",
                        options=provider_opts,
                        value=data.get("provider", "local_whisper"),
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                model_in = (
                    ui.input(
                        "Model",
                        value=str(data.get("model", "base")),
                        placeholder="tiny / base / small / medium / large",
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                api_key_in = (
                    ui.input(
                        "API Key",
                        value=str(data.get("api_key", "") or ""),
                        password=True,
                        password_toggle_button=True,
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                async def save_asr():
                    payload = {
                        "provider": provider_sel.value,
                        "model": model_in.value,
                        "api_key": api_key_in.value or None,
                    }
                    ok = await _put_section("asr", payload)
                    if ok:
                        ui.notify("ASR 配置已保存", type="positive")
                    else:
                        ui.notify("保存失败", type="negative")

                ui.button("保存 ASR 配置", icon="save", on_click=save_asr).props("unelevated").classes(
                    "bg-blue-600 text-white"
                ).style("border-radius:8px;")

    ui.timer(0.1, load, once=True)


def _build_tts_tab(container):
    """TTS 配置 Tab"""
    container.clear()
    with container:
        ui.spinner(size="lg").classes("self-center")

    async def load():
        data = await _get_section("tts")
        container.clear()
        with container:
            if data is None:
                ui.label("加载失败").classes("text-red-500")
                return

            with ui.column().classes("w-full gap-4 max-w-2xl"):
                provider_opts = ["local", "openai", "edge"]
                provider_sel = (
                    ui.select(
                        label="Provider",
                        options=provider_opts,
                        value=data.get("provider", "local"),
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                voice_in = (
                    ui.input(
                        "Voice",
                        value=str(data.get("voice", "") or ""),
                        placeholder="语音名称或ID",
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                speed_in = (
                    ui.number(
                        "Speed",
                        value=float(data.get("speed", 1.0)),
                        min=0.5,
                        max=2.0,
                        step=0.1,
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                async def save_tts():
                    payload = {
                        "provider": provider_sel.value,
                        "voice": voice_in.value or None,
                        "speed": speed_in.value,
                    }
                    ok = await _put_section("tts", payload)
                    if ok:
                        ui.notify("TTS 配置已保存", type="positive")
                    else:
                        ui.notify("保存失败", type="negative")

                ui.button("保存 TTS 配置", icon="save", on_click=save_tts).props("unelevated").classes(
                    "bg-blue-600 text-white"
                ).style("border-radius:8px;")

    ui.timer(0.1, load, once=True)


def _build_memory_tab(container):
    """Memory 配置 Tab"""
    container.clear()
    with container:
        ui.spinner(size="lg").classes("self-center")

    async def load():
        data = await _get_section("memory")
        container.clear()
        with container:
            if data is None:
                ui.label("加载失败").classes("text-red-500")
                return

            with ui.column().classes("w-full gap-4 max-w-2xl"):
                enabled_sw = ui.switch("启用记忆", value=data.get("enabled", True)).classes("w-full")

                max_messages_in = (
                    ui.number(
                        "最大消息数",
                        value=int(data.get("max_messages", 100)),
                        min=10,
                        max=1000,
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                async def save_memory():
                    payload = {
                        "enabled": enabled_sw.value,
                        "max_messages": int(max_messages_in.value),
                    }
                    ok = await _put_section("memory", payload)
                    if ok:
                        ui.notify("Memory 配置已保存", type="positive")
                    else:
                        ui.notify("保存失败", type="negative")

                ui.button("保存 Memory 配置", icon="save", on_click=save_memory).props("unelevated").classes(
                    "bg-blue-600 text-white"
                ).style("border-radius:8px;")

    ui.timer(0.1, load, once=True)


def _build_agent_tab(container):
    """Agent 配置 Tab"""
    container.clear()
    with container:
        ui.spinner(size="lg").classes("self-center")

    async def load():
        data = await _get_section("agent")
        container.clear()
        with container:
            if data is None:
                ui.label("加载失败").classes("text-red-500")
                return

            with ui.column().classes("w-full gap-4 max-w-2xl"):
                max_iterations_in = (
                    ui.number(
                        "最大迭代次数",
                        value=int(data.get("max_iterations", 10)),
                        min=1,
                        max=50,
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                timeout_in = (
                    ui.number(
                        "超时时间(秒)",
                        value=int(data.get("timeout", 300)),
                        min=30,
                        max=3600,
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                async def save_agent():
                    payload = {
                        "max_iterations": int(max_iterations_in.value),
                        "timeout": int(timeout_in.value),
                    }
                    ok = await _put_section("agent", payload)
                    if ok:
                        ui.notify("Agent 配置已保存", type="positive")
                    else:
                        ui.notify("保存失败", type="negative")

                ui.button("保存 Agent 配置", icon="save", on_click=save_agent).props("unelevated").classes(
                    "bg-blue-600 text-white"
                ).style("border-radius:8px;")

    ui.timer(0.1, load, once=True)


def _build_ui_tab(container):
    """UI 配置 Tab"""
    container.clear()
    with container:
        ui.spinner(size="lg").classes("self-center")

    async def load():
        data = await _get_section("ui")
        container.clear()
        with container:
            if data is None:
                ui.label("加载失败").classes("text-red-500")
                return

            with ui.column().classes("w-full gap-4 max-w-2xl"):
                theme_opts = ["light", "dark", "system"]
                theme_sel = (
                    ui.select(
                        label="主题",
                        options=theme_opts,
                        value=data.get("theme", "system"),
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                language_opts = ["zh", "en"]
                language_sel = (
                    ui.select(
                        label="语言",
                        options=language_opts,
                        value=data.get("language", "zh"),
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                async def save_ui():
                    payload = {
                        "theme": theme_sel.value,
                        "language": language_sel.value,
                    }
                    ok = await _put_section("ui", payload)
                    if ok:
                        ui.notify("UI 配置已保存", type="positive")
                    else:
                        ui.notify("保存失败", type="negative")

                ui.button("保存 UI 配置", icon="save", on_click=save_ui).props("unelevated").classes(
                    "bg-blue-600 text-white"
                ).style("border-radius:8px;")

    ui.timer(0.1, load, once=True)


def _build_advanced_tab(container):
    """高级配置 Tab"""
    container.clear()
    with container:
        ui.spinner(size="lg").classes("self-center")

    async def load():
        data = await _get_section("advanced")
        container.clear()
        with container:
            if data is None:
                ui.label("加载失败").classes("text-red-500")
                return

            with ui.column().classes("w-full gap-4 max-w-2xl"):
                debug_sw = ui.switch("调试模式", value=data.get("debug", False)).classes("w-full")

                log_level_opts = ["DEBUG", "INFO", "WARNING", "ERROR"]
                log_level_sel = (
                    ui.select(
                        label="日志级别",
                        options=log_level_opts,
                        value=data.get("log_level", "INFO"),
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                async def save_advanced():
                    payload = {
                        "debug": debug_sw.value,
                        "log_level": log_level_sel.value,
                    }
                    ok = await _put_section("advanced", payload)
                    if ok:
                        ui.notify("高级配置已保存", type="positive")
                    else:
                        ui.notify("保存失败", type="negative")

                ui.button("保存高级配置", icon="save", on_click=save_advanced).props("unelevated").classes(
                    "bg-blue-600 text-white"
                ).style("border-radius:8px;")

    ui.timer(0.1, load, once=True)


def _build_sync_tab(container):
    """同步配置 Tab"""
    container.clear()
    with container:
        ui.spinner(size="lg").classes("self-center")

    async def load():
        container.clear()
        with container:
            with ui.column().classes("w-full gap-4 max-w-2xl"):
                ui.label("从 YAML 文件同步配置").classes("text-lg font-semibold")
                ui.label("这将把 config/config.yaml 中的配置同步到系统中").classes("text-gray-600")

                async def do_sync():
                    ok = await _sync_from_yaml()
                    if ok:
                        ui.notify("配置同步成功", type="positive")
                    else:
                        ui.notify("同步失败", type="negative")

                ui.button("立即同步", icon="sync", on_click=do_sync).props("unelevated").classes(
                    "bg-green-600 text-white"
                ).style("border-radius:8px;")

    ui.timer(0.1, load, once=True)


def show_settings():
    """显示设置页面"""
    with ui.row().classes("w-full h-screen"):
        # 左侧导航
        with ui.column().classes("w-48 bg-gray-100 h-full p-4 gap-2"):
            ui.label("设置").classes("text-xl font-bold mb-4")

            tabs = {
                "llm": "LLM 配置",
                "asr": "ASR 配置",
                "tts": "TTS 配置",
                "memory": "记忆配置",
                "agent": "Agent 配置",
                "ui": "UI 配置",
                "advanced": "高级配置",
                "sync": "同步配置",
            }

            nav_buttons = {}
            content_container = ui.column().classes("flex-1 p-6")

            def switch_tab(tab_id: str):
                for tid, btn in nav_buttons.items():
                    if tid == tab_id:
                        btn.classes("bg-blue-600 text-white", remove="bg-white text-gray-700")
                    else:
                        btn.classes("bg-white text-gray-700", remove="bg-blue-600 text-white")

                if tab_id == "llm":
                    _build_llm_tab(content_container)
                elif tab_id == "asr":
                    _build_asr_tab(content_container)
                elif tab_id == "tts":
                    _build_tts_tab(content_container)
                elif tab_id == "memory":
                    _build_memory_tab(content_container)
                elif tab_id == "agent":
                    _build_agent_tab(content_container)
                elif tab_id == "ui":
                    _build_ui_tab(content_container)
                elif tab_id == "advanced":
                    _build_advanced_tab(content_container)
                elif tab_id == "sync":
                    _build_sync_tab(content_container)

            for tab_id, tab_name in tabs.items():
                btn = ui.button(tab_name).classes("w-full text-left justify-start")
                btn.classes("bg-white text-gray-700")
                btn.on("click", lambda tid=tab_id: switch_tab(tid))
                nav_buttons[tab_id] = btn

        # 右侧内容区
        with ui.column().classes("flex-1 h-full"):
            content_container = ui.column().classes("w-full h-full p-6")
            # 默认显示 LLM 配置
            _build_llm_tab(content_container)
