"""
AgnesAgent Web Server - FastAPI 后端
"""

import json
import os
import threading
import webbrowser
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse

# NiceGUI imports
from pydantic import BaseModel

from agnes import ChatHistory, get_logger
from agnes.core.llm_provider import LLMResponse


class LLMSetupRequest(BaseModel):
    provider: str
    model: str
    base_url: str | None = None
    api_key: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None


class ChatRequest(BaseModel):
    message: str
    use_history: bool = True
    system_prompt: str | None = None


class AgnesWebServer:
    """Agnes Web 服务器"""

    def __init__(self, agent):
        self.agent = agent
        self.config = agent.config
        self.logger = get_logger("agnes.web")

        # 确保 chat_history 已初始化
        if self.agent.chat_history is None:
            self.agent.chat_history = ChatHistory(max_messages=20)

        # 直接读取 HTML 模板
        template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
        with open(template_path, encoding="utf-8") as f:
            self.index_html = f.read()

        self.app = FastAPI(lifespan=self.lifespan)
        self._setup_routes()

        # Initialize NiceGUI
        self._setup_nicegui()

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """生命周期管理"""
        self.logger.info("Starting Agnes Web Server...")
        yield
        self.logger.info("Shutting down Agnes Web Server...")
        if self.agent:
            await self.agent.close()

    def _setup_routes(self):
        """设置路由"""

        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            """主页"""
            return HTMLResponse(content=self.index_html)

        @self.app.get("/favicon.ico")
        @self.app.get("/icon.ico")
        async def favicon():
            """网站图标"""
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.ico")
            return FileResponse(icon_path, media_type="image/png")

        @self.app.get("/api/status")
        async def get_status():
            """获取当前状态"""
            llm_provider = self.agent.get_current_llm_provider_name()
            asr_provider = self.agent.get_current_asr_provider_name()

            llm_config = None
            if llm_provider:
                llm_config = {
                    "provider": self.agent.config.llm.provider,
                    "model": self.agent.config.llm.model,
                    "base_url": self.agent.config.llm.base_url,
                    "temperature": self.agent.config.llm.temperature,
                }

            return {
                "llm_provider": llm_provider,
                "asr_provider": asr_provider,
                "llm_config": llm_config,
                "history_length": len(self.agent.chat_history.messages) if self.agent.chat_history else 0,
            }

        @self.app.post("/api/llm/setup")
        async def setup_llm(request: LLMSetupRequest):
            """配置 LLM"""
            try:
                from agnes.utils.config_loader import LLMConfig

                # 处理 openvino-server 和 local-api：映射到 openai provider
                provider = request.provider
                api_key = request.api_key
                if provider == "openvino-server" or provider == "local-api":
                    provider = "openai"
                    # 本地服务器通常不需要 API key，设置默认值
                    if not api_key:
                        api_key = "dummy"

                llm_config = LLMConfig(
                    provider=provider,
                    model=request.model,
                    base_url=request.base_url,
                    api_key=api_key,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                )

                display_provider = request.provider
                await self.agent.setup_llm(llm_config, display_provider=display_provider)
                self.logger.info(f"LLM set up: {display_provider} - {request.model}")

                return {
                    "success": True,
                    "message": f"LLM configured: {display_provider} - {request.model}",
                    "provider": display_provider,
                    "model": request.model,
                }
            except Exception as e:
                self.logger.error(f"Failed to setup LLM: {e}")
                return {"success": False, "message": str(e)}

        @self.app.post("/api/chat")
        async def chat(request: ChatRequest):
            """聊天（非流式）"""
            if not self.agent.llm_provider:
                return {"success": False, "message": "LLM not initialized"}

            try:
                if request.system_prompt:
                    self.agent.set_system_prompt(request.system_prompt)

                response: LLMResponse = await self.agent.chat(request.message, use_history=request.use_history)

                return {
                    "success": True,
                    "message": response.content,
                    "model": response.model,
                    "usage": response.usage,
                }
            except Exception as e:
                self.logger.error(f"Chat failed: {e}")
                return {"success": False, "message": str(e)}

        @self.app.websocket("/api/chat/stream")
        async def chat_stream(websocket: WebSocket):
            """流式聊天（WebSocket）"""
            await websocket.accept()

            if not self.agent.llm_provider:
                await websocket.send_json({"type": "error", "message": "LLM not initialized"})
                await websocket.close()
                return

            try:
                data = await websocket.receive_text()
                request_data = json.loads(data)

                message = request_data.get("message", "")
                use_history = request_data.get("use_history", True)
                system_prompt = request_data.get("system_prompt")

                if system_prompt:
                    self.agent.set_system_prompt(system_prompt)

                await websocket.send_json({"type": "start"})

                full_response = []
                async for token in self.agent.chat_stream(message, use_history=use_history):
                    full_response.append(token)
                    await websocket.send_json({"type": "token", "content": token})

                await websocket.send_json({"type": "done", "content": "".join(full_response)})

            except WebSocketDisconnect:
                self.logger.info("WebSocket disconnected")
            except Exception as e:
                self.logger.error(f"Stream chat failed: {e}")
                await websocket.send_json({"type": "error", "message": str(e)})
            finally:
                try:
                    await websocket.close()
                except:
                    pass

        @self.app.post("/api/history/clear")
        async def clear_history():
            """清空对话历史"""
            self.agent.clear_history()
            return {"success": True, "message": "History cleared"}

        @self.app.get("/api/history")
        async def get_history():
            """获取对话历史"""
            if not self.agent.chat_history:
                return {"success": True, "messages": []}

            return {
                "success": True,
                "messages": [{"role": msg.role, "content": msg.content} for msg in self.agent.chat_history.messages],
            }

    def _setup_nicegui(self):
        """Setup NiceGUI integration"""
        try:
            # Import web2 app and initialize NiceGUI
            from nicegui import ui

            # Initialize NiceGUI with FastAPI
            ui.run_with(self.app, title="Agnes Agent", storage_secret="agnes-secret-key")

            self.logger.info("NiceGUI integrated successfully at /web2")
        except Exception as e:
            self.logger.warning(f"NiceGUI integration failed: {e}")
            self.logger.info("Continuing without NiceGUI (using original web interface)")


async def start_web_server(agent, host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True):
    """
    启动 Web 服务器

    Args:
        agent: AgnesAgent 实例
        host: 监听地址
        port: 监听端口
        open_browser: 是否自动打开浏览器
    """
    web_server = AgnesWebServer(agent)

    if open_browser:

        def open_browser_thread():
            import time

            time.sleep(1.5)
            webbrowser.open(f"http://{host}:{port}")

        threading.Thread(target=open_browser_thread, daemon=True).start()

    import uvicorn

    config = uvicorn.Config(
        web_server.app,
        host=host,
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()
