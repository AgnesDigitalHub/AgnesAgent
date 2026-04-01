"""
MCP 工具市场页面 schema
浏览预置MCP列表，一键安装
直接使用字典构建，不依赖amis-python pydantic验证
"""

from web2.schemas.mcp import MCP_MARKET


def get_mcp_market_schema() -> dict:
    """MCP工具市场页面 schema"""

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

    return {
        "type": "page",
        "title": "MCP 工具市场",
        "body": [
            {
                "type": "alert",
                "level": "info",
                "body": "这里展示了社区推荐的常用 MCP 服务器，选择需要的工具一键安装。安装后请到「服务器管理」配置详细参数。",
            },
            {
                "type": "crud",
                "title": "MCP 工具市场",
                "api": {
                    "method": "get",
                    "url": "/api/mcp/market",
                    "responseData": {"items": "${items}", "total": "${items.length}"},
                },
                "columns": [
                    {"name": "name", "label": "名称", "sortable": False},
                    {"name": "description", "label": "描述", "sortable": False},
                    {"name": "category", "label": "分类", "sortable": False},
                    {"name": "author", "label": "作者", "sortable": False},
                    {
                        "type": "button",
                        "label": "安装",
                        "level": "primary",
                        "actionType": "dialog",
                        "dialog": {
                            "title": "安装 MCP",
                            "body": {
                                "type": "form",
                                "api": "post:/api/mcp/install",
                                "body": [
                                    {"type": "hidden", "name": "mcp_id"},
                                    {"type": "static", "name": "name", "label": "工具名称"},
                                    {"type": "static", "name": "description", "label": "描述"},
                                    {
                                        "type": "input-text",
                                        "name": "token",
                                        "label": "API Key / Token",
                                        "visibleOn": "data.needs_token",
                                        "placeholder": "请输入你的 API Key",
                                    },
                                    {
                                        "type": "input-text",
                                        "name": "path",
                                        "label": "允许访问路径",
                                        "visibleOn": "data.needs_path",
                                        "placeholder": "例如 /Users/xxx/project",
                                    },
                                ],
                                "redirect": "/mcp/servers",
                            },
                        },
                    },
                ],
                "headerToolbar": ["reload"],
                "perPage": 12,
            },
        ],
    }
