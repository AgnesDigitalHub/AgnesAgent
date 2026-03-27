"""
Settings Page - 系统设置（全量分类配置）
"""

from typing import Any

import httpx
from nicegui import ui

API_BASE = "http://127.0.0.1:8000"


# ─────────────────────────────────────────────────────────
# API helpers
# ──���───────────────────────────────���──────────────────────


async def _get_section(section: str) -> dict[str, Any] | None:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{API_BASE}/api/settings/{section}")
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        print(f"Failed to load settings/{section}: {e}")
    return None


async def _put_section(section: str, data: dict[str, Any]) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.put(f"{API_BASE}/api/settings/{section}", json=data)
            return r.status_code == 200
    except Exception as e:
        print(f"Failed to save settings/{section}: {e}")
    return False


async def _sync_from_yaml() -> bool:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{API_BASE}/api/settings/sync-from-yaml")
            return r.status_code == 200
    except Exception as e:
        print(f"Failed to sync from yaml: {e}")
    return False


# ──────────────────────────────���──────────────────────────
# Tab builders
# ──────────────────────────────���──────────────────────────


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

                base_url_in = (
                    ui.input(
                        "Base URL",
                        value=str(data.get("base_url", "") or ""),
                        placeholder="https://api.openai.com/v1",
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                use_openvino_chk = ui.checkbox(
                    "使用 OpenVINO 加速",
                    value=bool(data.get("use_openvino", False)),
                )

                async def save_asr():
                    payload = {
                        "provider": provider_sel.value,
                        "model": model_in.value,
                        "api_key": api_key_in.value or None,
                        "base_url": base_url_in.value or None,
                        "use_openvino": use_openvino_chk.value,
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


def _build_audio_tab(container):
    """音频配置 Tab"""
    container.clear()
    with container:
        ui.spinner(size="lg").classes("self-center")

    async def load():
        data = await _get_section("audio")
        container.clear()
        with container:
            if data is None:
                ui.label("加载失败").classes("text-red-500")
                return

            with ui.column().classes("w-full gap-4 max-w-2xl"):
                sample_rate_in = (
                    ui.number(
                        "采样率 (Hz)",
                        value=int(data.get("sample_rate", 16000)),
                        min=8000,
                        max=48000,
                        step=1000,
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                channels_in = (
                    ui.number(
                        "声道数",
                        value=int(data.get("channels", 1)),
                        min=1,
                        max=2,
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                blocksize_in = (
                    ui.number(
                        "Block Size",
                        value=int(data.get("blocksize", 1024)),
                        min=256,
                        step=256,
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                device_in = (
                    ui.number(
                        "音频设备 ID（留空自动）",
                        value=data.get("device") if data.get("device") is not None else None,
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                async def save_audio():
                    payload = {
                        "sample_rate": int(sample_rate_in.value) if sample_rate_in.value else 16000,
                        "channels": int(channels_in.value) if channels_in.value else 1,
                        "blocksize": int(blocksize_in.value) if blocksize_in.value else 1024,
                        "device": int(device_in.value) if device_in.value is not None else None,
                    }
                    ok = await _put_section("audio", payload)
                    if ok:
                        ui.notify("音频配置已保存", type="positive")
                    else:
                        ui.notify("保存失败", type="negative")

                ui.button("保存音频配置", icon="save", on_click=save_audio).props("unelevated").classes(
                    "bg-blue-600 text-white"
                ).style("border-radius:8px;")

    ui.timer(0.1, load, once=True)


def _build_vad_tab(container):
    """VAD 配置 Tab"""
    container.clear()
    with container:
        ui.spinner(size="lg").classes("self-center")

    async def load():
        data = await _get_section("vad")
        container.clear()
        with container:
            if data is None:
                ui.label("加载失败").classes("text-red-500")
                return

            with ui.column().classes("w-full gap-4 max-w-2xl"):
                silence_thr_in = (
                    ui.number(
                        "静音阈值 (silence_threshold)",
                        value=float(data.get("silence_threshold", 0.01)),
                        min=0,
                        max=1,
                        step=0.001,
                        format="%.3f",
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                speech_thr_in = (
                    ui.number(
                        "语音阈值 (speech_threshold)",
                        value=float(data.get("speech_threshold", 0.02)),
                        min=0,
                        max=1,
                        step=0.001,
                        format="%.3f",
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                min_speech_in = (
                    ui.number(
                        "最小语音帧数 (min_speech_frames)",
                        value=int(data.get("min_speech_frames", 10)),
                        min=1,
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                min_silence_in = (
                    ui.number(
                        "最小静音帧数 (min_silence_frames)",
                        value=int(data.get("min_silence_frames", 30)),
                        min=1,
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                async def save_vad():
                    payload = {
                        "silence_threshold": float(silence_thr_in.value) if silence_thr_in.value is not None else 0.01,
                        "speech_threshold": float(speech_thr_in.value) if speech_thr_in.value is not None else 0.02,
                        "min_speech_frames": int(min_speech_in.value) if min_speech_in.value else 10,
                        "min_silence_frames": int(min_silence_in.value) if min_silence_in.value else 30,
                    }
                    ok = await _put_section("vad", payload)
                    if ok:
                        ui.notify("VAD 配置已保存", type="positive")
                    else:
                        ui.notify("保存失败", type="negative")

                ui.button("保存 VAD 配置", icon="save", on_click=save_vad).props("unelevated").classes(
                    "bg-blue-600 text-white"
                ).style("border-radius:8px;")

    ui.timer(0.1, load, once=True)


def _build_proxy_tab(container):
    """代理配置 Tab"""
    container.clear()
    with container:
        ui.spinner(size="lg").classes("self-center")

    async def load():
        data = await _get_section("proxy")
        container.clear()
        with container:
            if data is None:
                ui.label("加载失败").classes("text-red-500")
                return

            with ui.column().classes("w-full gap-4 max-w-2xl"):
                http_in = (
                    ui.input(
                        "HTTP 代理",
                        value=str(data.get("http_proxy", "") or ""),
                        placeholder="http://127.0.0.1:7890",
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                https_in = (
                    ui.input(
                        "HTTPS 代理",
                        value=str(data.get("https_proxy", "") or ""),
                        placeholder="http://127.0.0.1:7890",
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                async def save_proxy():
                    payload = {
                        "http_proxy": http_in.value or None,
                        "https_proxy": https_in.value or None,
                    }
                    ok = await _put_section("proxy", payload)
                    if ok:
                        ui.notify("代理配置已保存", type="positive")
                    else:
                        ui.notify("保存失败", type="negative")

                ui.button("保存���理配置", icon="save", on_click=save_proxy).props("unelevated").classes(
                    "bg-blue-600 text-white"
                ).style("border-radius:8px;")

    ui.timer(0.1, load, once=True)


def _build_general_tab(container):
    """通用/日志配置 Tab"""
    container.clear()
    with container:
        ui.spinner(size="lg").classes("self-center")

    async def load():
        data = await _get_section("general")
        container.clear()
        with container:
            if data is None:
                ui.label("加载失败").classes("text-red-500")
                return

            with ui.column().classes("w-full gap-4 max-w-2xl"):
                log_level_sel = (
                    ui.select(
                        label="日志级别",
                        options=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        value=data.get("log_level", "INFO"),
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                log_file_in = (
                    ui.input(
                        "日志文件路径（留空不写文件）",
                        value=str(data.get("log_file", "") or ""),
                        placeholder="例如 agnes.log",
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                async def save_general():
                    payload = {
                        "log_level": log_level_sel.value,
                        "log_file": log_file_in.value or None,
                    }
                    ok = await _put_section("general", payload)
                    if ok:
                        ui.notify("通用配置已保存", type="positive")
                    else:
                        ui.notify("保存失败", type="negative")

                ui.button("保存通用配置", icon="save", on_click=save_general).props("unelevated").classes(
                    "bg-blue-600 text-white"
                ).style("border-radius:8px;")

    ui.timer(0.1, load, once=True)


# ─────────────────────────────────────────────────────────
# Main entry
# ─────────────────────────────────────────────────────────


def show_settings():
    """Show Settings page with full classified config"""
    with ui.element("div").classes("w-full").style("padding: 20px; padding-top: 8px; padding-bottom: 40px;"):
        # Page header
        with ui.row().classes("w-full justify-between items-center px-4 py-3 pb-4"):
            with ui.column():
                with ui.row().classes("items-center gap-2"):
                    ui.icon("settings").classes("text-black")
                    ui.label("系统设置").classes("text-h4 font-bold")
                ui.label("查看并修改所有系统参数，按分类保存").classes("text-subtitle-1 text-medium-emphasis")

            async def on_sync():
                ok = await _sync_from_yaml()
                if ok:
                    ui.notify("已从 config.yaml 同步配���", type="positive")
                    ui.navigate.reload()
                else:
                    ui.notify("同步失败（config.yaml 不存在或读取出错）", type="warning")

            ui.button("从 config.yaml 同步", icon="sync", on_click=on_sync).props("tonal rounded=xl").classes(
                "bg-gray-100 text-gray-700"
            )

        # Tabs
        with ui.tabs().classes("w-full") as tabs:
            tab_llm = ui.tab("llm", label="LLM", icon="smart_toy")
            tab_asr = ui.tab("asr", label="ASR", icon="mic")
            tab_audio = ui.tab("audio", label="音频", icon="volume_up")
            tab_vad = ui.tab("vad", label="VAD", icon="graphic_eq")
            tab_proxy = ui.tab("proxy", label="代理", icon="vpn_key")
            tab_general = ui.tab("general", label="通用", icon="tune")

        with ui.tab_panels(tabs, value=tab_llm).classes("w-full"):
            with ui.tab_panel(tab_llm):
                llm_container = ui.column().classes("w-full gap-4")
                _build_llm_tab(llm_container)

            with ui.tab_panel(tab_asr):
                asr_container = ui.column().classes("w-full gap-4")
                _build_asr_tab(asr_container)

            with ui.tab_panel(tab_audio):
                audio_container = ui.column().classes("w-full gap-4")
                _build_audio_tab(audio_container)

            with ui.tab_panel(tab_vad):
                vad_container = ui.column().classes("w-full gap-4")
                _build_vad_tab(vad_container)

            with ui.tab_panel(tab_proxy):
                proxy_container = ui.column().classes("w-full gap-4")
                _build_proxy_tab(proxy_container)

            with ui.tab_panel(tab_general):
                general_container = ui.column().classes("w-full gap-4")
                _build_general_tab(general_container)
