"""
Agnes Web2 - FastAPI + AMIS SPA 后端
异步按需加载版本：
- 顶层 App 配置一次性返回
- 每个页面 schema 点击时异步获取 /api/pages/{page_name}
- Pydantic + python-amis 构建所有 schema
"""

import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from typing import Optional

# Add parent directory to path
web2_dir = Path(__file__).parent
root_dir = web2_dir.parent
sys.path.insert(0, str(root_dir))

from web2.app_config import get_built_amis_app, get_app_config


def read_index_html() -> str:
    """读取 index.html 模板"""
    template_path = web2_dir / "templates" / "index.html"
    abs_path = template_path.resolve()
    print(f"[DEBUG] 读取 index.html 从绝对路径: {abs_path}")
    print(f"[DEBUG] 文件是否存在: {template_path.exists()}")
    if template_path.exists():
        print(f"[DEBUG] 文件大小: {template_path.stat().st_size} 字节")
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