"""
设置页面 schema
直接使用字典构建
"""


def get_settings_schema() -> dict:
    """获取设置页面 amis Schema"""
    return {
        "type": "page",
        "title": "系统设置",
        "body": [
            {
                "type": "form",
                "api": "/api/settings/save",
                "initApi": "/api/settings/get",
                "body": [
                    {
                        "type": "tpl",
                        "tpl": "<div class='m-b-xl'><h3>基本设置</h3></div>",
                    },
                    {
                        "type": "input-text",
                        "name": "site_name",
                        "label": "网站名称",
                        "value": "Agents Dashboard",
                    },
                    {
                        "type": "input-text",
                        "name": "site_description",
                        "label": "网站描述",
                    },
                    {
                        "type": "textarea",
                        "name": "site_intro",
                        "label": "网站介绍",
                    },
                    {
                        "type": "tpl",
                        "tpl": "<div class='m-t-xl m-b-xl'><h3>LLM 设置</h3></div>",
                    },
                    {
                        "type": "input-text",
                        "name": "openai_api_key",
                        "label": "OpenAI API Key",
                        "inputType": "password",
                    },
                    {
                        "type": "input-text",
                        "name": "openai_base_url",
                        "label": "OpenAI Base URL",
                    },
                    {
                        "type": "input-number",
                        "name": "max_tokens",
                        "label": "最大 Token 数",
                        "value": 4096,
                        "min": 1024,
                        "max": 16384,
                    },
                    {
                        "type": "tpl",
                        "tpl": "<div class='m-t-xl m-b-xl'><h3>功能开关</h3></div>",
                    },
                    {
                        "type": "switch",
                        "name": "enable_registration",
                        "label": "允许注册",
                        "value": True,
                    },
                    {
                        "type": "switch",
                        "name": "enable_analytics",
                        "label": "启用统计",
                        "value": False,
                    },
                    {
                        "type": "switch",
                        "name": "debug_mode",
                        "label": "调试模式",
                        "value": False,
                    },
                    {
                        "type": "button",
                        "actionType": "submit",
                        "label": "保存设置",
                        "level": "primary",
                    },
                ],
            }
        ],
    }
