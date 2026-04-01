"""
MCP 密钥管理页面 schema
统一管理 API Key 和环境变量，支持多环境配置
"""


def get_mcp_secrets_schema() -> dict:
    """MCP密钥管理页面 schema - 直接字典构建"""

    return {
        "type": "page",
        "title": "MCP 密钥管理",
        "body": [
            {
                "type": "alert",
                "level": "info",
                "body": "在这里统一管理所有 MCP 需要的 API Key 和令牌。这些密钥会被加密存储，并在启动 MCP 进程时自动注入为环境变量。支持多环境配置切换。",
            },
            {
                "type": "crud",
                "title": "密钥配置",
                "api": "/api/mcp/secrets/list",
                "addApi": "/api/mcp/secrets/create",
                "updateApi": "/api/mcp/secrets/update",
                "deleteApi": "/api/mcp/secrets/delete",
                "columns": [
                    {"name": "key_name", "label": "Key 名称", "sortable": True},
                    {"name": "service_name", "label": "服务名称", "sortable": True},
                    {"name": "environment", "label": "环境", "sortable": True},
                    {"name": "description", "label": "描述", "sortable": False},
                ],
                "perPage": 10,
                "headerToolbar": ["add", "reload"],
            },
        ],
    }
