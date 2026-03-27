"""
Dashboard 页面 Schema
"""


def get_dashboard_schema():
    """获取 Dashboard 页面 amis Schema"""
    return {
        "type": "page",
        "title": "概览",
        "body": [
            {
                "type": "grid",
                "columns": [
                    {
                        "md": 3,
                        "body": {
                            "type": "card",
                            "body": [
                                {
                                    "type": "tpl",
                                    "tpl": "<div class='text-center'><div class='text-3xl font-bold text-primary'>📊</div><div class='text-xl font-bold mt-2'>${llm_provider || '未配置'}</div><div class='text-gray-500'>LLM Provider</div></div>",
                                }
                            ],
                        },
                    },
                    {
                        "md": 3,
                        "body": {
                            "type": "card",
                            "body": [
                                {
                                    "type": "tpl",
                                    "tpl": "<div class='text-center'><div class='text-3xl font-bold text-success'>🤖</div><div class='text-xl font-bold mt-2'>${llm_config.model || '-'}</div><div class='text-gray-500'>当前模型</div></div>",
                                }
                            ],
                        },
                    },
                    {
                        "md": 3,
                        "body": {
                            "type": "card",
                            "body": [
                                {
                                    "type": "tpl",
                                    "tpl": "<div class='text-center'><div class='text-3xl font-bold text-warning'>💬</div><div class='text-xl font-bold mt-2'>${history_length || 0}</div><div class='text-gray-500'>历史消息</div></div>",
                                }
                            ],
                        },
                    },
                    {
                        "md": 3,
                        "body": {
                            "type": "card",
                            "body": [
                                {
                                    "type": "tpl",
                                    "tpl": "<div class='text-center'><div class='text-3xl font-bold text-info'>🔌</div><div class='text-xl font-bold mt-2' id='status-text'>就绪</div><div class='text-gray-500'>系统状态</div></div>",
                                }
                            ],
                        },
                    },
                ],
            },
            {
                "type": "divider",
            },
            {
                "type": "tabs",
                "tabs": [
                    {
                        "title": "系统状态",
                        "body": [
                            {
                                "type": "service",
                                "api": "get:/api/status",
                                "interval": 3000,
                                "body": [
                                    {
                                        "type": "grid",
                                        "columns": [
                                            {
                                                "md": 6,
                                                "body": {
                                                    "type": "card",
                                                    "title": "LLM 配置",
                                                    "body": [
                                                        {
                                                            "type": "property",
                                                            "column": 1,
                                                            "items": [
                                                                {
                                                                    "label": "Provider",
                                                                    "content": "${llm_provider || '-'}",
                                                                    "remark": "语言模型提供商",
                                                                },
                                                                {
                                                                    "label": "Model",
                                                                    "content": "${llm_config.model || '-'}",
                                                                    "remark": "模型名称",
                                                                },
                                                                {
                                                                    "label": "Base URL",
                                                                    "content": "${llm_config.base_url || '-'}",
                                                                    "remark": "API 地址",
                                                                },
                                                                {
                                                                    "label": "Temperature",
                                                                    "content": "${llm_config.temperature || '-'}",
                                                                    "remark": "温度参数",
                                                                },
                                                            ],
                                                        },
                                                    ],
                                                },
                                            },
                                            {
                                                "md": 6,
                                                "body": {
                                                    "type": "card",
                                                    "title": "快捷操作",
                                                    "body": [
                                                        {
                                                            "type": "button-group",
                                                            "buttons": [
                                                                {
                                                                    "type": "button",
                                                                    "label": "配置模型",
                                                                    "level": "primary",
                                                                    "actionType": "link",
                                                                    "link": "/models",
                                                                },
                                                                {
                                                                    "type": "button",
                                                                    "label": "查看日志",
                                                                    "level": "default",
                                                                    "actionType": "link",
                                                                    "link": "/logs",
                                                                },
                                                                {
                                                                    "type": "button",
                                                                    "label": "API 文档",
                                                                    "level": "default",
                                                                    "actionType": "url",
                                                                    "url": "/docs",
                                                                    "blank": True,
                                                                },
                                                            ],
                                                        },
                                                    ],
                                                },
                                            },
                                        ],
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "title": "快速开始",
                        "body": [
                            {
                                "type": "alert",
                                "level": "info",
                                "body": "欢迎使用 Agnes Agent！首先在「模型管理」中配置您的 LLM，然后开始使用。",
                            },
                            {
                                "type": "steps",
                                "value": 1,
                                "steps": [
                                    {"title": "配置模型", "subTitle": "在模型管理中添加 LLM 配置"},
                                    {"title": "测试连接", "subTitle": "验证 API 是否正常工作"},
                                    {"title": "开始使用", "subTitle": "通过 API 或界面进行对话"},
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    }
