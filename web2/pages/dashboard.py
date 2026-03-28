"""
Dashboard Page - 使用 python-amis schema
"""

from nicegui import ui


def show_dashboard():
    """Show Dashboard page with python-amis schema"""
    # 对于 nicegui 集成，我们仍然保留原生实现，
    # 但如果需要 amis 渲染，可以通过 iframe 或 API 返回 schema
    # 当前保持 nicegui 原生实现
    import httpx

    async def load_status():
        """Load system status from API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://127.0.0.1:8000/api/status")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"Failed to load status: {e}")
        return None

    with ui.card().classes("w-full"):
        ui.label("Dashboard").classes("text-2xl font-bold mb-4")

        # Status section
        with ui.row().classes("w-full gap-4 mb-6"):
            with ui.card().classes("flex-1"):
                ui.label("LLM 状态").classes("text-lg font-semibold")
                status_label = ui.label("加载中...").classes("text-2xl font-bold")
                model_label = ui.label("-").classes("text-gray-500")

            with ui.card().classes("flex-1"):
                ui.label("活跃配置").classes("text-lg font-semibold")
                profile_label = ui.label("-").classes("text-2xl font-bold")

        # Quick actions
        ui.label("快捷操作").classes("text-lg font-semibold mb-4")
        with ui.row().classes("gap-4"):
            ui.button("去配置模型", on_click=lambda: ui.navigate.to("/web2/models")).classes("bg-blue-500")
            ui.button("开始聊天", on_click=lambda: ui.navigate.to("/web2/chat")).classes("bg-green-500")

        # Load status asynchronously
        async def update_status():
            status = await load_status()
            if status:
                llm_provider = status.get("llm_provider", "未配置")
                llm_config = status.get("llm_config", {})
                profile_name = status.get("active_profile_name", "-")

                status_label.text = llm_provider
                model_label.text = llm_config.get("model", "-") if llm_config else "-"
                profile_label.text = profile_name

        ui.timer(1.0, update_status, once=True)
