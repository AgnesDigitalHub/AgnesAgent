"""
Agnes Web2 - FastAPI + AMIS SPA 后端
异步按需加载版本：
- 顶层 App 配置一次性返回
- 每个页面 schema 点击时异步获取 /api/pages/{page_name}
- Pydantic + python-amis 构建所有 schema
"""

import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List

# Add parent directory to path
web2_dir = Path(__file__).parent
root_dir = web2_dir.parent
sys.path.insert(0, str(root_dir))

from web2.app_config import get_built_amis_app, get_app_config
from web2.models import ProfileStore, LLMProfile
from web2.persona import PersonaStore, Persona
from agnes.core import LLMProvider
from agnes.providers import OllamaProvider, OpenAIProvider, OpenVINOProvider


def read_index_html() -> str:
    """读取 index.html 模板"""
    template_path = web2_dir / "templates" / "index.html"
    with open(template_path, "r", encoding="utf-8") as f:
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
        """获取单个页面 schema（异步按需加载）"""
        schema = app_config.get_page_schema(page_name)
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
        "openai", "openai-compat", "deepseek", "gemini", 
        "anthropic", "openvino-server", "local-api", "generic"
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
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class FetchModelsRequest(BaseModel):
    provider: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None


# 请求模型 - Persona (Agent)
class CreatePersonaRequest(BaseModel):
    full_name: str
    nickname: str = ""
    role: str = ""
    personality: str = ""
    scenario: str = ""
    system_prompt: str
    llm_profile_id: Optional[str] = None
    description: str = ""
    enabled: bool = True
    mcp_enabled: bool = False
    mcp_servers: Optional[List[str]] = None
    skills: Optional[List[str]] = None


class UpdatePersonaRequest(BaseModel):
    full_name: Optional[str] = None
    nickname: Optional[str] = None
    role: Optional[str] = None
    personality: Optional[str] = None
    scenario: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_profile_id: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    mcp_enabled: Optional[bool] = None
    mcp_servers: Optional[List[str]] = None
    skills: Optional[List[str]] = None




# 请求模型 - 系统设置
class SettingsRequest(BaseModel):
    site_name: Optional[str] = None
    site_description: Optional[str] = None
    site_intro: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    max_tokens: Optional[int] = None
    enable_registration: Optional[bool] = None
    enable_analytics: Optional[bool] = None
    debug_mode: Optional[bool] = None


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
        with open(settings_storage_path, "r", encoding="utf-8") as f:
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
        return {
            "profiles": [p.to_dict() for p in profiles],
            "active": active_id
        }
    
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
            "has_active_persona": False
        }
        
        if active_profile:
            result.update({
                "llm_provider": active_profile.provider,
                "active_profile_name": active_profile.name,
                "llm_config": active_profile.to_dict(),
                "has_active_llm": True
            })
        
        if active_persona:
            result.update({
                "active_persona": active_persona.to_dict(),
                "active_persona_id": active_persona.id,
                "has_active_persona": True
            })
        
        return result
    
    @app.websocket("/ws/chat")
    async def websocket_chat(websocket: WebSocket):
        """聊天 WebSocket 端点 - 流式输出"""
        await websocket.accept()

        llm = get_llm_instance()
        if not llm:
            await websocket.send_json({
                "type": "error",
                "message": "没有激活的模型，请先在模型管理中激活一个配置"
            })
            await websocket.close()
            return

        # 保存对话历史
        if not hasattr(llm, 'chat_history'):
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
                    await websocket.send_json({
                        "type": "error",
                        "message": "没有激活的模型，请先激活"
                    })
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
                            max_tokens=active_profile.max_tokens
                        )
                        async for token in stream:
                            if token:
                                full_response += token
                                await websocket.send_json({
                                    "type": "token",
                                    "content": token
                                })
                    else:
                        # 无历史，单次对话
                        stream = llm.generate_stream(
                            message,
                            temperature=active_profile.temperature,
                            max_tokens=active_profile.max_tokens
                        )
                        async for token in stream:
                            if token:
                                full_response += token
                                await websocket.send_json({
                                    "type": "token",
                                    "content": token
                                })
                    
                    # 添加助手回复到历史
                    if use_history:
                        llm.chat_history.append({"role": "assistant", "content": full_response})
                    
                    await websocket.send_json({"type": "done"})
                    
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
                    
        except WebSocketDisconnect:
            pass

    # ============ 人格管理 API ============

    @app.get(f"{api_prefix}/personas")
    async def list_personas():
        """获取所有人格列表"""
        personas = persona_store.list_personas()
        active_id = persona_store.get_active_id()
        return {
            "personas": [p.to_dict() for p in personas],
            "active": active_id
        }

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
            day = today - datetime.timedelta(days=6-i)
            import random
            tokens = random.randint(1000, 15000)
            data.append({
                "date": day.strftime("%m-%d"),
                "tokens": tokens
            })
        return {
            "xField": "date",
            "yField": "tokens",
            "data": data
        }

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
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"获取模型列表失败: {response.text}"
                    )
                
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
                
                return {
                    "success": True,
                    "count": len(models),
                    "models": models
                }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取模型列表异常: {str(e)}")


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