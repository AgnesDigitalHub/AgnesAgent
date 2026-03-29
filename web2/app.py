"""
Agnes Web2 - FastAPI + AMIS SPA 后端
异步按需加载版本：
- 顶层 App 配置一次性返回
- 每个页面 schema 点击时异步获取 /api/pages/{page_name}
- Pydantic + python-amis 构建所有 schema
"""

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# Add parent directory to path
web2_dir = Path(__file__).parent
root_dir = web2_dir.parent
sys.path.insert(0, str(root_dir))

from agnes.core import LLMProvider
from agnes.providers import OllamaProvider, OpenAIProvider, OpenVINOProvider
from agnes.skills import SkillResult, registry
from web2.app_config import get_app_config, get_built_amis_app
from web2.models import ProfileStore
from web2.persona import PersonaStore
from web2.stats_manager import get_stats_manager


def read_index_html() -> str:
    """读取 index.html 模板"""
    template_path = web2_dir / "templates" / "index.html"
    with open(template_path, encoding="utf-8") as f:
        return f.read()


def register_amis_routes(app: FastAPI, api_prefix: str = "/api") -> None:
    """
    注册 AMIS SPA 所需路由：
    1. GET / - 返回 HTML 入口页
    2. GET /app.json - 返回完整内嵌式 App 配置（兼容旧版入口）
    3. GET {api_prefix}/amis/schema - 返回顶层 App 配置
    4. GET {api_prefix}/pages/{page_name} - 返回单个页面 schema（异步按需加载）
    """

    # 保存全局配置实例
    app_config = get_app_config()

    @app.get("/", response_class=HTMLResponse)
    @app.get("/index.html", response_class=HTMLResponse)
    async def index():
        """返回 AMIS HTML 入口页面"""
        html = read_index_html()
        return HTMLResponse(content=html)

    @app.get(f"{api_prefix}/amis/schema", response_class=JSONResponse)
    async def get_app_schema():
        """获取顶层 AMIS App 配置（包含菜单和路由）"""
        try:
            schema = get_built_amis_app()
            return JSONResponse(content=schema)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"构建 App 配置失败: {str(e)}")

    @app.get(f"{api_prefix}/pages/{{page_name}}", response_class=JSONResponse)
    async def get_page_schema(page_name: str):
        """获取单个页面 schema（异步按需加载）
        URL 中的连字符会转换为下划线匹配 Python 文件名
        """
        # URL 路径中的连字符转下划线，因为 Python 模块名不能包含连字符
        page_name_py = page_name.replace("-", "_")
        schema = app_config.get_page_schema(page_name_py)
        if schema is None:
            raise HTTPException(status_code=404, detail=f"页面 {page_name} 不存在")
        return JSONResponse(content=schema)

    # 暴露 app.json - 供前端获取顶层配置
    @app.get("/app.json", response_class=JSONResponse)
    async def get_app_json():
        """获取完整的 AMIS App 配置（包含所有菜单项）"""
        try:
            schema = get_built_amis_app()
            return JSONResponse(content=schema)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"构建 App 配置失败: {str(e)}")

    # 注册 API 路由（模型管理 + 聊天）
    register_api_routes(app, api_prefix)

    # SPA 兜底路由：所有非 API、非静态文件请求都返回 index.html
    # 这样才能支持浏览器直接访问 /dashboard 等前端路由
    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def serve_spa(full_path: str):
        # 过滤掉 API 请求，API 请求不应该返回 HTML
        if full_path.startswith("api/") or full_path.startswith("/api/"):
            raise HTTPException(status_code=404, detail="API 端点不存在")
        # 过滤掉带扩展名的静态资源请求，避免把 .js/.css 也返回成 html
        if "." in full_path:
            raise HTTPException(status_code=404, detail="静态资源不存在")
        html = read_index_html()
        return HTMLResponse(content=html)


# ============ LLM 工厂函数 ============


