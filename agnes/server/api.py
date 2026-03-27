"""
Agnes Server - amis Web 控制台 + NiceGUI Web2 + OpenAI 兼容 API
"""

import json
import os
import time
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse

from agnes import ChatHistory, get_logger
from agnes.config import SETTINGS_SECTIONS, ConfigManager, LLMProfile, SettingsStorage
from agnes.core.llm_provider import LLMResponse

# NiceGUI imports
try:
    from nicegui import ui

    NUI_AVAILABLE = True
except ImportError:
    NUI_AVAILABLE = False

from .models import (
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionUsage,
    ChatMessage,
    CreateProfileRequest,
    Model,
    ModelListResponse,
    ProfileListResponse,
    ProfileResponse,
    StatusResponse,
    SuccessResponse,
    UpdateProfileRequest,
)

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

        # Initialize NiceGUI if available
        self._setup_nicegui()

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
        # amis 控制台（已禁用，保留代码以便恢复）
        # ============================================
        # @self.app.get("/amis", response_class=HTMLResponse)
        # async def index():
        #     """主页 - amis 控制台"""
        #     template_path = os.path.join(os.path.dirname(__file__), "../web/templates/index.html")
        #     template_path = os.path.abspath(template_path)
        #     logger.info(f"Loading amis console from: {template_path}")
        #     if os.path.exists(template_path):
        #         with open(template_path, "r", encoding="utf-8") as f:
        #             return HTMLResponse(content=f.read())
        #     return HTMLResponse(
        #         content="""
        #         <html>
        #             <head><title>Agnes Server</title></head>
        #             <body>
        #                 <h1>Agnes Server</h1>
        #                 <p>Template not found</p>
        #             </body>
        #         </html>
        #         """
        #     )

        # ============================================
        # amis Schema API（已禁用，保留代码以便恢复）
        # ============================================
        # @self.app.get("/api/schema/dashboard")
        # async def schema_dashboard():
        #     """Dashboard 页面 Schema"""
        #     return get_dashboard_schema()

        # @self.app.get("/api/schema/chat")
        # async def schema_chat():
        #     """聊天页面 Schema"""
        #     return get_chat_schema()

        # @self.app.get("/api/schema/agents")
        # async def schema_agents():
        #     """Agent 管理页面 Schema"""
        #     return get_agents_schema()

        # @self.app.get("/api/schema/models")
        # async def schema_models():
        #     """模型管理页面 Schema"""
        #     return get_models_schema()

        # @self.app.get("/api/schema/workflows")
        # async def schema_workflows():
        #     """Workflow 编排页面 Schema"""
        #     return get_workflows_schema()

        # @self.app.get("/api/schema/tools")
        # async def schema_tools():
        #     """工具管理页面 Schema"""
        #     return get_tools_schema()

        # @self.app.get("/api/schema/knowledge")
        # async def schema_knowledge():
        #     """知识库页面 Schema"""
        #     return get_knowledge_schema()

        # @self.app.get("/api/schema/logs")
        # async def schema_logs():
        #     """运行日志页面 Schema"""
        #     return get_logs_schema()

        # @self.app.get("/api/schema/prompts")
        # async def schema_prompts():
        #     """Prompt IDE 页面 Schema"""
        #     return get_prompts_schema()

        # @self.app.get("/api/schema/publish")
        # async def schema_publish():
        #     """API 发布页面 Schema"""
        #     return get_publish_schema()

        # @self.app.get("/api/schema/users")
        # async def schema_users():
        #     """用户权限页面 Schema"""
        #     return get_users_schema()

        # @self.app.get("/api/schema/settings")
        # async def schema_settings():
        #     """系统设置页面 Schema"""
        #     return get_settings_schema()

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
        #
