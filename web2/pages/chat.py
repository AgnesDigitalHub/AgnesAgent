"""
Chat Page - 真实 WebSocket 流式聊天
"""

import json

import httpx
from nicegui import ui

API_BASE = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws/chat"


async def _get_status():
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{API_BASE}/api/status", timeout=3)
            if r.status_code == 200:
                return r.json()
    except Exception:
        pass
    return None


def show_chat():
    """Show Chat page with real WebSocket streaming"""
    with ui.element("div").classes("w-full").style("padding: 20px; padding-top: 8px; padding-bottom: 40px;"):
        # ── Page header ─────────────────���────────────────────────
        with ui.row().classes("w-full justify-between items-center px-4 py-3 pb-2"):
            with ui.column():
                with ui.row().classes("items-center gap-2"):
                    ui.icon("chat").classes("text-black")
                    ui.label("对话").classes("text-h4 font-bold")

        # ── Current model info card ──────────────���────────────────
        model_info_row = ui.row().classes("w-full px-4 pb-3")

        async def refresh_model_info():
            model_info_row.clear()
            with model_info_row:
                status = await _get_status()
                if status and status.get("llm_provider"):
                    cfg = status.get("llm_config") or {}
                    with (
                        ui.card()
                        .classes("w-full")
                        .style("border-radius:12px; background:#f0f4ff; border:1px solid #c7d2fe;")
                    ):
                        with ui.row().classes("items-center gap-3 px-4 py-2"):
                            ui.icon("smart_toy").classes("text-indigo-500")
                            ui.label(
                                f"当前模型：{status.get('active_profile_name') or status.get('llm_provider')}  "
                                f"│  {cfg.get('provider', '')} / {cfg.get('model', '')}  "
                                f"│  temperature: {cfg.get('temperature', '')}"
                            ).classes("text-indigo-700 text-sm font-medium")
                else:
                    with (
                        ui.card()
                        .classes("w-full")
                        .style("border-radius:12px; background:#fff7ed; border:1px solid #fed7aa;")
                    ):
                        with ui.row().classes("items-center gap-3 px-4 py-2"):
                            ui.icon("warning").classes("text-orange-500")
                            ui.label(
                                "尚未激活任何模型。请前往「模型管理」激活一个配置，或在「系统设置」中配置 LLM。"
                            ).classes("text-orange-700 text-sm")

        ui.timer(0.1, refresh_model_info, once=True)

        # ── Chat area ───────────────���─────────────────────────────
        with ui.card().classes("w-full").style("border-radius:16px;"):
            # Messages container
            messages_col = (
                ui.column()
                .classes("w-full gap-3 px-2 py-2")
                .style("min-height:420px; max-height:520px; overflow-y:auto;")
            )

            with messages_col:
                with ui.row().classes("w-full justify-start"):
                    with ui.chat_message(name="Agnes", avatar="🤖"):
                        ui.label("你好！我是 Agnes，有什么可以帮你的？")

            ui.separator()

            # Input area
            with ui.row().classes("w-full items-end gap-2 px-2 py-3"):
                input_field = (
                    ui.textarea(placeholder="输入消息���Shift+Enter 换行，Enter 发送...")
                    .classes("flex-1")
                    .props("outlined rows=2 autogrow")
                )

                async def send_message():
                    message = (input_field.value or "").strip()
                    if not message:
                        return

                    input_field.value = ""

                    # Append user bubble
                    with messages_col:
                        with ui.row().classes("w-full justify-end"):
                            with ui.chat_message(name="你", sent=True, avatar="👤"):
                                ui.label(message)

                    # Agnes bubble with streaming content
                    agnes_label = None
                    with messages_col:
                        with ui.row().classes("w-full justify-start"):
                            with ui.chat_message(name="Agnes", avatar="🤖"):
                                agnes_label = ui.label("...").classes("whitespace-pre-wrap")

                    async def do_ws_chat():
                        import websockets

                        collected = []
                        debug_lines = []

                        def append_debug(line: str):
                            debug_lines.append(line)
                            debug_panel.set_content(
                                ""
                                + "\n".join(debug_lines[-50:])  # 最多保留最近50行
                                + ""
                            )

                        append_debug(f">>> 发送: {message!r}")
                        try:
                            async with websockets.connect(WS_URL) as ws:
                                await ws.send(json.dumps({"message": message, "use_history": True}))
                                while True:
                                    raw = await ws.recv()
                                    data = json.loads(raw)
                                    t = data.get("type")
                                    if t == "start":
                                        agnes_label.set_text("")
                                        append_debug("[start] 开始流式输出")
                                    elif t == "token":
                                        token_content = data.get("content", "")
                                        collected.append(token_content)
                                        agnes_label.set_text("".join(collected))
                                        append_debug(f"[token] {token_content!r}")
                                    elif t == "done":
                                        append_debug(
                                            f"[done] 完整回复 ({len(collected)} 个 token): {''.join(collected)[:200]!r}"
                                        )
                                        break
                                    elif t == "error":
                                        err_msg = data.get("message", "未知错误")
                                        agnes_label.set_text(f"[错误] {err_msg}")
                                        append_debug(f"[error] {err_msg}")
                                        break
                                    else:
                                        append_debug(f"[unknown] {data}")
                        except Exception as e:
                            agnes_label.set_text(f"[连接失败] {e}\n\n请检查服务是否已启动，并已激活模型。")
                            append_debug(f"[exception] {e}")

                    ui.timer(0.05, do_ws_chat, once=True)

                send_btn = (
                    ui.button("发送", icon="send", on_click=send_message)
                    .props("unelevated")
                    .classes("bg-indigo-600 text-white")
                    .style("border-radius:10px; height:56px;")
                )

                # Enter to send (not Shift+Enter)
                input_field.on(
                    "keydown.enter",
                    lambda e: send_message() if not e.args.get("shiftKey") else None,
                )

        # Refresh model info button
        ui.button(
            "刷新模型状态",
            icon="refresh",
            on_click=refresh_model_info,
        ).props("flat size=sm").classes("text-gray-500 mt-2")

        # ── Debug panel (fixed bottom) ───────────────────────────
        debug_panel = (
            ui.markdown("")
            .classes("w-full")
            .style(
                "position:fixed; bottom:0; left:220px; right:0; z-index:9999;"
                "background:#1a1a2e; color:#00ff88; font-family:monospace; font-size:12px;"
                "padding:8px 16px; max-height:200px; overflow-y:auto;"
                "border-top:2px solid #00ff88; white-space:pre-wrap;"
            )
        )
