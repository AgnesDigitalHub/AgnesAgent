"""
Agnes Server - amis Web 控制台 + OpenAI 兼容 API
"""

import json
import os
import time
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse

from agnes import ChatHistory, get_logger
from agnes.config import SETTINGS_SECTIONS, ConfigManager, LLMProfile, SettingsStorage

from .models import (
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionUsage,
    ChatMessage,
    CreateProfileRequest,
    ProfileListResponse,
    ProfileResponse,
    StatusResponse,
    SuccessResponse,
    UpdateProfileRequest,
)
from .schemas.agents import get_agents_schema
from .schemas.chat import get_chat_schema
from .schemas.dashboard import get_dashboard_schema
from .schemas.knowledge import get_knowledge_schema
from .schemas.logs import get_logs_schema
from .schemas.models import get_models_schema
from .schemas.prompts import get_prompts_schema
from .schemas.publish import get_publish_schema
from .schemas.settings import get_settings_schema
from .schemas.tools import get_tools_schema
from .schemas.users import get_users_schema
from .schemas.workflows import get_workflows_schema

logger = get_logger("agnes.server.api")


class AgnesServer:
    """Agnes 服务端 - amis Web 控制台"""

    def __init__(self, agent, storage_dir: str = "config/llm_profiles"):
        """
        初始化服务端

        Args:
            agent: AgnesAgent 实例
            storage_dir: 配置存储目录
        """
        self.agent = agent
        self.config = agent.config
        self.config_manager = ConfigManager(storage_dir)
        self.settings_storage = SettingsStorage()

        if self.agent.chat_history is None:
            self.agent.chat_history = ChatHistory(max_messages=20)

        self.app = FastAPI(lifespan=self.lifespan)
        self._setup_routes()

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """生命周期管理"""
        logger.info("Starting Agnes Server...")
        await self._auto_restore_llm()
        yield
        logger.info("Shutting down Agnes Server...")
        if self.agent:
            await self.agent.close()

    async def _auto_restore_llm(self):
        """
        服务启动时自动从持久化配置恢复 LLM Provider。
        优先顺序：
        1. config/settings/llm.json（SettingsStorage）
        2. 上次激活的 LLM Profile（从 .active 文件读取）
        3. 最近更新的 LLM Profile（兜底）
        """
        from agnes.utils.config_loader import LLMConfig

        def _build_llm_config(provider, model, base_url, api_key, temperature, max_tokens):
            """构建 LLMConfig，正确处理 openvino-server"""
            actual_provider = provider
            if provider == "openvino-server" or provider == "local-api":
                # openvino-server 和 local-api 都是 OpenAI 兼容的本地服务，无需 API key
                actual_provider = "openai"
                # 本地服务不需要真实 api_key；传 None 或空字符串均可
                # 不要强制 "dummy"，避免部分 client 将其当作有效 key 发送
            return LLMConfig(
                provider=actual_provider,
                model=model,
                base_url=base_url,
                api_key=api_key or None,
                temperature=float(temperature) if temperature is not None else 0.7,
                max_tokens=max_tokens,
            )

        # 1. 尝试从 settings/llm.json 恢复
        try:
            llm_data = self.settings_storage.load_section("llm")
            provider = llm_data.get("provider", "")
            model = llm_data.get("model", "")
            if provider and model:
                llm_config = _build_llm_config(
                    provider=provider,
                    model=model,
                    base_url=llm_data.get("base_url"),
                    api_key=llm_data.get("api_key"),
                    temperature=llm_data.get("temperature", 0.7),
                    max_tokens=llm_data.get("max_tokens"),
                )
                await self.agent.setup_llm(llm_config, display_provider=provider)
                logger.info(f"Auto-restored LLM from settings/llm.json: {provider}/{model}")
                return
        except Exception as e:
            logger.warning(f"Failed to restore LLM from settings/llm.json: {e}")

        # 2. 尝试从上次激活的 Profile 恢复（.active 文件）
        # 3. 兜底：最近更新的第一个 Profile
        try:
            # 优先使用 .active 记录的 Profile，否则取列表第一个
            profile = self.config_manager.get_active_profile()
            if profile is None:
                profiles = self.config_manager.list_profiles()
                profile = profiles[0] if profiles else None

            if profile:
                llm_config = _build_llm_config(
                    provider=profile.provider,
                    model=profile.model,
                    base_url=profile.base_url,
                    api_key=profile.api_key,
                    temperature=profile.temperature,
                    max_tokens=profile.max_tokens,
                )
                await self.agent.setup_llm(llm_config, display_provider=profile.provider)
                self.config_manager.activate_profile(profile.id)
                logger.info(f"Auto-restored LLM from profile: {profile.name} ({profile.provider}/{profile.model})")
                return
        except Exception as e:
            logger.warning(f"Failed to restore LLM from profiles: {e}")

        logger.info("No persisted LLM config found, LLM not initialized at startup")

    def _profile_to_response(self, profile: LLMProfile) -> ProfileResponse:
        """将配置转换为响应格式"""
        active_profile = self.config_manager.get_active_profile()
        is_active = bool(active_profile and active_profile.id == profile.id)

        return ProfileResponse(
            id=profile.id,
            name=profile.name,
            description=profile.description,
            provider=profile.provider,
            model=profile.model,
            base_url=profile.base_url,
            temperature=profile.temperature,
            max_tokens=profile.max_tokens,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
            is_active=is_active,
        )

    def _setup_routes(self):
        """设置路由"""

        # ============================================
        # 根路径 - 重定向到 web2
        # ============================================

        @self.app.get("/")
        async def root():
            """根路径 - 重定向到 web2"""
            from fastapi.responses import RedirectResponse

            return RedirectResponse(url="/web2")

        @self.app.get("/favicon.ico")
        @self.app.get("/icon.png")
        async def favicon():
            """网站图标"""
            # 先尝试 favicon.ico
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.png")
            if os.path.exists(icon_path):
                return FileResponse(icon_path, media_type="image/x-icon")
            # 再尝试 icon.png
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "favicon.ico")
            if os.path.exists(icon_path):
                return FileResponse(icon_path, media_type="image/png")
            raise HTTPException(status_code=404, detail="Icon not found")

        # ============================================
        # amis App JSON - 完整内嵌所有页面 schema，必须在 /web2/{path:path} 之前注册
        # ============================================
        @self.app.get("/web2/app.json")
        async def get_amis_app_json():
            """返回完整的 amis app 配置（所有页面 schema 内嵌，无 schemaApi 异步���求）"""
            app_config = {
                "type": "app",
                "brandName": "Agnes Agent",
                "logo": "/favicon.ico",
                "footer": "",
                "pages": [
                    {"path": "/", "redirect": "/dashboard"},
                    {
                        "path": "/dashboard",
                        "label": "Dashboard",
                        "icon": "fa fa-tachometer",
                        "schema": get_dashboard_schema(),
                    },
                    {"path": "/models", "label": "模型管理", "icon": "fa fa-brain", "schema": get_models_schema()},
                    {"path": "/chat", "label": "聊天", "icon": "fa fa-comments", "schema": get_chat_schema()},
                    {"path": "/agents", "label": "Agent 管理", "icon": "fa fa-robot", "schema": get_agents_schema()},
                    {
                        "path": "/prompts",
                        "label": "Prompt IDE",
                        "icon": "fa fa-comment",
                        "schema": get_prompts_schema(),
                    },
                    {"path": "/tools", "label": "工具/插件", "icon": "fa fa-wrench", "schema": get_tools_schema()},
                    {
                        "path": "/knowledge",
                        "label": "知识库/RAG",
                        "icon": "fa fa-book",
                        "schema": get_knowledge_schema(),
                    },
                    {
                        "path": "/workflows",
                        "label": "Workflow 编排",
                        "icon": "fa fa-link",
                        "schema": get_workflows_schema(),
                    },
                    {"path": "/logs", "label": "运行日志", "icon": "fa fa-history", "schema": get_logs_schema()},
                    {"path": "/publish", "label": "API/集成", "icon": "fa fa-plug", "schema": get_publish_schema()},
                    {"path": "/users", "label": "用户权限", "icon": "fa fa-users", "schema": get_users_schema()},
                    {"path": "/settings", "label": "系统设置", "icon": "fa fa-cog", "schema": get_settings_schema()},
                ],
            }
            return JSONResponse(content=app_config)

        # ============================================
        # amis Web2 控制台
        # ============================================
        @self.app.get("/web2", response_class=HTMLResponse)
        @self.app.get("/web2/{path:path}")
        async def index():
            """主页 - amis Web2 控制台"""
            template_path = os.path.join(os.path.dirname(__file__), "../../agnes/web/templates/index.html")
            template_path = os.path.abspath(template_path)
            logger.info(f"Loading amis Web2 console from: {template_path}")
            if os.path.exists(template_path):
                with open(template_path, encoding="utf-8") as f:
                    return HTMLResponse(content=f.read())
            return HTMLResponse(
                content="""
                <html>
                    <head><title>Agnes Agent</title></head>
                    <body>
                        <h1>Agnes Agent</h1>
                        <p>Template not found</p>
                    </body>
                </html>
                """
            )

        # ============================================
        # amis Schema API
        # ============================================
        @self.app.get("/web2/api/schema/dashboard")
        async def schema_dashboard():
            """Dashboard 页面 Schema"""
            return get_dashboard_schema()

        @self.app.get("/web2/api/schema/chat")
        async def schema_chat():
            """聊天页面 Schema"""
            return get_chat_schema()

        @self.app.get("/web2/api/schema/agents")
        async def schema_agents():
            """Agent 管理页面 Schema"""
            return get_agents_schema()

        @self.app.get("/web2/api/schema/models")
        async def schema_models():
            """模型管理页面 Schema"""
            return get_models_schema()

        @self.app.get("/web2/api/schema/workflows")
        async def schema_workflows():
            """Workflow 编排页面 Schema"""
            return get_workflows_schema()

        @self.app.get("/web2/api/schema/tools")
        async def schema_tools():
            """工具管理页面 Schema"""
            return get_tools_schema()

        @self.app.get("/web2/api/schema/knowledge")
        async def schema_knowledge():
            """知识库页面 Schema"""
            return get_knowledge_schema()

        @self.app.get("/web2/api/schema/logs")
        async def schema_logs():
            """运行日志页面 Schema"""
            return get_logs_schema()

        @self.app.get("/web2/api/schema/prompts")
        async def schema_prompts():
            """Prompt IDE 页面 Schema"""
            return get_prompts_schema()

        @self.app.get("/web2/api/schema/publish")
        async def schema_publish():
            """API 发布页面 Schema"""
            return get_publish_schema()

        @self.app.get("/web2/api/schema/users")
        async def schema_users():
            """用户权限页面 Schema"""
            return get_users_schema()

        @self.app.get("/web2/api/schema/settings")
        async def schema_settings():
            """系统设置页面 Schema"""
            return get_settings_schema()

        # ============================================
        # 业务 API
        # ============================================

        @self.app.get("/api/status", response_model=StatusResponse)
        async def get_status():
            """获取当前状态"""
            llm_provider = self.agent.get_current_llm_provider_name()
            active_profile = self.config_manager.get_active_profile()

            llm_config = None
            if llm_provider:
                llm_config = {
                    "provider": self.agent.config.llm.provider,
                    "model": self.agent.config.llm.model,
                    "base_url": self.agent.config.llm.base_url,
                    "temperature": self.agent.config.llm.temperature,
                }

            return StatusResponse(
                llm_provider=llm_provider,
                llm_config=llm_config,
                active_profile_id=active_profile.id if active_profile else None,
                active_profile_name=active_profile.name if active_profile else None,
            )

        # ============================================
        # 配置管理 API
        # ============================================

        @self.app.get("/api/profiles", response_model=ProfileListResponse)
        async def list_profiles():
            """列出所有配置"""
            profiles = self.config_manager.list_profiles()
            active_profile = self.config_manager.get_active_profile()

            return ProfileListResponse(
                profiles=[self._profile_to_response(p) for p in profiles],
                active_profile_id=active_profile.id if active_profile else None,
            )

        @self.app.get("/api/profiles/{profile_id}", response_model=ProfileResponse)
        async def get_profile(profile_id: str):
            """获取配置详情"""
            profile = self.config_manager.get_profile(profile_id)
            if not profile:
                raise HTTPException(status_code=404, detail="Profile not found")
            return self._profile_to_response(profile)

        @self.app.post("/api/profiles", response_model=ProfileResponse)
        async def create_profile(request: CreateProfileRequest):
            """创建新配置"""
            profile = self.config_manager.create_profile(
                name=request.name,
                description=request.description,
                provider=request.provider,
                model=request.model,
                base_url=request.base_url,
                api_key=request.api_key,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            return self._profile_to_response(profile)

        @self.app.put("/api/profiles/{profile_id}", response_model=ProfileResponse)
        async def update_profile(profile_id: str, request: UpdateProfileRequest):
            """更新配置"""
            update_data = {k: v for k, v in request.dict().items() if v is not None}
            profile = self.config_manager.update_profile(profile_id, **update_data)
            if not profile:
                raise HTTPException(status_code=404, detail="Profile not found")
            return self._profile_to_response(profile)

        @self.app.delete("/api/profiles/{profile_id}", response_model=SuccessResponse)
        async def delete_profile(profile_id: str):
            """删除配置"""
            success = self.config_manager.delete_profile(profile_id)
            if not success:
                raise HTTPException(status_code=404, detail="Profile not found")
            return SuccessResponse(message="Profile deleted")

        @self.app.post("/api/profiles/{profile_id}/activate", response_model=SuccessResponse)
        async def activate_profile(profile_id: str):
            """激活配置"""
            profile = self.config_manager.get_profile(profile_id)
            if not profile:
                raise HTTPException(status_code=404, detail="Profile not found")

            try:
                from agnes.utils.config_loader import LLMConfig

                provider = profile.provider
                actual_provider = provider
                api_key = profile.api_key

                if provider == "openvino-server" or provider == "local-api":
                    # openvino-server 和 local-api 都是 OpenAI 兼容的本地服务，不需要真实 api_key
                    actual_provider = "openai"
                    # 本地服务不需要真实 api_key，设置默认值
                    if not api_key:
                        api_key = "dummy"

                llm_config = LLMConfig(
                    provider=actual_provider,
                    model=profile.model,
                    base_url=profile.base_url,
                    api_key=api_key,
                    temperature=profile.temperature,
                    max_tokens=profile.max_tokens,
                )

                await self.agent.setup_llm(llm_config, display_provider=profile.provider)
                self.config_manager.activate_profile(profile_id)
                return SuccessResponse(message=f"Profile activated: {profile.name}")
            except Exception as e:
                logger.error(f"Failed to activate profile: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ============================================
        # 系统设置 API
        # ============================================

        @self.app.get("/api/settings")
        async def get_all_settings():
            """获取所有分类配置"""
            return self.settings_storage.load_all()

        @self.app.get("/api/settings/{section}")
        async def get_settings_section(section: str):
            """获取某分类配置"""
            if section not in SETTINGS_SECTIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown section: {section}. Valid sections: {SETTINGS_SECTIONS}",
                )
            return self.settings_storage.load_section(section)

        @self.app.put("/api/settings/{section}")
        async def update_settings_section(section: str, data: dict[str, Any]):
            """更新某分类配置"""
            if section not in SETTINGS_SECTIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown section: {section}. Valid sections: {SETTINGS_SECTIONS}",
                )
            success = self.settings_storage.save_section(section, data)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to save settings")
            return {"success": True, "section": section, "data": data}

        @self.app.post("/api/settings/sync-from-yaml")
        async def sync_settings_from_yaml():
            """从 config.yaml 同步配置到分类 JSON"""
            success = self.settings_storage.sync_from_yaml()
            if success:
                return {"success": True, "message": "Settings synced from config.yaml"}
            return {"success": False, "message": "config.yaml not found or sync failed"}

        # ============================================
        # OpenAI 兼容 API - /v1/chat/completions
        # ============================================

        @self.app.post("/v1/chat/completions")
        async def chat_completions(request: ChatCompletionRequest):
            """OpenAI 兼容的聊天补全 API"""
            if not self.agent.llm_provider:
                raise HTTPException(status_code=500, detail="LLM provider not initialized")

            if request.stream:
                return StreamingResponse(
                    stream_openai_response(self.agent, request),
                    media_type="text/event-stream",
                )
            else:
                return create_openai_response(self.agent, request)


