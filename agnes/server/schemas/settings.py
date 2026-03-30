"""
系统设置页面 Schema
"""


def get_settings_schema():
    """获取系统设置页面 amis Schema"""
    return {
        "type": "page",
        "title": "系统设置",
        "body": [
            {
                "type": "service",
                "api": {
                    "method": "get",
                    "url": "/api/profiles",
                },
                "body": [
                    {
                        "type": "card",
                        "title": "全局设置",
                        "body": [
                            {
                                "type": "form",
                                "initApi": {
                                    "method": "get",
                                    "url": "/api/settings/llm",
                                },
                                "api": {
                                    "method": "put",
                                    "url": "/api/settings/llm",
                                },
                                "messages": {"success": "保存成功", "failed": "保存失败"},
                                "body": [
                                    {
                                        "type": "select",
                                        "name": "default_profile_id",
                                        "label": "默认 LLM 模型",
                                        "description": "选择系统默认使用的模型配置",
                                        "required": False,
                                        "clearable": True,
                                        "options": "${profiles.map(p => ({label: p.name + ' (' + p.provider + ')', value: p.id}))}",
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    }
