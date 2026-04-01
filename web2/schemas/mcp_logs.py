"""
MCP 调用日志页面 schema
记录所有工具调用，方便调试和性能分析
直接使用字典构建
"""


def get_mcp_logs_schema() -> dict:
    """MCP调用日志页面 schema"""

    return {
        "type": "page",
        "title": "MCP 调用日志",
        "body": [
            {
                "type": "alert",
                "level": "info",
                "body": "这里记录了所有 MCP 工具调用的详细日志，包括请求参数、响应结果、耗时和 Token 消耗。可以帮助你分析性能损耗和调试问题。",
            },
            {
                "type": "crud",
                "title": "工具调用日志",
                "api": "/api/mcp/logs/list",
                "columns": [
                    {"name": "timestamp", "label": "时间", "sortable": True},
                    {"name": "server_name", "label": "服务器", "sortable": True},
                    {"name": "tool_name", "label": "工具", "sortable": True},
                    {"name": "duration_ms", "label": "耗时(ms)", "sortable": True},
                    {"name": "tokens_used", "label": "Token 消耗", "sortable": True},
                    {
                        "name": "success",
                        "label": "成功",
                        "type": "mapping",
                        "mapping": {
                            "True": {"label": "是", "type": "success"},
                            "False": {"label": "否", "type": "danger"},
                        },
                    },
                    {
                        "type": "button",
                        "label": "详情",
                        "level": "primary",
                        "actionType": "dialog",
                        "dialog": {
                            "title": "调用详情",
                            "body": {
                                "type": "form",
                                "body": [
                                    {
                                        "type": "static",
                                        "name": "server_name",
                                        "label": "服务器",
                                    },
                                    {
                                        "type": "static",
                                        "name": "tool_name",
                                        "label": "工具",
                                    },
                                    {
                                        "type": "json-editor",
                                        "name": "request_args",
                                        "label": "请求参数",
                                        "disabled": True,
                                    },
                                    {
                                        "type": "json-editor",
                                        "name": "response",
                                        "label": "响应结果",
                                        "disabled": True,
                                    },
                                    {
                                        "type": "static",
                                        "name": "duration_ms",
                                        "label": "耗时(ms)",
                                    },
                                    {
                                        "type": "static",
                                        "name": "tokens_used",
                                        "label": "Token 消耗",
                                    },
                                    {
                                        "type": "static",
                                        "name": "error_message",
                                        "label": "错误信息",
                                        "visibleOn": "data.success === false",
                                    },
                                ],
                            },
                        },
                    },
                ],
                "headerToolbar": [
                    "reload",
                    {
                        "type": "button",
                        "label": "清空日志",
                        "level": "danger",
                        "actionType": "ajax",
                        "api": "post:/api/mcp/logs/clear",
                        "feedback": "日志已清空",
                        "refresh": True,
                        "confirmText": "确定要清空所有日志吗？",
                    },
                ],
                "affixHeader": True,
            },
        ],
    }