def create_llm_provider(config) -> LLMProvider:
    """根据配置创建 LLM provider 实例"""
    provider_type = config.provider

    # 所有兼容 OpenAI 接口格式的供应商都走 OpenAIProvider
    openai_compatible_providers = {
        "openai",
        "openai-compat",
        "deepseek",
        "gemini",
        "anthropic",
        "openvino-server",
        "local-api",
        "generic",
    }

    if provider_type == "ollama":
        return OllamaProvider(
            base_url=config.base_url or "http://localhost:11434",
            model=config.model,
        )
    elif provider_type in openai_compatible_providers:
        # 默认 API Key 处理：本地服务一般不需要 key
        default_api_key = "dummy-key" if provider_type in ["ollama", "openvino-server", "generic"] else ""

        # 默认 Base URL
        default_base_url = {
            "openai": "https://api.openai.com/v1",
            "deepseek": "https://api.deepseek.com",
            "gemini": "https://generativelanguage.googleapis.com/v1beta",
            "anthropic": "https://api.anthropic.com",
            "ollama": "http://localhost:11434",
            "openvino-server": "http://localhost:8000/v1",
        }.get(provider_type, "http://localhost:8000/v1")

        return OpenAIProvider(
            api_key=config.api_key or default_api_key,
            base_url=config.base_url or default_base_url,
            model=config.model,
        )
    elif provider_type == "openvino":
        return OpenVINOProvider(
            model_name_or_path=config.model,
        )
    else:
        raise ValueError(f"不支持的 provider: {provider_type}")


# ============ 模型管理 ============

# 存储路径
storage_path = root_dir / "config" / "llm_profiles" / "profiles.json"
profile_store = ProfileStore(storage_path)

# 人格存储路径
persona_storage_path = root_dir / "config" / "personas" / "personas.json"
persona_store = PersonaStore(persona_storage_path)


# 请求模型 - LLM Profile
class CreateProfileRequest(BaseModel):
    name: str
    description: str = ""
    provider: str
    model: str
    base_url: str | None = None
    api_key: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class FetchModelsRequest(BaseModel):
    provider: str
    base_url: str | None = None
    api_key: str | None = None


class GenerateIdRequest(BaseModel):
    provider: str


# 请求模型 - Persona (Agent)
class CreatePersonaRequest(BaseModel):
    full_name: str
    nickname: str = ""
    role: str = ""
    personality: str = ""
    scenario: str = ""
    system_prompt: str
    llm_profile_id: str | None = None
    description: str = ""
    enabled: bool = True
    mcp_enabled: bool = False
    mcp_servers: list[str] | None = None
    skills: list[str] | None = None


class UpdatePersonaRequest(BaseModel):
    full_name: str | None = None
    nickname: str | None = None
    role: str | None = None
    personality: str | None = None
    scenario: str | None = None
    system_prompt: str | None = None
    llm_profile_id: str | None = None
    description: str | None = None
    enabled: bool | None = None
    mcp_enabled: bool | None = None
    mcp_servers: list[str] | None = None
    skills: list[str] | None = None


# 请求模型 - 系统设置
class SettingsRequest(BaseModel):
    site_name: str | None = None
    site_description: str | None = None
    site_intro: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    max_tokens: int | None = None
    enable_registration: bool | None = None
    enable_analytics: bool | None = None
    debug_mode: bool | None = None


# ============ MCP 服务器配置存储 ============

# MCP 配置存储路径
mcp_storage_path = root_dir / "config" / "mcp" / "servers.json"

# 确保目录存在
if not mcp_storage_path.parent.exists():
    mcp_storage_path.parent.mkdir(parents=True, exist_ok=True)


# Pydantic 模型
class MCPConfig(BaseModel):
    """MCP 服务器配置"""

    id: str
    name: str
    transport_type: str = "stdio"
    command: str
    args: list[str] = []
    env: dict[str, str] | None = None
    description: str = ""
    enabled: bool = True


def load_mcp_configs() -> dict[str, MCPConfig]:
    """加载所有 MCP 配置"""
    if not mcp_storage_path.exists():
        return {}
    try:
        import json

        with open(mcp_storage_path, encoding="utf-8") as f:
            data = json.load(f)
        result = {}
        for item in data:
            config = MCPConfig(**item)
            result[config.id] = config
        return result
    except Exception:
        return {}


