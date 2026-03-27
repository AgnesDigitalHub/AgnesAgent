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
    
    # SPA 兜底路由：所有非 API、非静态文件请求都返回 index.html
    # 这样才能支持浏览器直接访问 /dashboard 等前端路由
    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def serve_spa(full_path: str):
        # 过滤掉带扩展名的静态资源请求，避免把 .js/.css 也返回成 html
        if "." in full_path:
            raise HTTPException(status_code=404, detail="静态资源不存在")
        html = read_index_html()
        return HTMLResponse(content=html)

    # 注册 API 路由（模型管理 + 聊天）
    register_api_routes(app, api_prefix)


# ============ LLM 工厂函数 ============

def create_llm_provider(config) -> LLMProvider:
    """根据配置创建 LLM provider 实例"""
    provider_type = config.provider

    if provider_type == "ollama":
        return OllamaProvider(
            base_url=config.base_url or "http://localhost:11434",
            model=config.model,
        )
    elif provider_type == "openai":
        return OpenAIProvider(
            api_key=config.api_key or "",
            base_url=config.base_url or "https://api.openai.com/v1",
            model=config.model,
        )
    elif provider_type == "openvino":
        return OpenVINOProvider(
            model_name_or_path=config.model,
        )
    elif provider_type == "openvino-server":
        # OpenVINO 服务器模式使用 OpenAI 兼容接口
        return OpenAIProvider(
            api_key=config.api_key or "dummy",
            base_url=config.base_url or "http://localhost:8000/v1",
            model=config.model,
        )
    elif provider_type == "local-api":
        # 兼容 OpenAI 兼容格式的本地 API
        return OpenAIProvider(
            api_key=config.api_key or "dummy",
            base_url=config.base_url or "http://localhost:8000/v1",
            model=config.model,
        )
    else:
        raise ValueError(f"不支持的 provider: {provider_type}")


# ============ 模型管理 ============

# 存储路径
storage_path = root_dir / "config" / "llm_profiles" / "profiles.json"
profile_store = ProfileStore(storage_path)


# 请求模型
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
        if not active_profile:
            return {
                "llm_provider": None,
                "active_profile_name": None,
                "llm_config": None,
                "has_active": False
            }
        
        return {
            "llm_provider": active_profile.provider,
            "active_profile_name": active_profile.name,
            "llm_config": active_profile.to_dict(),
            "has_active": True
        }
    
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
                if not active_profile:
                    await websocket.send_json({
                        "type": "error",
                        "message": "没有激活的模型，请先激活"
                    })
                    break

                # 构造对话消息
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})

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