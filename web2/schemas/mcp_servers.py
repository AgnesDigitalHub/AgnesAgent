"""
MCP 服务器管理页面 schema
管理已安装的 MCP 服务器，配置开关/权限/作用域
"""


def get_mcp_servers_schema() -> dict:
    """MCP服务器管理页面 schema - 直接字典构建"""

    columns = [
        {"name": "name", "label": "名称", "sortable": True},
        {"name": "command", "label": "启动命令", "sortable": False},
        {
            "name": "enabled",
            "label": "已启用",
            "type": "switch",
            "quickEditEnabled": True,
        },
        {
            "name": "health",
            "label": "状态",
            "type": "mapping",
            "mapping": {
                "running": {"label": "运行中", "type": "success"},
                "stopped": {"label": "已停止", "type": "default"},
                "error": {"label": "启动失败", "type": "danger"},
                "timeout": {"label": "连接超时", "type": "warning"},
            },
        },
        {"name": "token_estimate", "label": "预估 Token", "sortable": True},
        {
            "type": "button",
            "label": "健康检查",
            "level": "success",
            "actionType": "ajax",
            "api": "get:/api/mcp/check-health/$id",
            "feedback": "健康检查完成",
            "refresh": True,
        },
        {
            "type": "button",
            "label": "编辑",
            "level": "primary",
            "actionType": "drawer",
            "drawer": {
                "title": "编辑服务器配置",
                "body": {
                    "type": "form",
                    "api": "put:/api/mcp/update/$id",
                    "body": [
                        {"type": "hidden", "name": "id"},
                        {
                            "type": "input-text",
                            "name": "name",
                            "label": "服务器名称",
                            "required": True,
                        },
                        {
                            "type": "input-text",
                            "name": "command",
                            "label": "启动命令",
                            "required": True,
                            "placeholder": "例如: npx @modelcontextprotocol/server-filesystem",
                        },
                        {
                            "type": "input-text",
                            "name": "description",
                            "label": "描述",
                            "placeholder": "服务器描述",
                        },
                        {
                            "type": "switch",
                            "name": "enabled",
                            "label": "启用",
                            "value": True,
                        },
                        {"type": "divider", "title": "安全配置"},
                        {
                            "type": "switch",
                            "name": "security.readonly",
                            "label": "只读模式",
                            "value": False,
                            "remark": "开启后禁止写操作，适合文件系统/数据库工具",
                        },
                        {
                            "type": "switch",
                            "name": "security.confirm_on_dangerous",
                            "label": "需要人工确认",
                            "value": True,
                            "remark": "高危操作需要用户确认后才执行",
                        },
                        {
                            "type": "input-array",
                            "name": "security.allowed_paths",
                            "label": "允许访问路径",
                            "placeholder": "例如: /home/you/Documents/AgnesAgent",
                            "remark": "仅允许访问这些目录，不填则不限制（需要服务器端支持）",
                        },
                        {
                            "type": "input-array",
                            "name": "security.allowed_domains",
                            "label": "允许访问域名",
                            "placeholder": "例如: api.github.com",
                            "remark": "仅允许访问这些域名，不填则不限制",
                        },
                        {
                            "type": "input-number",
                            "name": "token_estimate",
                            "label": "预估 Token 消耗",
                            "value": 500,
                            "remark": "开启此工具会增加这么多 System Prompt tokens",
                        },
                        {
                            "type": "json-editor",
                            "name": "env",
                            "label": "环境变量",
                            "placeholder": "{}",
                            "remark": "JSON格式，会注入到MCP进程中",
                        },
                    ],
                },
            },
        },
        {
            "type": "button",
            "label": "测试连接",
            "level": "info",
            "actionType": "ajax",
            "api": "post:/api/mcp/test/$id",
            "feedback": "测试完成",
            "refresh": True,
        },
    ]

    return {
        "type": "page",
        "title": "MCP 服务器管理",
        "body": [
            {
                "type": "alert",
                "level": "info",
                "body": "在这里管理已安装的 MCP 服务器，可以启用/禁用、配置权限、查看运行状态。健康检查会自动检测服务器是否正常运行。",
            },
            {
                "type": "crud",
                "title": "MCP 服务器管理",
                "api": "/api/mcp/list",
                "addApi": "/api/mcp/create",
                "updateApi": "/api/mcp/update/$id",
                "deleteApi": "/api/mcp/delete/$id",
                "columns": columns,
                "perPage": 10,
                "headerToolbar": ["add", "reload"],
            },
        ],
    }