def create_app(agent):
    """创建 FastAPI 应用"""
    server = AgnesServer(agent)
    return server.app


async def stream_openai_response(agent, request: ChatCompletionRequest):
    """流式生成 OpenAI 兼容的响应"""

    created = int(time.time())
    msg_id = f"chatcmpl-{uuid4()}"

    messages = request.messages
    if agent.chat_history:
        agent.chat_history.clear()
        for msg in messages:
            if msg.role == "system":
                agent.chat_history.add_system_message(msg.content)
            elif msg.role == "user":
                agent.chat_history.add_user_message(msg.content)
            elif msg.role == "assistant":
                agent.chat_history.add_assistant_message(msg.content)

    full_content = []
    async for token in agent.chat_stream(
        messages[-1].content,
        use_history=len(messages) > 1,
    ):
        full_content.append(token)
        chunk = ChatCompletionChunk(
            id=msg_id,
            object="chat.completion.chunk",
            created=created,
            model=request.model or agent.config.llm.model,
            choices=[
                ChatCompletionChunkChoice(
                    delta=ChatMessage(role="assistant", content=token),
                    index=0,
                )
            ],
        )
        yield f"data: {json.dumps(chunk.model_dump())}\n\n"

    yield "data: [DONE]\n\n"


def create_openai_response(agent, request: ChatCompletionRequest):
    """生成非流式 OpenAI 兼容的响应"""

    created = int(time.time())
    msg_id = f"chatcmpl-{uuid4()}"

    messages = request.messages
    if agent.chat_history:
        agent.chat_history.clear()
        for msg in messages:
            if msg.role == "system":
                agent.chat_history.add_system_message(msg.content)
            elif msg.role == "user":
                agent.chat_history.add_user_message(msg.content)
            elif msg.role == "assistant":
                agent.chat_history.add_assistant_message(msg.content)

    response = agent.chat(
        messages[-1].content,
        use_history=len(messages) > 1,
    )
    result = response.content

    return ChatCompletionResponse(
        id=msg_id,
        object="chat.completion",
        created=created,
        model=request.model or agent.config.llm.model,
        choices=[
            ChatCompletionChoice(
                message=ChatMessage(role="assistant", content=result),
                index=0,
                finish_reason="stop",
            )
        ],
        usage=ChatCompletionUsage(
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
        ),
    )
