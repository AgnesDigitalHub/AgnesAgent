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

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# Add parent directory to path
web2_dir = Path(__file__).parent
root_dir = web2_dir.parent
sys.path.insert(0, str(root_dir))

from agnes.core import LLMProvider
from agnes.providers import OllamaProvider, OpenAIProvider
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


def register_amis_routes(app: FastAPI, api_prefix: str = "/api", add_spa_fallback: bool = True) -> None:
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

    @app.get(f"{api_prefix}/pages/{{full_path:path}}", response_class=JSONResponse)
    async def get_page_schema(full_path: str):
        """获取单个页面 schema（异步按需加载）
        URL 路径中的连字符和斜杠都会转换为下划线匹配 Python 文件名
        例如 mcp/servers -> mcp_servers
        """
        # 将路径中的斜杠转换为下划线匹配 Python 模块名
        # /mcp/servers -> mcp_servers
        page_name_py = full_path.replace("/", "_").replace("-", "_")
        schema = app_config.get_page_schema(page_name_py)
        if schema is None:
            raise HTTPException(status_code=404, detail=f"页面 {full_path} 不存在")
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
    # 但当 web2_app 被挂载到根应用时（如 main.py 中）不要添加兜底路由，否则会导致路由匹配问题
    if add_spa_fallback:

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
        "nvidia",
        "siliconflow",
        "minimax",
        "gemini",
        "anthropic",
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
        default_api_key = "dummy-key" if provider_type in ["ollama", "generic"] else ""

        # 默认 Base URL
        default_base_url = {
            "openai": "https://api.openai.com/v1",
            "deepseek": "https://api.deepseek.com",
            "nvidia": "https://integrate.api.nvidia.com/v1",
            "siliconflow": "https://api.siliconflow.cn/v1",
            "minimax": "https://api.minimax.chat/v1",
            "gemini": "https://generativelanguage.googleapis.com/v1beta",
            "anthropic": "https://api.anthropic.com",
            "ollama": "http://localhost:11434",
        }.get(provider_type, "http://localhost:8000/v1")

        return OpenAIProvider(
            api_key=config.api_key or default_api_key,
            base_url=config.base_url or default_base_url,
            model=config.model,
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
    name: str | None = None
    description: str = ""
    provider: str
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    enabled_models: list[str] | None = None


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    enabled_models: list[str] | None = None


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
from agnes.mcp.manager import (
    DependencyInstaller,
    HealthStatus,
    MCPEnhancedManager,
    MCPSecurityConfig,
    enhanced_manager,
)


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

    # 环境
    environment: str = "default"
    """环境名称（用于多环境配置支持：default / development / production）"""

    # 安全配置
    security: MCPSecurityConfig = MCPSecurityConfig()
    """安全配置整合"""

    # 向后兼容字段 - 将被弃用
    readonly: bool = False
    """@deprecated 使用 security.readonly"""

    confirm_on_dangerous: bool = True
    """@deprecated 使用 security.confirm_on_dangerous"""

    allowed_paths: list[str] | None = None
    """@deprecated 使用 security.allowed_paths"""

    allowed_domains: list[str] | None = None
    """@deprecated 使用 security.allowed_domains"""

    # Token 预估
    token_estimate: int = 0
    """预估增加的 token 消耗"""

    # 元数据
    created_at: str | None = None
    """创建时间"""

    updated_at: str | None = None
    """更新时间"""

    # 迁移兼容处理
    def __init__(self, **data):
        # 迁移旧版字段到新版结构
        if "readonly" in data and data["readonly"] and "security" not in data:
            data["security"] = MCPSecurityConfig(readonly=data["readonly"])
        if "confirm_on_dangerous" in data and "security" not in data:
            if "security" not in data:
                data["security"] = MCPSecurityConfig()
            data["security"].confirm_on_dangerous = data["confirm_on_dangerous"]
        if "allowed_paths" in data and data["allowed_paths"] and "security" not in data:
            if "security" not in data:
                data["security"] = MCPSecurityConfig()
            data["security"].allowed_paths = data["allowed_paths"] or []
        if "allowed_domains" in data and data["allowed_domains"] and "security" not in data:
            if "security" not in data:
                data["security"] = MCPSecurityConfig()
            data["security"].allowed_domains = data["allowed_domains"] or []
        # 添加时间戳
        from datetime import datetime

        if "created_at" not in data:
            data["created_at"] = datetime.now().isoformat()
        super().__init__(**data)


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


# 全局 LLM 实例管理
_global_llm_instance = None


def get_global_llm_instance():
    """获取全局 LLM 实例"""
    global _global_llm_instance
    active_profile = profile_store.get_active_profile()
    if not active_profile:
        return None

    if _global_llm_instance is None:
        llm_config = active_profile.to_llm_config()
        _global_llm_instance = create_llm_provider(llm_config)

    return _global_llm_instance


def reset_global_llm_instance():
    """重置全局 LLM 实例"""
    global _global_llm_instance
    _global_llm_instance = None


# ============ 注册 API 路由到 app ============
def register_api_routes(app: FastAPI, api_prefix: str = "/api"):
    """注册 API 路由"""

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
        # 如果没有提供 name，自动生成
        name = req.name
        if not name:
            # 使用 generate_id 逻辑生成唯一名称
            existing_profiles = profile_store.list_profiles()
            existing_ids = {p.id for p in existing_profiles}
            base_id = req.provider
            if base_id not in existing_ids:
                name = base_id
            else:
                counter = 2
                while f"{base_id}-{counter}" in existing_ids:
                    counter += 1
                name = f"{base_id}-{counter}"

        # 如果没有提供 model，使用默认值
        model = req.model
        if not model:
            default_models = {
                "openai": "gpt-4o",
                "deepseek": "deepseek-chat",
                "gemini": "gemini-pro",
                "anthropic": "claude-3-sonnet-20240229",
                "ollama": "llama3",
            }
            model = default_models.get(req.provider, "")

        profile = profile_store.create_profile(
            name=name,
            description=req.description,
            provider=req.provider,
            model=model,
            base_url=req.base_url,
            api_key=req.api_key,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            enabled_models=req.enabled_models,
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
        reset_global_llm_instance()
        success = profile_store.activate_profile(profile_id)
        if not success:
            raise HTTPException(status_code=404, detail="配置不存在")
        return {"success": True}

    @app.post(f"{api_prefix}/profiles/deactivate")
    async def deactivate_profile():
        """取消激活当前配置"""
        reset_global_llm_instance()
        profile_store.deactivate_profile()
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

        llm = get_global_llm_instance()
        if not llm:
            await websocket.send_json({"type": "error", "message": "没有激活的模型，请先在模型管理中激活一个配置"})
            await websocket.close()
            return

        # 类型断言：确保 llm 是 LLMProvider 类型
        assert isinstance(llm, LLMProvider)

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
                    # 流式生成 - 始终使用构造好的 messages 列表
                    async for token in llm.chat_stream(  # type: ignore
                        messages,
                        temperature=active_profile.temperature,
                        max_tokens=active_profile.max_tokens,
                    ):
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
        except Exception as e:
            # 捕获其他异常并发送错误消息
            try:
                await websocket.send_json({"type": "error", "message": f"服务器错误: {str(e)}"})
            except Exception:
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
                "nvidia": "https://integrate.api.nvidia.com/v1",
                "siliconflow": "https://api.siliconflow.cn/v1",
                "minimax": "https://api.minimax.chat/v1",
                "gemini": "https://generativelanguage.googleapis.com/v1beta",
                "anthropic": "https://api.anthropic.com",
                "ollama": "http://localhost:11434",
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

    def _check_command_exists(cmd: str) -> bool:
        """检查命令是否在系统 PATH 中存在"""
        import shutil

        return shutil.which(cmd) is not None

    @app.get(f"{api_prefix}/mcp/check-env")
    async def check_mcp_environment():
        """检查 MCP 运行环境（node/uv 等是否安装）"""
        return {
            "node": _check_command_exists("node"),
            "npm": _check_command_exists("npm"),
            "npx": _check_command_exists("npx"),
            "uv": _check_command_exists("uv"),
            "uvx": _check_command_exists("uvx"),
            "python": _check_command_exists("python") or _check_command_exists("python3"),
        }

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
        # 安全配置
        readonly: bool = False
        confirm_on_dangerous: bool = True
        allowed_paths: list[str] | None = None
        allowed_domains: list[str] | None = None

    class UpdateMCPRequest(BaseModel):
        id: str | None = None
        name: str | None = None
        transport_type: str | None = None
        command: str | None = None
        args: list[str] | None = None
        env: dict[str, str] | None = None
        description: str | None = None
        enabled: bool | None = None
        # 安全配置
        readonly: bool | None = None
        confirm_on_dangerous: bool | None = None
        allowed_paths: list[str] | None = None
        allowed_domains: list[str] | None = None

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

    @app.post(f"{api_prefix}/mcp/install")
    async def install_mcp_from_market(request: dict):
        """从市场安装 MCP"""
        mcp_id = request.get("mcp_id")
        token = request.get("token")
        path = request.get("path")

        # 从配置文件加载 MCP 市场数据
        from web2.schemas.mcp import MCP_MARKET

        # 查找 MCP 信息
        mcp_info = None
        for item in MCP_MARKET:
            if item["id"] == mcp_id:
                mcp_info = item
                break

        if not mcp_info:
            raise HTTPException(status_code=400, detail=f"未知的 MCP: {mcp_id}")

        # 构建 env
        env = {}
        command = mcp_info["command"]
        args = mcp_info["args"].copy()

        # 如果需要 token，注入到环境变量或参数
        if mcp_info.get("needs_token") and token:
            token_key = mcp_info.get("token_key", mcp_info.get("token_name"))
            if token_key:
                env[token_key] = token

        # 如果需要路径，注入到参数
        if mcp_info.get("needs_path") and path:
            # 找到占位符替换
            if "{}" in args:
                args = [path if arg == "{}" else arg for arg in args]
            elif args and args[-1] == "{}":
                args[-1] = path

        # 检查是否已存在
        configs = load_mcp_configs()
        if mcp_id in configs:
            raise HTTPException(status_code=400, detail=f"{mcp_info['name']} 已安装")

        # 创建配置
        config = MCPConfig(
            id=mcp_id,
            name=mcp_info["name"],
            transport_type="stdio",
            command=command,
            args=args,
            env=env if env else None,
            description=mcp_info.get("description", f"从市场安装的 {mcp_info['name']}"),
            enabled=True,
        )

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

        # 尝试连接
        connected = False
        try:
            connected = await conn.connect()
        except Exception as e:
            print(f"连接失败: {e}")

        return {
            "success": True,
            "id": config.id,
            "name": config.name,
            "connected": connected,
            "message": f"{mcp_info['name']} 安装成功！",
        }

    @app.post(f"{api_prefix}/mcp/connect/{{server_id}}")
    async def connect_mcp_server(server_id: str):
        """连接 MCP 服务器"""
        configs = load_mcp_configs()
        if server_id not in configs:
            raise HTTPException(status_code=404, detail="服务器不存在")

        config = configs[server_id]
        client = get_mcp_client()
        conn = client.get_connection(server_id)

        if not conn:
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
            return {"success": True, "connected": True, "message": "已经连接"}

        connected = await conn.connect()
        return {
            "success": True,
            "connected": connected,
            "message": "连接成功" if connected else "连接失败",
        }

    @app.post(f"{api_prefix}/mcp/install-dependency")
    async def install_mcp_dependency(request: dict):
        """一键安装缺失依赖（node/uv 等）"""
        dependency = request.get("dependency")
        if not dependency:
            raise HTTPException(status_code=400, detail="缺少 dependency 参数")

        success, message = DependencyInstaller.install_dependency(dependency)
        return {
            "success": success,
            "message": message,
        }

    @app.get(f"{api_prefix}/mcp/check-health/{{server_id}}")
    async def check_mcp_health(server_id: str):
        """检查服务器健康状态"""
        configs = load_mcp_configs()
        if server_id not in configs:
            raise HTTPException(status_code=404, detail="服务器不存在")

        client = get_mcp_client()
        conn = client.get_connection(server_id)

        if not conn:
            return {
                "server_id": server_id,
                "health": HealthStatus.UNKNOWN,
                "status": "未连接",
            }

        connected = conn.connected
        last_error = conn.last_error
        health = enhanced_manager.check_health(server_id, connected, last_error)

        return {
            "server_id": server_id,
            "health": health.value,
            "connected": connected,
            "last_error": last_error,
            "status": {
                HealthStatus.RUNNING: "运行中",
                HealthStatus.STOPPED: "已停止",
                HealthStatus.TIMEOUT: "连接超时",
                HealthStatus.ERROR: "错误",
                HealthStatus.UNKNOWN: "未知",
            }[health],
        }

    @app.get(f"{api_prefix}/mcp/secrets/list")
    async def list_mcp_secrets(environment: str = "default"):
        """列出存储的密钥（只显示名称，不显示值）"""
        keys = enhanced_manager.secret_manager.list_keys(environment)
        return {
            "keys": keys,
            "environment": environment,
            "environments": list(enhanced_manager.secret_manager._secrets.keys()),
        }

    @app.post(f"{api_prefix}/mcp/secrets/set")
    async def set_mcp_secret(request: dict):
        """设置密钥"""
        key = request.get("key")
        value = request.get("value")
        environment = request.get("environment", "default")

        if not key:
            raise HTTPException(status_code=400, detail="缺少 key")

        enhanced_manager.secret_manager.set_secret(key, value, environment)
        return {"success": True, "message": f"已保存 {key}"}

    @app.post(f"{api_prefix}/mcp/secrets/add")
    async def add_mcp_secret(request: dict):
        """添加密钥"""
        key = request.get("key")
        value = request.get("value")
        environment = request.get("environment", "default")

        if not key or not value:
            raise HTTPException(status_code=400, detail="缺少 key 或 value")

        enhanced_manager.secret_manager.set_secret(key, value, environment)
        return {"success": True, "message": f"已添加 {key}"}

    @app.delete(f"{api_prefix}/mcp/secrets/{{key}}")
    async def delete_mcp_secret(key: str, environment: str = "default"):
        """删除密钥"""
        success = enhanced_manager.secret_manager.delete_secret(key, environment)
        if not success:
            raise HTTPException(status_code=404, detail=f"密钥 {key} 不存在")
        return {"success": True}

    @app.post(f"{api_prefix}/mcp/secrets/set-environment")
    async def set_mcp_environment(request: dict):
        """设置当前环境"""
        environment = request.get("environment", "default")
        # 这里只是记录当前选择，实际注入时使用选择的环境
        # 可以存储到全局或配置中
        return {"success": True, "current_environment": environment}

    @app.get(f"{api_prefix}/mcp/stats/{{server_id}}")
    async def get_mcp_stats(server_id: str):
        """获取服务器统计信息"""
        stats = enhanced_manager.get_stats(server_id)
        return {
            "server_id": server_id,
            "stats": stats.get(server_id, stats),
        }

    @app.post(f"{api_prefix}/mcp/confirm-operation")
    async def confirm_mcp_operation(request: dict):
        """确认待执行的高危操作"""
        confirmation_id = request.get("confirmation_id")
        if not confirmation_id:
            raise HTTPException(status_code=400, detail="缺少 confirmation_id")

        operation = enhanced_manager.confirm_pending_operation(confirmation_id)
        if not operation:
            raise HTTPException(status_code=404, detail="待确认操作不存在或已过期")

        return {
            "success": True,
            "operation": operation,
        }

    # 预设组合包 - 预置场景模板
    preset_bundles = {
        "code-assistant": {
            "name": "代码助手",
            "description": "适合日常编程开发，包含文件系统、Git 和终端工具",
            "mcp_servers": ["filesystem", "git", "terminal"],
            "persona": {
                "name": "代码助手",
                "role": "专业软件开发工程师",
                "description": "帮你编写、阅读、调试代码，管理项目",
                "system_prompt": "你是一位经验丰富的软件开发工程师，擅长编写高质量代码，调试问题，重构项目，帮助用户高效开发。",
            },
        },
        "research-assistant": {
            "name": "学术研究助手",
            "description": "适合文献检索和学术研究，包含 Arxiv 和网页搜索",
            "mcp_servers": ["brave-search", "arxiv", "memory"],
            "persona": {
                "name": "研究助手",
                "role": "学术研究助手",
                "description": "帮助查找文献，总结论文，追踪最新研究进展",
                "system_prompt": "你是一位专业的研究助手，擅长搜索学术文献，总结研究成果，帮助用户快速了解领域最新进展。",
            },
        },
        "data-analyst": {
            "name": "数据分析助手",
            "description": "适合数据处理分析，包含 Pandas 和数据库访问",
            "mcp_servers": ["postgres", "sqlite", "filesystem"],
            "persona": {
                "name": "数据分析助手",
                "role": "数据分析专家",
                "description": "帮助探索数据，生成分析报告，可视化结果",
                "system_prompt": "你是一位专业的数据分析师，擅长探索数据、发现洞察、生成清晰的分析报告。",
            },
        },
        "web-dev": {
            "name": "Web 开发调试",
            "description": "适合前端开发调试，包含 Puppeteer 浏览器自动化",
            "mcp_servers": ["filesystem", "puppeteer"],
            "persona": {
                "name": "Web 开发工程师",
                "role": "前端开发专家",
                "description": "帮助开发和调试网页应用，自动化测试",
                "system_prompt": "你是一位专业的前端开发工程师，精通现代 Web 技术栈，帮助开发调试网页应用，解决界面交互问题。",
            },
        },
    }

    @app.get(f"{api_prefix}/mcp/presets")
    async def list_mcp_presets():
        """列出所有预设组合包"""
        result = []
        for bundle_id, bundle in preset_bundles.items():
            result.append(
                {
                    "id": bundle_id,
                    **bundle,
                }
            )
        return {"presets": result}

    @app.post(f"{api_prefix}/mcp/presets/apply")
    async def apply_mcp_preset(request: dict):
        """应用预设组合包（从前端schema调用）"""
        preset = request.get("preset")
        if not preset:
            raise HTTPException(status_code=400, detail="缺少 preset 参数")

        # preset名称映射，前端使用下划线，后端使用连字符
        preset_map = {
            "code_assistant": "code-assistant",
            "academic_search": "research-assistant",
            "data_analysis": "data-analyst",
            "web_automation": "web-dev",
        }
        bundle_id = preset_map.get(preset, preset)

        if bundle_id not in preset_bundles:
            raise HTTPException(status_code=404, detail=f"预设 {bundle_id} 不存在")

        bundle = preset_bundles[bundle_id]
        created = []

        # 检查哪些需要安装
        existing_configs = load_mcp_configs()

        for mcp_id in bundle["mcp_servers"]:
            if mcp_id in existing_configs:
                created.append(
                    {
                        "id": mcp_id,
                        "name": mcp_id.replace("-", " ").title(),
                        "created": False,
                        "message": "已存在",
                    }
                )
                continue

            # 根据常见MCP名称创建默认配置
            default_configs = {
                "filesystem": {
                    "name": "Filesystem",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", str(root_dir)],
                    "env": {},
                    "description": "文件系统访问",
                    "security": {
                        "readonly": False,
                        "allowed_paths": [str(root_dir)],
                    },
                },
                "git": {
                    "name": "Git",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-git"],
                    "env": {},
                    "description": "Git 仓库操作",
                },
                "terminal": {
                    "name": "Terminal",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-terminal"],
                    "env": {},
                    "description": "终端命令执行",
                    "security": {
                        "confirm_on_dangerous": True,
                    },
                },
                "brave-search": {
                    "name": "Brave Search",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                    "env": {},
                    "description": "Brave 网页搜索",
                    "needs_token": True,
                    "token_name": "BRAVE_API_KEY",
                },
                "arxiv": {
                    "name": "Arxiv",
                    "command": "npx",
                    "args": ["-y", "mcp-arxiv-server"],
                    "env": {},
                    "description": "Arxiv 文献搜索",
                },
                "postgres": {
                    "name": "PostgreSQL",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-postgres", "${POSTGRES_CONNECTION_STRING}"],
                    "env": {},
                    "description": "PostgreSQL 数据库访问",
                },
                "sqlite": {
                    "name": "SQLite",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-sqlite"],
                    "env": {},
                    "description": "SQLite 数据库访问",
                },
                "puppeteer": {
                    "name": "Puppeteer",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
                    "env": {},
                    "description": "Chrome 浏览器自动化",
                },
                "memory": {
                    "name": "Memory",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"],
                    "env": {},
                    "description": "知识图谱记忆存储",
                },
                "github": {
                    "name": "GitHub",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {},
                    "description": "GitHub API 访问",
                    "needs_token": True,
                    "token_name": "GITHUB_PERSONAL_ACCESS_TOKEN",
                },
            }

            default_config = default_configs.get(
                mcp_id,
                {
                    "name": mcp_id.replace("-", " ").title(),
                    "command": "npx",
                    "args": ["-y", f"mcp-{mcp_id}-server"],
                    "env": {},
                    "description": f"{mcp_id} MCP 服务器",
                },
            )

            config = MCPConfig(
                id=mcp_id,
                enabled=True,
                **default_config,
            )

            existing_configs[mcp_id] = config
            created.append(
                {
                    "id": mcp_id,
                    "name": default_config["name"],
                    "created": True,
                    "needs_token": default_config.get("needs_token", False),
                    "token_name": default_config.get("token_name"),
                }
            )

        # 保存配置
        save_mcp_configs(existing_configs)

        # 创建人格
        persona_bundle = bundle.get("persona", {})
        if persona_bundle:
            created_persona = persona_store.create_persona(
                full_name=persona_bundle.get("name", bundle["name"]),
                role=persona_bundle.get("role", ""),
                description=persona_bundle.get("description", bundle["description"]),
                system_prompt=persona_bundle.get("system_prompt", ""),
                mcp_enabled=True,
                mcp_servers=bundle["mcp_servers"],
            )
        else:
            created_persona = None

        return {
            "success": True,
            "bundle_id": bundle_id,
            "bundle_name": bundle["name"],
            "created_servers": created,
            "created_persona": created_persona.to_dict() if created_persona else None,
        }

    @app.get(f"{api_prefix}/mcp/export")
    async def export_mcp_config():
        """导出当前配置（所有MCP服务器 + 人格）"""
        from datetime import datetime

        export_data = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "personas": [],
            "mcp_servers": [],
        }

        # 导出所有人格
        personas = persona_store.list_personas()
        for persona in personas:
            export_data["personas"].append(persona.to_dict())

        # 导出所有MCP服务器
        configs = load_mcp_configs()
        for server in configs.values():
            export_data["mcp_servers"].append(server.dict())

        return JSONResponse(
            content=export_data,
            headers={
                "Content-Disposition": "attachment; filename=agnes-mcp-config.json",
            },
        )

    @app.post(f"{api_prefix}/mcp/import")
    async def import_mcp_config(file: UploadFile = File(...)):
        """导入 MCP 配置包"""
        import json

        try:
            content = await file.read()
            import_data = json.loads(content.decode("utf-8"))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"无效的 JSON 文件: {str(e)}")

        imported = {
            "personas": [],
            "servers": [],
            "conflicts": [],
        }

        existing_configs = load_mcp_configs()
        existing_personas = {p.id: p for p in persona_store.list_personas()}

        # 导入 MCP 服务器
        for server_data in import_data.get("mcp_servers", import_data.get("mcp_servers", [])):
            server_id = server_data.get("id")
            if not server_id:
                continue

            if server_id in existing_configs:
                imported["conflicts"].append(
                    {
                        "id": server_id,
                        "name": server_data.get("name", server_id),
                        "reason": "ID 已存在",
                    }
                )
                continue

            config = MCPConfig(**server_data)
            existing_configs[server_id] = config
            imported["servers"].append(
                {
                    "id": server_id,
                    "name": config.name,
                }
            )

        # 导入人格
        for persona_data in import_data.get(
            "personas", [] if "persona" in import_data else [import_data.get("persona")]
        ):
            if not persona_data:
                continue

            try:
                persona_id = persona_data.get("id")
                if persona_id and persona_id in existing_personas:
                    imported["conflicts"].append(
                        {
                            "id": persona_id,
                            "name": persona_data.get("full_name", persona_id),
                            "reason": "ID 已存在",
                        }
                    )
                    continue

                # 创建新人格
                created = persona_store.create_persona(
                    full_name=persona_data.get("full_name", "Imported Persona"),
                    nickname=persona_data.get("nickname", ""),
                    role=persona_data.get("role", ""),
                    personality=persona_data.get("personality", ""),
                    scenario=persona_data.get("scenario", ""),
                    system_prompt=persona_data.get("system_prompt", ""),
                    llm_profile_id=persona_data.get("llm_profile_id"),
                    description=persona_data.get("description", ""),
                    enabled=persona_data.get("enabled", True),
                    mcp_enabled=persona_data.get("mcp_enabled", True),
                    mcp_servers=persona_data.get("mcp_servers", []),
                    skills=persona_data.get("skills"),
                )
                imported["personas"].append(
                    {
                        "id": created.id,
                        "name": created.full_name,
                    }
                )
            except Exception as e:
                imported["conflicts"].append(
                    {
                        "id": "persona",
                        "reason": str(e),
                    }
                )

        # 保存配置
        save_mcp_configs(existing_configs)

        return {
            "success": True,
            "imported": imported,
            "message": f"导入完成: {len(imported['servers'])} 个服务器, {len(imported['personas'])} 个人格",
        }

    @app.post(f"{api_prefix}/mcp/export-bundle")
    async def export_mcp_bundle(request: dict):
        """导出 MCP 配置包（包含人格和MCP配置）"""
        from datetime import datetime

        persona_id = request.get("persona_id")
        selected_servers = request.get("mcp_servers", [])

        export_data = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "persona": None,
            "mcp_servers": [],
        }

        if persona_id:
            persona = persona_store.get_persona(persona_id)
            if persona:
                export_data["persona"] = persona.to_dict()
                # 如果没有指定服务器，使用人格绑定的服务器
                if not selected_servers and persona.mcp_servers:
                    selected_servers = persona.mcp_servers

        configs = load_mcp_configs()
        for server_id in selected_servers:
            if server_id in configs:
                export_data["mcp_servers"].append(configs[server_id].dict())

        return JSONResponse(
            content=export_data,
            headers={
                "Content-Disposition": f"attachment; filename=agnes-mcp-bundle-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json",
            },
        )

    @app.post(f"{api_prefix}/mcp/import-bundle")
    async def import_mcp_bundle(file: UploadFile = File(...)):
        """导入 MCP 配置包"""
        import json

        try:
            content = await file.read()
            import_data = json.loads(content.decode("utf-8"))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"无效的 JSON 文件: {str(e)}")

        imported = {
            "persona": None,
            "servers": [],
            "conflicts": [],
        }

        existing_configs = load_mcp_configs()

        # 导入 MCP 服务器
        for server_data in import_data.get("mcp_servers", []):
            server_id = server_data.get("id")
            if not server_id:
                continue

            if server_id in existing_configs:
                imported["conflicts"].append(
                    {
                        "id": server_id,
                        "name": server_data.get("name", server_id),
                        "reason": "ID 已存在",
                    }
                )
                continue

            config = MCPConfig(**server_data)
            existing_configs[server_id] = config
            imported["servers"].append(
                {
                    "id": server_id,
                    "name": config.name,
                }
            )

        # 导入人格
        persona_data = import_data.get("persona")
        if persona_data:
            try:
                # 创建新人格
                created = persona_store.create_persona(
                    full_name=persona_data.get("full_name", "Imported Persona"),
                    nickname=persona_data.get("nickname", ""),
                    role=persona_data.get("role", ""),
                    personality=persona_data.get("personality", ""),
                    scenario=persona_data.get("scenario", ""),
                    system_prompt=persona_data.get("system_prompt", ""),
                    llm_profile_id=persona_data.get("llm_profile_id"),
                    description=persona_data.get("description", ""),
                    enabled=persona_data.get("enabled", True),
                    mcp_enabled=persona_data.get("mcp_enabled", True),
                    mcp_servers=persona_data.get("mcp_servers", []),
                    skills=persona_data.get("skills"),
                )
                imported["persona"] = {
                    "id": created.id,
                    "name": created.full_name,
                }
            except Exception as e:
                imported["conflicts"].append(
                    {
                        "id": "persona",
                        "reason": str(e),
                    }
                )

        # 保存配置
        save_mcp_configs(existing_configs)

        return {
            "success": True,
            "imported": imported,
            "message": f"导入完成: {len(imported['servers'])} 个服务器, {1 if imported['persona'] else 0} 个人格",
        }

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

    @app.get(f"{api_prefix}/mcp/options")
    async def get_mcp_options(value_field: str = "id", label_field: str = "name"):
        """获取MCP服务器选项列表（供下拉选择使用）"""
        configs = load_mcp_configs()
        options = []
        for config in configs.values():
            if config.enabled:
                value = getattr(config, value_field, config.id)
                label = getattr(config, label_field, config.name)
                options.append({"value": value, "label": label})
        return options

    @app.get(f"{api_prefix}/mcp/logs/list")
    async def get_mcp_call_logs(
        server_id: str = None,
        success: str = None,
        page: int = 1,
        per_page: int = 50,
    ):
        """获取工具调用日志（分页支持Amis表格）"""
        logs = enhanced_manager.get_call_logs(server_id)

        # 根据success过滤
        if success is not None:
            success_bool = success.lower() == "true"
            logs = [log for log in logs if log.get("success") == success_bool]

        # 计算分页
        total = len(logs)
        start = (page - 1) * per_page
        end = start + per_page
        items = logs[start:end]

        return {
            "items": items,
            "total": total,
            "page": page,
            "perPage": per_page,
        }

    @app.get(f"{api_prefix}/mcp/market")
    async def get_mcp_market_list(
        page: int = 1,
        per_page: int = 12,
    ):
        """获取MCP工具市场列表"""
        from web2.schemas.mcp import MCP_MARKET

        # 构建表格数据
        items = []
        for item in MCP_MARKET:
            row = {
                "id": item["id"],
                "name": item["name"],
                "description": item.get("description", ""),
                "category": item.get("category", "其他"),
                "author": item.get("author", "community"),
                "needs_token": item.get("needs_token", False),
                "needs_path": item.get("needs_path", False),
                "token_key": item.get("token_key", item.get("token_name", "")),
            }
            items.append(row)

        # 计算分页
        total = len(items)
        start = (page - 1) * per_page
        end = start + per_page
        page_items = items[start:end]

        return {
            "items": page_items,
            "total": total,
            "page": page,
            "perPage": per_page,
        }

    @app.get(f"{api_prefix}/mcp/logs/stats")
    async def get_mcp_logs_stats():
        """获取调用日志统计概览"""
        return enhanced_manager.get_call_stats()

    @app.delete(f"{api_prefix}/mcp/logs/{{log_id}}")
    async def delete_mcp_log(log_id: str):
        """删除单条日志"""
        success = enhanced_manager.delete_call_log(log_id)
        if not success:
            raise HTTPException(status_code=404, detail="日志不存在")
        return {"success": True}

    @app.delete(f"{api_prefix}/mcp/logs")
    async def clear_mcp_logs():
        """清空所有日志"""
        enhanced_manager.clear_call_logs()
        return {"success": True, "message": "所有日志已清空"}

    # 预设API
    from web2.schemas.mcp import MCP_PRESETS

    @app.get(f"{api_prefix}/mcp/presets/list")
    async def list_mcp_presets_full():
        """列出所有预设模板（完整格式）"""
        return {
            "items": MCP_PRESETS,
            "total": len(MCP_PRESETS),
        }

    @app.post(f"{api_prefix}/mcp/presets/apply/{{preset_id}}")
    async def apply_mcp_preset_full(preset_id: str):
        """应用预设模板"""
        # 查找预设
        preset = None
        for p in MCP_PRESETS:
            if p["id"] == preset_id:
                preset = p
                break

        if not preset:
            raise HTTPException(status_code=404, detail=f"预设 {preset_id} 不存在")

        created = []
        existing_configs = load_mcp_configs()

        # 常见默认配置
        default_configs = {
            "filesystem": {
                "name": "Filesystem",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", str(root_dir)],
                "env": {},
                "description": "文件系统访问",
                "security": {
                    "readonly": False,
                    "allowed_paths": [str(root_dir)],
                },
            },
            "git": {
                "name": "Git",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-git"],
                "env": {},
                "description": "Git 仓库操作",
            },
            "terminal": {
                "name": "Terminal",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-terminal"],
                "env": {},
                "description": "终端命令执行",
                "security": {
                    "confirm_on_dangerous": True,
                },
            },
            "brave-search": {
                "name": "Brave Search",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                "env": {},
                "description": "Brave 网页搜索",
            },
            "arxiv": {
                "name": "Arxiv",
                "command": "npx",
                "args": ["-y", "mcp-arxiv-server"],
                "env": {},
                "description": "Arxiv 文献搜索",
            },
            "postgres": {
                "name": "PostgreSQL",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-postgres"],
                "env": {},
                "description": "PostgreSQL 数据库访问",
            },
            "snowflake": {
                "name": "Snowflake",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-snowflake"],
                "env": {},
                "description": "Snowflake 数据仓库访问",
            },
            "bigquery": {
                "name": "BigQuery",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-bigquery"],
                "env": {},
                "description": "Google BigQuery 访问",
            },
            "redis": {
                "name": "Redis",
                "command": "uvx",
                "args": ["mcp-redis-server"],
                "env": {},
                "description": "Redis 缓存访问",
            },
            "sqlite": {
                "name": "SQLite",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-sqlite"],
                "env": {},
                "description": "SQLite 数据库访问",
            },
            "puppeteer": {
                "name": "Puppeteer",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
                "env": {},
                "description": "Chrome 浏览器自动化",
            },
            "memory": {
                "name": "Memory",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-memory"],
                "env": {},
                "description": "知识图谱记忆存储",
            },
            "github": {
                "name": "GitHub",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {},
                "description": "GitHub API 访问",
            },
        }

        for mcp_id in preset.get("mcps", []):
            if mcp_id in existing_configs:
                created.append(
                    {
                        "id": mcp_id,
                        "name": existing_configs[mcp_id].name,
                        "created": False,
                        "message": "已存在",
                    }
                )
                continue

            default_config = default_configs.get(
                mcp_id,
                {
                    "name": mcp_id.replace("-", " ").title(),
                    "command": "npx",
                    "args": ["-y", f"mcp-{mcp_id}-server"],
                    "env": {},
                    "description": f"{mcp_id} MCP 服务器",
                },
            )

            config = MCPConfig(
                id=mcp_id,
                enabled=True,
                **default_config,
            )

            existing_configs[mcp_id] = config
            created.append(
                {
                    "id": mcp_id,
                    "name": default_config["name"],
                    "created": True,
                }
            )

        # 保存配置
        save_mcp_configs(existing_configs)

        return {
            "success": True,
            "preset_id": preset_id,
            "preset_name": preset["name"],
            "created": created,
            "message": f"预设应用完成，创建 {len([c for c in created if c['created']])} 个服务器",
        }

    @app.post(f"{api_prefix}/mcp/presets/export")
    async def export_mcp_preset(request: dict):
        """导出自定义预设"""
        name = request.get("name")
        description = request.get("description", "")
        mcp_ids = request.get("mcps", [])
        category = request.get("category", "自定义")

        export_data = {
            "id": name.lower().replace(" ", "-").replace("_", "-"),
            "name": name,
            "description": description,
            "category": category,
            "mcps": mcp_ids,
            "created_at": None,
        }

        return JSONResponse(
            content=export_data,
            headers={
                "Content-Disposition": f"attachment; filename=agnes-mcp-preset-{export_data['id']}.json",
            },
        )

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

    # ============ Skills 上传 API ============

    @app.post(f"{api_prefix}/skills/upload")
    async def upload_skills(file: UploadFile = File(...)):
        """上传包含 skills 的 zip 压缩包"""
        import shutil
        import tempfile
        import zipfile

        # 验证文件类型
        if not file.filename.endswith(".zip"):
            raise HTTPException(status_code=400, detail="只支持 .zip 格式的压缩包")

        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_zip = Path(temp_dir) / "skills.zip"

            # 保存上传的文件
            with open(temp_zip, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            # 解压到临时目录
            extract_dir = Path(temp_dir) / "extracted"
            extract_dir.mkdir()

            try:
                with zipfile.ZipFile(temp_zip, "r") as zip_ref:
                    zip_ref.extractall(extract_dir)
            except zipfile.BadZipFile:
                raise HTTPException(status_code=400, detail="无效的 zip 文件")

            # 查找所有 yaml 文件
            skills_dir = root_dir / "config" / "skills"
            skills_dir.mkdir(parents=True, exist_ok=True)

            uploaded_count = 0
            errors = []

            # 遍历解压的文件
            for yaml_file in extract_dir.rglob("*.yaml"):
                try:
                    # 复制到 skills 目录
                    dest_file = skills_dir / yaml_file.name
                    shutil.copy2(yaml_file, dest_file)
                    uploaded_count += 1
                except Exception as e:
                    errors.append(f"{yaml_file.name}: {str(e)}")

            # 也查找 .yml 文件
            for yaml_file in extract_dir.rglob("*.yml"):
                try:
                    dest_file = skills_dir / yaml_file.name
                    shutil.copy2(yaml_file, dest_file)
                    uploaded_count += 1
                except Exception as e:
                    errors.append(f"{yaml_file.name}: {str(e)}")

            # 重新加载 skills
            if uploaded_count > 0:
                try:
                    from agnes.skills import load_and_register_all

                    load_and_register_all(skills_dir)
                except Exception as e:
                    errors.append(f"重新加载失败: {str(e)}")

            return {
                "success": True,
                "uploaded_count": uploaded_count,
                "errors": errors if errors else None,
                "message": f"成功上传 {uploaded_count} 个 Skill 文件",
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
