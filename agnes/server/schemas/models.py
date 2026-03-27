"""
模型管理页面 Schema
"""


def get_models_schema():
    """获取模型管理页面 amis Schema"""
    return {
        "type": "page",
        "title": "模型管理",
        "body": [
            {
                "type": "crud",
                "api": {
                    "method": "get",
                    "url": "/api/profiles",
                    "responseData": {"items": "${profiles}", "total": "${profiles.length}"},
                },
                "perPage": 10,
                "headerToolbar": [
                    "reload",
                    {
                        "type": "button",
                        "label": "新增配置",
                        "level": "primary",
                        "actionType": "dialog",
                        "dialog": {
                            "title": "新增模型配置",
                            "body": {
                                "type": "form",
                                "api": "post:/api/profiles",
                                "body": [
                                    {
                                        "type": "input-text",
                                        "name": "name",
                                        "label": "名称",
                                        "required": True,
                                    },
                                    {"type": "input-text", "name": "description", "label": "描述"},
                                    {
                                        "type": "select",
                                        "name": "provider",
                                        "label": "Provider",
                                        "required": True,
                                        "options": [
                                            {"label": "OpenAI", "value": "openai"},
                                            {"label": "Ollama", "value": "ollama"},
                                            {
                                                "label": "OpenVINO Server",
                                                "value": "openvino-server",
                                            },
                                            {
                                                "label": "其他本地模型",
                                                "value": "local-api",
                                            },
                                        ],
                                    },
                                    {
                                        "type": "input-text",
                                        "name": "model",
                                        "label": "Model",
                                        "required": True,
                                    },
                                    {"type": "input-text", "name": "base_url", "label": "Base URL"},
                                    {
                                        "type": "input-password",
                                        "name": "api_key",
                                        "label": "API Key",
                                    },
                                    {
                                        "type": "input-number",
                                        "name": "temperature",
                                        "label": "Temperature",
                                        "value": 0.7,
                                        "min": 0,
                                        "max": 2,
                                        "step": 0.1,
                                    },
                                    {
                                        "type": "input-number",
                                        "name": "max_tokens",
                                        "label": "Max Tokens",
                                    },
                                ],
                            },
                        },
                    },
                ],
                "columns": [
                    {"name": "name", "label": "名称", "type": "text"},
                    {"name": "provider", "label": "Provider", "type": "tag"},
                    {"name": "model", "label": "Model", "type": "text"},
                    {
                        "name": "is_active",
                        "label": "状态",
                        "type": "mapping",
                        "map": {
                            True: {"label": "激活中", "level": "success"},
                            False: {"label": "未激活", "level": "info"},
                        },
                    },
                    {"name": "updated_at", "label": "更新时间", "type": "datetime"},
                ],
                "itemActions": [
                    {
                        "type": "button",
                        "label": "激活",
                        "level": "success",
                        "actionType": "ajax",
                        "api": "post:/api/profiles/${id}/activate",
                        "visibleOn": "!data.is_active",
                    },
                    {
                        "type": "button",
                        "label": "编辑",
                        "level": "info",
                        "actionType": "dialog",
                        "dialog": {
                            "title": "编辑配置",
                            "body": {
                                "type": "form",
                                "api": "put:/api/profiles/${id}",
                                "initApi": "get:/api/profiles/${id}",
                                "body": [
                                    {
                                        "type": "input-text",
                                        "name": "name",
                                        "label": "名称",
                                        "required": True,
                                    },
                                    {"type": "input-text", "name": "description", "label": "描述"},
                                    {
                                        "type": "select",
                                        "name": "provider",
                                        "label": "Provider",
                                        "required": True,
                                        "options": [
                                            {"label": "OpenAI", "value": "openai"},
                                            {"label": "Ollama", "value": "ollama"},
                                            {
                                                "label": "OpenVINO Server",
                                                "value": "openvino-server",
                                            },
                                            {
                                                "label": "其他本地模型",
                                                "value": "local-api",
                                            },
                                        ],
                                    },
                                    {
                                        "type": "input-text",
                                        "name": "model",
                                        "label": "Model",
                                        "required": True,
                                    },
                                    {"type": "input-text", "name": "base_url", "label": "Base URL"},
                                    {
                                        "type": "input-password",
                                        "name": "api_key",
                                        "label": "API Key",
                                    },
                                    {
                                        "type": "input-number",
                                        "name": "temperature",
                                        "label": "Temperature",
                                        "min": 0,
                                        "max": 2,
                                        "step": 0.1,
                                    },
                                    {
                                        "type": "input-number",
                                        "name": "max_tokens",
                                        "label": "Max Tokens",
                                    },
                                ],
                            },
                        },
                    },
                    {
                        "type": "button",
                        "label": "删除",
                        "level": "danger",
                        "actionType": "ajax",
                        "confirmText": "确定要删除此配置吗？",
                        "api": "delete:/api/profiles/${id}",
                    },
                ],
            },
        ],
    }
