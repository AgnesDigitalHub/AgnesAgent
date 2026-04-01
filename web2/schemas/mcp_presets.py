"""
MCP 预设模板页面 schema
场景化预设组合，支持导出分享
"""


def get_mcp_presets_schema() -> dict:
    """MCP预设模板页面 schema - 直接字典构建"""

    columns = [
        {"name": "name", "label": "预设名称", "sortable": True},
        {"name": "description", "label": "描述", "sortable": False},
        {"name": "category", "label": "场景分类", "sortable": True},
        {"name": "server_count", "label": "服务器数量", "sortable": True},
        {
            "type": "button",
            "label": "应用",
            "level": "primary",
            "actionType": "ajax",
            "api": "post:/api/mcp/presets/apply?id=$id",
            "feedback": "预设已应用",
        },
        {
            "type": "button",
            "label": "导出",
            "level": "default",
            "actionType": "download",
            "url": "/api/mcp/presets/export?id=$id",
            "fileName": "${name}.json",
        },
    ]

    return {
        "type": "page",
        "title": "MCP 预设模板",
        "body": [
            {
                "type": "alert",
                "level": "info",
                "body": "预设模板让你一键配置常用场景，比如「代码开发助手」会自动开启 Git、Terminal、Filesystem 等工具。你也可以把自己的配置导出分享给他人使用。",
            },
            {
                "type": "crud",
                "title": "预设模板",
                "api": "/api/mcp/presets/list",
                "addApi": "/api/mcp/presets/create",
                "updateApi": "/api/mcp/presets/update",
                "deleteApi": "/api/mcp/presets/delete",
                "columns": columns,
                "perPage": 10,
                "headerToolbar": [
                    "add",
                    "reload",
                    {
                        "type": "button",
                        "label": "导入预设",
                        "level": "success",
                        "actionType": "dialog",
                        "dialog": {
                            "title": "导入预设",
                            "body": {
                                "type": "form",
                                "api": "post:/api/mcp/presets/import",
                                "body": [
                                    {
                                        "type": "textarea",
                                        "name": "json_data",
                                        "label": "JSON 配置",
                                        "required": True,
                                        "placeholder": "粘贴导出的 JSON 配置",
                                    }
                                ],
                                "redirect": "/mcp/presets",
                            },
                        },
                    },
                ],
            },
        ],
    }