def save_mcp_configs(configs: dict[str, MCPConfig]) -> None:
    """保存所有 MCP 配置"""
    import json

    data = [config.dict() for config in configs.values()]
    with open(mcp_storage_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# 全局 MCP 客户端实例（延迟初始化）
from agnes.mcp.client import MCPClient, MCPServerConnection

_global_mcp_client: MCPClient | None = None


def get_mcp_client() -> MCPClient:
    """获取全局 MCP 客户端，自动加载已保存的配置"""
    global _global_mcp_client
    if _global_mcp_client is None:
        _global_mcp_client = MCPClient()
        # 加载配置并连接所有启用的服务器
        configs = load_mcp_configs()
        for config in configs.values():
            if config.enabled:
                conn = MCPServerConnection(
                    server_id=config.id,
                    name=config.name,
                    transport_type=config.transport_type,
                    command=config.command,
                    args=config.args,
                    env=config.env,
                )
                _global_mcp_client.add_connection(conn)
                # 异步连接会在首次使用时处理
    return _global_mcp_client


# 系统设置存储
settings_storage_path = root_dir / "config" / "settings" / "settings.json"

# 确保目录存在
if not settings_storage_path.parent.exists():
    settings_storage_path.parent.mkdir(parents=True, exist_ok=True)

# 默认设置
default_settings = {
    "site_name": "Agents Dashboard",
    "site_description": "",
    "site_intro": "",
    "openai_api_key": "",
    "openai_base_url": "",
    "max_tokens": 4096,
    "enable_registration": True,
    "enable_analytics": False,
    "debug_mode": False,
}


def load_settings():
    """加载设置"""
    if not settings_storage_path.exists():
        return default_settings.copy()
    try:
        import json

        with open(settings_storage_path, encoding="utf-8") as f:
            data = json.load(f)
        # 合并默认设置
        merged = default_settings.copy()
        merged.update(data)
        return merged
    except Exception:
        return default_settings.copy()


def save_settings(data):
    """保存设置"""
    import json

    with open(settings_storage_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ============ 注册 API 路由到 app ============
def register_api_routes(app: FastAPI, api_prefix: str = "/api"):
    """注册 API 路由"""

    # 全局保存 LLM 提供者实例
    _llm_instance = None

    def get_llm_instance():
        """获取或创建 LLM 实例"""
        nonlocal _llm_instance
        active_profile = profile_store.get_active_profile()
        if not active_profile:
            return None

        if _llm_instance is None:
            llm_config = active_profile.to_llm_config()
            _llm_instance = create_llm_provider(llm_config)

        return _llm_instance

    @app.get(f"{api_prefix}/profiles")
    async def list_profiles():
        """获取所有配置列表"""
        profiles = profile_store.list_profiles()
        active_id = profile_store.get_active_id()
        return {"profiles": [p.to_dict() for p in profiles], "active": active_id}

    @app.get(f"{api_prefix}/profiles/{{profile_id}}")
    async def get_profile(profile_id: str):
        """获取单个配置"""
        profile = profile_store.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="配置不存在")
        return profile.to_dict()

    @app.post(f"{api_prefix}/profiles")
    async def create_profile(req: CreateProfileRequest):
        """创建新配置"""
        profile = profile_store.create_profile(
            name=req.name,
            description=req.description,
            provider=req.provider,
            model=req.model,
            base_url=req.base_url,
            api_key=req.api_key,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
        return {"success": True, "id": profile.id, "profile": profile.to_dict()}

    @app.put(f"{api_prefix}/profiles/{{profile_id}}")
    async def update_profile(profile_id: str, req: UpdateProfileRequest):
        """更新配置"""
        updates = req.dict(exclude_unset=True)
        profile = profile_store.update_profile(profile_id, **updates)
        if not profile:
            raise HTTPException(status_code=404, detail="配置不存在")
        return {"success": True, "profile": profile.to_dict()}

    @app.delete(f"{api_prefix}/profiles/{{profile_id}}")
    async def delete_profile(profile_id: str):
        """删除配置"""
        success = profile_store.delete_profile(profile_id)
        if not success:
            raise HTTPException(status_code=404, detail="配置不存在")
        return {"success": True}

    @app.post(f"{api_prefix}/profiles/{{profile_id}}/activate")
    async def activate_profile(profile_id: str):
        """激活配置"""
        # 激活时强制重新创建 LLM 实例
        nonlocal _llm_instance
        _llm_instance = None
        success = profile_store.activate_profile(profile_id)
        if not success:
            raise HTTPException(status_code=404, detail="配置不存在")
        return {"success": True}

    @app.get(f"{api_prefix}/status")
    async def get_status():
        """获取当前状态信息"""
        active_profile = profile_store.get_active_profile()
        active_persona = persona_store.get_active_persona()

        result = {
            "llm_provider": None,
            "active_profile_name": None,
            "llm_config": None,
            "has_active_llm": False,
            "active_persona": None,
            "active_persona_id": None,
            "has_active_persona": False,
        }

        if active_profile:
            result.update(
                {
                    "llm_provider": active_profile.provider,
                    "active_profile_name": active_profile.name,
                    "llm_config": active_profile.to_dict(),
                    "has_active_llm": True,
                }
            )

        if active_persona:
            result.update(
                {
                    "active_persona": active_persona.to_dict(),
                    "active_persona_id": active_persona.id,
                    "has_active_persona": True,
                }
            )

        return result

    @app.websocket("/ws/chat")
    async def websocket_chat(websocket: WebSocket):
        """聊天 WebSocket 端点 - 流式输出"""
        await websocket.accept()

        llm = get_llm_instance()
        if not llm:
            await websocket.send_json({"type": "error", "message": "没有激活的模型，请先在模型管理中激活一个配置"})
            await websocket.close()
            return

        # 保存对话历史
        if not hasattr(llm, "chat_history"):
            llm.chat_history = []

        try:
            while True:
                # 接收客户端消息
                data = await websocket.receive_json()
                message = data.get("message", "").strip()
                use_history = data.get("use_history", True)
                system_prompt = data.get("system_prompt", None)

                if not message:
                    continue

                # 获取当前激活的配置
                active_profile = profile_store.get_active_profile()
                active_persona = persona_store.get_active_persona()

                # 如果人格绑定了LLM，使用人格绑定的LLM配置覆盖
                if active_persona and active_persona.llm_profile_id:
                    active_profile = profile_store.get_profile(active_persona.llm_profile_id)

                if not active_profile:
                    await websocket.send_json({"type": "error", "message": "没有激活的模型，请先激活"})
                    break

                # 构造对话消息
                messages = []

                # 优先使用websocket传入的system_prompt，如果没有则使用人格构建的
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                elif active_persona:
                    built_prompt = active_persona.build_system_prompt()
                    messages.append({"role": "system", "content": built_prompt})

                if use_history:
                    # 使用已有历史 + 用户新消息
                    if system_prompt:
                        messages.extend(llm.chat_history)
                    messages.append({"role": "user", "content": message})
                else:
                    # 不使用历史，只发送当前消息
                    if not system_prompt:
                        messages = [{"role": "user", "content": message}]

                if use_history and not system_prompt:
                    llm.chat_history.append({"role": "user", "content": message})

                # 开始生成
                await websocket.send_json({"type": "start"})

                full_response = ""

                try:
                    # 流式生成
                    if use_history or system_prompt:
                        # 使用对话历史
                        stream = llm.chat_stream(
                            messages if (system_prompt or not use_history) else llm.chat_history,
                            temperature=active_profile.temperature,
                            max_tokens=active_profile.max_tokens,
                        )
                        async for token in stream:
                            if token:
                                full_response += token
                                await websocket.send_json({"type": "token", "content": token})
                    else:
                        # 无历史，单次对话
                        stream = llm.generate_stream(
                            message, temperature=active_profile.temperature, max_tokens=active_profile.max_tokens
                        )
                        async for token in stream:
                            if token:
                                full_response += token
                                await websocket.send_json({"type": "token", "content": token})

                    # 添加助手回复到历史
                    if use_history:
                        llm.chat_history.append({"role": "assistant", "content": full_response})

                    await websocket.send_json({"type": "done"})

                except Exception as e:
                    await websocket.send_json({"type": "error", "message": str(e)})

        except WebSocketDisconnect:
            pass

    # ============ 人格管理 API ============

    @app.get(f"{api_prefix}/personas")
    async def list_personas():
        """获取所有人格列表"""
        personas = persona_store.list_personas()
        active_id = persona_store.get_active_id()
        return {"personas": [p.to_dict() for p in personas], "active": active_id}

    @app.get(f"{api_prefix}/personas/{{persona_id}}")
    async def get_persona(persona_id: str):
        """获取单个人格"""
        persona = persona_store.get_persona(persona_id)
        if not persona:
            raise HTTPException(status_code=404, detail="人格不存在")
        return persona.to_dict()

    @app.post(f"{api_prefix}/personas")
    async def create_persona(req: CreatePersonaRequest):
        """创建新人格（Agent）"""
        persona = persona_store.create_persona(
            full_name=req.full_name,
            nickname=req.nickname,
            role=req.role,
            personality=req.personality,
            scenario=req.scenario,
            system_prompt=req.system_prompt,
            llm_profile_id=req.llm_profile_id,
            description=req.description,
            enabled=req.enabled,
            mcp_enabled=req.mcp_enabled,
            mcp_servers=req.mcp_servers,
            skills=req.skills,
        )
        return {"success": True, "id": persona.id, "persona": persona.to_dict()}

    @app.put(f"{api_prefix}/personas/{{persona_id}}")
    async def update_persona(persona_id: str, req: UpdatePersonaRequest):
        """更新人格"""
        updates = req.dict(exclude_unset=True)
        persona = persona_store.update_persona(persona_id, **updates)
        if not persona:
            raise HTTPException(status_code=404, detail="人格不存在")
        return {"success": True, "persona": persona.to_dict()}

    @app.delete(f"{api_prefix}/personas/{{persona_id}}")
    async def delete_persona(persona_id: str):
        """删除人格"""
        success = persona_store.delete_persona(persona_id)
        if not success:
            raise HTTPException(status_code=404, detail="人格不存在")
        return {"success": True}

    @app.post(f"{api_prefix}/personas/{{persona_id}}/activate")
    async def activate_persona(persona_id: str):
        """激活人格"""
        success = persona_store.activate_persona(persona_id)
        if not success:
            raise HTTPException(status_code=404, detail="人格不存在")
        return {"success": True}

    # ============ Dashboard API ============

    @app.get(f"{api_prefix}/dashboard/tokens")
    async def get_dashboard_tokens():
        """获取 Token 使用趋势数据（演示）"""
        # 生成最近7天的模拟数据
        import datetime

        today = datetime.datetime.now()
        data = []
        for i in range(7):
            day = today - datetime.timedelta(days=6 - i)
            import random

            tokens = random.randint(1000, 15000)
            data.append({"date": day.strftime("%m-%d"), "tokens": tokens})
        return {"xField": "date", "yField": "tokens", "data": data}

    @app.get(f"{api_prefix}/dashboard/stats")
    async def get_dashboard_stats():
        """获取仪表板统计数据"""
        stats_manager = get_stats_manager()
        stats = stats_manager.get_all_stats()

        # 获取内存使用情况
        memory_usage = stats["memory_usage"]

        return {
            "connected_agents": stats["active_connections"],
            "total_messages": stats["today_messages"],  # 使用今天的消息数
            "uptime": stats["uptime"],
            "memory_usage": f"{memory_usage['process_rss']:.1f} MB",
            "memory_percent": f"{memory_usage['system_percent']:.1f}%",
        }

    @app.get(f"{api_prefix}/dashboard/messages")
    async def get_dashboard_messages():
        """获取消息统计数据"""
        stats_manager = get_stats_manager()
        stats = stats_manager.get_all_stats()

        # 获取最近7天的消息数据
        import datetime

        today = datetime.datetime.now()
        daily_messages = stats["daily_messages"]

        data = []
        for i in range(7):
            day = today - datetime.timedelta(days=6 - i)
            day_str = day.strftime("%Y-%m-%d")
            messages = daily_messages.get(day_str, 0)
            data.append({"date": day.strftime("%m-%d"), "messages": messages})

        return {"xField": "date", "yField": "messages", "data": data}

    @app.post(f"{api_prefix}/dashboard/increment-messages")
    async def increment_messages():
        """增加消息计数"""
        stats_manager = get_stats_manager()
        stats_manager.increment_messages()
        return {"success": True, "total_messages": stats_manager.get_today_messages()}

    @app.post(f"{api_prefix}/dashboard/update-connections")
    async def update_connections(connections: int):
        """更新活跃连接数"""
        stats_manager = get_stats_manager()
        stats_manager.set_active_connections(connections)
        return {"success": True, "active_connections": stats_manager.get_active_connections()}

    # ============ 系统设置 API ============

    @app.get(f"{api_prefix}/settings/get")
    async def get_settings():
        """获取系统设置"""
        settings = load_settings()
        return settings

    @app.post(f"{api_prefix}/settings/save")
    async def save_settings_api(req: SettingsRequest):
        """保存系统设置"""
        current = load_settings()
        updates = req.dict(exclude_unset=True)
        current.update(updates)
        save_settings(current)
        return {"success": True, "settings": current}

    @app.post(f"{api_prefix}/profiles/fetch-models")
    async def fetch_models(req: FetchModelsRequest):
        """从供应商 API 获取可用模型列表"""
        import httpx

        provider = req.provider
        base_url = req.base_url
        api_key = req.api_key

        # 根据供应商补全默认 base_url
        if not base_url:
            default_base_url = {
                "openai": "https://api.openai.com/v1",
                "deepseek": "https://api.deepseek.com",
                "gemini": "https://generativelanguage.googleapis.com/v1beta",
                "anthropic": "https://api.anthropic.com",
                "ollama": "http://localhost:11434",
                "openvino-server": "http://localhost:8000/v1",
            }.get(provider)
            base_url = default_base_url

        if not base_url:
            raise HTTPException(status_code=400, detail="无法确定 API Base URL，请手动填写")

        # Ollama 使用不同的 API 路径
        if provider == "ollama":
            # Ollama API: GET /api/tags
            base_url = base_url.rstrip("/")
            models_url = f"{base_url}/api/tags"
        else:
            # OpenAI 兼容格式: GET /v1/models
            base_url = base_url.rstrip("/")
            if base_url.endswith("/v1"):
                models_url = f"{base_url}/models"
            else:
                models_url = f"{base_url}/v1/models"

        # 准备 headers
        headers = {}
        if api_key:
            if provider != "gemini":
                headers["Authorization"] = f"Bearer {api_key}"
                if provider == "anthropic":
                    headers["anthropic-version"] = "2023-06-01"

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                if provider == "gemini":
                    # Gemini 使用 API key 作为查询参数
                    if not api_key:
                        raise ValueError("Gemini 需要 API Key")
                    models_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
                    response = await client.get(models_url)
                else:
                    response = await client.get(models_url, headers=headers)

                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=f"获取模型列表失败: {response.text}")

                data = response.json()

                # 解析不同格式
                models = []
                if provider == "gemini":
                    # Gemini 返回格式: { "models": [ { "name": "models/gemini-pro", ... } ] }
                    for m in data.get("models", []):
                        model_id = m.get("name", "").replace("models/", "")
                        display_name = m.get("displayName", model_id)
                        models.append({"value": model_id, "label": display_name})
                elif provider == "ollama":
                    # Ollama 返回格式: { "models": [ { "name": "llama3:8b", ... } ] }
                    for m in data.get("models", []):
                        model_id = m.get("name")
                        if model_id:
                            models.append({"value": model_id, "label": model_id})
                elif "data" in data and isinstance(data["data"], list):
                    # OpenAI 兼容格式: { "data": [ { "id": "model-id" }, ... ] }
                    for m in data["data"]:
                        model_id = m.get("id")
                        if model_id:
                            models.append({"value": model_id, "label": model_id})
                elif isinstance(data, list):
                    # 某些提供商直接返回列表
                    for m in data:
                        model_id = m.get("id") or m.get("name")
                        if model_id:
                            models.append({"value": model_id, "label": model_id})
                else:
                    # 兜底处理
                    for k in data:
                        if isinstance(data[k], list) and len(data[k]) > 0:
                            for m in data[k]:
                                model_id = m.get("id") or m.get("name")
                                if model_id:
                                    models.append({"value": model_id, "label": model_id})
                            break

                # 按名称排序
                models.sort(key=lambda x: x["label"])

                return {"success": True, "count": len(models), "models": models}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取模型列表异常: {str(e)}")

    @app.post(f"{api_prefix}/profiles/generate-id")
    async def generate_profile_id(req: GenerateIdRequest):
        """生成唯一的配置 ID"""
        provider = req.provider
        base_id = provider

        # 检查是否已存在
        existing_profiles = profile_store.list_profiles()
        existing_ids = {p.id for p in existing_profiles}

        # 如果基础 ID 不存在，直接返回
        if base_id not in existing_ids:
            return {"success": True, "id": base_id}

        # 否则添加数字后缀
        counter = 2
        while f"{base_id}-{counter}" in existing_ids:
            counter += 1

        unique_id = f"{base_id}-{counter}"
        return {"success": True, "id": unique_id}

    # ============ MCP 管理 API ============

    # 请求模型
    class CreateMCPRequest(BaseModel):
        id: str
        name: str
        transport_type: str = "stdio"
        command: str
        args: list[str] = []
        env: dict[str, str] | None = None
        description: str = ""
        enabled: bool = True

    class UpdateMCPRequest(BaseModel):
        id: str | None = None
        name: str | None = None
        transport_type: str | None = None
        command: str | None = None
        args: list[str] | None = None
        env: dict[str, str] | None = None
        description: str | None = None
        enabled: bool | None = None

    @app.get(f"{api_prefix}/mcp/list")
    async def list_mcp_servers():
        """列出所有 MCP 服务器，包含连接状态"""
        configs = load_mcp_configs()
        client = get_mcp_client()
        result = []

        for config in configs.values():
            conn = client.get_connection(config.id)
            connected = False
            tools = []
            if conn:
                connected = conn.connected
                tools = conn.tools

            result.append(
                {
                    **config.dict(),
                    "connected": connected,
                    "tool_count": len(tools),
                    "tools": [t.dict() for t in tools],
                }
            )

        return {
            "items": result,
            "total": len(result),
        }

    @app.get(f"{api_prefix}/mcp/get/{{server_id}}")
    async def get_mcp_server(server_id: str):
        """获取单个 MCP 服务器配置"""
        configs = load_mcp_configs()
        if server_id not in configs:
            raise HTTPException(status_code=404, detail="服务器不存在")
        return configs[server_id].dict()

    @app.post(f"{api_prefix}/mcp/create")
    async def create_mcp_server(req: CreateMCPRequest):
        """创建 MCP 服务器"""
        configs = load_mcp_configs()
        if req.id in configs:
            raise HTTPException(status_code=400, detail=f"服务器 ID '{req.id}' 已存在")

        config = MCPConfig(**req.dict())
        configs[config.id] = config
        save_mcp_configs(configs)

        # 添加到客户端并尝试连接
        client = get_mcp_client()
        conn = MCPServerConnection(
            server_id=config.id,
            name=config.name,
            transport_type=config.transport_type,
            command=config.command,
            args=config.args,
            env=config.env,
        )
        client.add_connection(conn)

        # 如果启用，尝试连接
        connected = False
        if config.enabled:
            connected = await conn.connect()

        return {
            "success": True,
            "id": config.id,
            "config": config.dict(),
            "connected": connected,
            "tool_count": len(conn.tools) if connected else 0,
        }

    @app.put(f"{api_prefix}/mcp/update/{{server_id}}")
    async def update_mcp_server(server_id: str, req: UpdateMCPRequest):
        """更新 MCP 服务器配置"""
        configs = load_mcp_configs()
        if server_id not in configs:
            raise HTTPException(status_code=404, detail="服务器不存在")

        existing = configs[server_id]
        updates = req.dict(exclude_unset=True)

        # 更新字段
        for key, value in updates.items():
            if hasattr(existing, key):
                setattr(existing, key, value)

        save_mcp_configs(configs)

        # 重新连接
        client = get_mcp_client()
        client.remove_connection(server_id)

        if existing.enabled:
            conn = MCPServerConnection(
                server_id=existing.id,
                name=existing.name,
                transport_type=existing.transport_type,
                command=existing.command,
                args=existing.args,
                env=existing.env,
            )
            client.add_connection(conn)
            connected = await conn.connect()
        else:
            connected = False

        return {
            "success": True,
            "config": existing.dict(),
            "connected": connected,
        }

    @app.delete(f"{api_prefix}/mcp/delete/{{server_id}}")
    async def delete_mcp_server(server_id: str):
        """删除 MCP 服务器"""
        configs = load_mcp_configs()
        if server_id not in configs:
            raise HTTPException(status_code=404, detail="服务器不存在")

        # 断开连接并移除
        client = get_mcp_client()
        conn = client.get_connection(server_id)
        if conn and conn.connected:
            await conn.disconnect()
        client.remove_connection(server_id)

        # 从存储删除
        del configs[server_id]
        save_mcp_configs(configs)

        return {"success": True}

    @app.post(f"{api_prefix}/mcp/test/{{server_id}}")
    async def test_mcp_connection(server_id: str):
        """测试连接到 MCP 服务器"""
        configs = load_mcp_configs()
        if server_id not in configs:
            raise HTTPException(status_code=404, detail="服务器不存在")

        client = get_mcp_client()
        conn = client.get_connection(server_id)
        if not conn:
            config = configs[server_id]
            conn = MCPServerConnection(
                server_id=config.id,
                name=config.name,
                transport_type=config.transport_type,
                command=config.command,
                args=config.args,
                env=config.env,
            )
            client.add_connection(conn)

        if conn.connected:
            return {
                "success": True,
                "connected": True,
                "tool_count": len(conn.tools),
                "tools": [t.dict() for t in conn.tools],
            }

        connected = await conn.connect()
        if connected:
            return {
                "success": True,
                "connected": True,
                "tool_count": len(conn.tools),
                "tools": [t.dict() for t in conn.tools],
            }
        else:
            error = conn.last_error or "连接失败"
            raise HTTPException(status_code=500, detail=f"连接失败: {error}")

    @app.post(f"{api_prefix}/mcp/disconnect/{{server_id}}")
    async def disconnect_mcp_server(server_id: str):
        """断开 MCP 服务器连接"""
        client = get_mcp_client()
        conn = client.get_connection(server_id)
        if not conn:
            return {"success": True, "disconnected": True}

        if conn.connected:
            await conn.disconnect()

        return {"success": True, "disconnected": True}

    @app.get(f"{api_prefix}/mcp/tools/{{server_id}}")
    async def list_mcp_tools(server_id: str):
        """获取服务器的工具列表"""
        client = get_mcp_client()
        conn = client.get_connection(server_id)
        if not conn:
            raise HTTPException(status_code=404, detail="服务器不存在")

        return {
            "tools": [t.dict() for t in conn.tools],
        }

    # ============ Skill 调试 API ============

    class ExecuteSkillRequest(BaseModel):
        """执行 Skill 请求"""

        parameters: dict[str, Any]

    @app.get(f"{api_prefix}/skills/list")
    async def list_skills():
        """列出所有已注册的 Skill"""
        skills = registry.list_skills()
        result = []
        for skill in skills:
            schema = skill.get_schema()
            meta = skill.get_metadata()
            result.append(
                {
                    "name": schema.name,
                    "description": schema.description,
                    "category": meta.category,
                    "version": meta.version,
                    "tags": meta.tags,
                    "source": "yaml" if hasattr(skill, "yaml_source") else "native",
                    "parameters": schema.parameters,
                }
            )
        return {"skills": result}

    @app.post(f"{api_prefix}/skills/execute/{{skill_name}}")
    async def execute_skill(skill_name: str, req: ExecuteSkillRequest):
        """执行指定 Skill，返回结果"""
        skill = registry.get_skill(skill_name)
        if not skill:
            raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' 不存在")

        import time

        start_time = time.time()

        try:
            result = await skill.execute(req.parameters)
            execution_time_ms = (time.time() - start_time) * 1000
            # 确保执行时间被记录
            result.execution_time_ms = execution_time_ms
            return {"success": True, "result": result.dict()}
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return {
                "success": False,
                "result": SkillResult.error(
                    error_type="exception", message=str(e), execution_time_ms=execution_time_ms
                ).dict(),
            }


def create_fastapi_app(api_prefix: str = "/api") -> FastAPI:
    """创建 FastAPI 应用并注册 AMIS 路由"""
    app = FastAPI(title="Agnes AMIS", version="2.0")

    # 注册所有 AMIS 路由
    register_amis_routes(app, api_prefix)

    return app


if __name__ in {"__main__", "__mp_main__"}:
    import uvicorn

    app = create_fastapi_app()
    uvicorn.run(app, host="127.0.0.1", port=8080)
