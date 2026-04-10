"""
MCP 市场页面 Schema - 用户友好的MCP管理
提供预置MCP列表，一键安装，简化配置流程
"""

import json
from pathlib import Path

from agnes.utils.logger import get_logger

logger = get_logger("agnes.schemas")


def _load_mcp_market():
    """从JSON文件加载MCP市场数据"""
    market_file = Path(__file__).parent.parent.parent / "config" / "mcp" / "market.json"
    try:
        with open(market_file, encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"[MCP] 成功加载市场数据: {len(data)} 条记录")
            return data
    except Exception as e:
        logger.error(f"[MCP] 加载MCP市场数据失败: {e}")
        logger.error(f"[MCP] 尝试加载的文件路径: {market_file}")
        return []


MCP_MARKET = _load_mcp_market()

# 预置预设模板
MCP_PRESETS = [
    {
        "id": "code-assistant",
        "name": "代码助手",
        "description": "适合软件开发，包含文件系统、Git、终端访问",
        "category": "开发",
        "mcps": [
            "filesystem",
            "git",
            "terminal",
        ],
    },
    {
        "id": "research-assistant",
        "name": "学术研究助手",
        "description": "适合文献搜索和学术研究",
        "category": "学术",
        "mcps": [
            "arxiv",
            "brave-search",
            "memory",
        ],
    },
    {
        "id": "web-dev",
        "name": "Web 开发",
        "description": "适合网页开发和调试",
        "category": "开发",
        "mcps": [
            "filesystem",
            "git",
            "terminal",
            "brave-search",
        ],
    },
    {
        "id": "data-analysis",
        "name": "数据分析",
        "description": "适合数据处理和分析",
        "category": "数据",
        "mcps": [
            "filesystem",
            "postgres",
            "snowflake",
            "bigquery",
        ],
    },
    {
        "id": "full-stack",
        "name": "全栈开发",
        "description": "完整的全栈开发工具集",
        "category": "开发",
        "mcps": [
            "filesystem",
            "git",
            "terminal",
            "brave-search",
            "postgres",
            "redis",
        ],
    },
]


def get_mcp_schema():
    """生成完整的MCP管理页面Schema"""
    from .mcp_parts import (
        _dependency_install_section,
        _export_import_section,
        _installed_servers_section,
        _market_gallery_section,
        _presets_section,
        _secret_manager_section,
    )

    schema = {
        "title": "MCP 工具市场",
        "subTitle": "一键安装和管理 Model Context Protocol 服务器",
        "body": [
            _market_gallery_section(),
            {"type": "divider"},
            _installed_servers_section(),
            {"type": "divider"},
            _dependency_install_section(),
            {"type": "divider"},
            _secret_manager_section(),
            {"type": "divider"},
            _presets_section(),
            {"type": "divider"},
            _export_import_section(),
        ],
    }
    return schema
