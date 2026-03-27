#!/usr/bin/env python3
"""
Agnes Web2 - FastAPI + python-amis SPA 应用
异步按需加载版本：
- 顶层 App 配置一次性返回（仅菜单路由）
- 每个页面 schema 点击时异步获取 /api/pages/{page_name}
- Pydantic + python-amis 构建所有 schema
- AMIS SDK 从 CDN 加载，不占用服务器带宽
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入新的路由注册函数
from web2.app import create_fastapi_app, register_amis_routes

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(reload: bool = False) -> FastAPI:
    """
    创建 FastAPI 应用
    
    Args:
        reload: 开发模式下每次请求重新构建 schema
    """
    app = FastAPI(title="Agnes Web2", version="2.0.0")
    
    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 静态文件目录（如果有的话）
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        from fastapi.staticfiles import StaticFiles
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # 预构建顶层 App 配置（带缓存）
    from web2.app_config import get_built_amis_app
    if not reload:
        logger.info("预构建顶层 Amis App 配置...")
        get_built_amis_app()
    
    # 注册所有 AMIS 路由
    # 因为 app.mount("/web2", web2_app)，所以实际 API 路径是 /web2/api/xxx
    # 路由结构：
    #   GET / -> HTML 入口（匹配 /web2/）
    #   GET /api/amis/schema -> 顶层 App 配置（实际路径 /web2/api/amis/schema）
    #   GET /api/pages/{page_name} -> 单个页面 schema（实际路径 /web2/api/pages/{page_name}）
    register_amis_routes(app, api_prefix="/api")
    
    logger.info("Web2 FastAPI 应用创建完成（异步按需加载模式）")
    return app


# 创建默认应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    # 开发模式运行
    app = create_app(reload=True)
    uvicorn.run(app, host="127.0.0.1", port=8080)
