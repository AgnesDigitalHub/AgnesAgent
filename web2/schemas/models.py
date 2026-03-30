"""
模型管理页面 Schema - 重新设计版本
"""


def get_models_schema():
    """获取模型管理页面 amis Schema"""

    # 主流 AI 供应商列表
    provider_options = [
        {"label": "OpenAI", "value": "openai"},
        {"label": "OpenAI 兼容（Azure / 第三方代理）", "value": "openai-compat"},
        {"label": "DeepSeek", "value": "deepseek"},
        {"label": "Google Gemini", "value": "gemini"},
        {"label": "Anthropic Claude", "value": "anthropic"},
        {"label": "Ollama", "value": "ollama"},
        {"label": "OpenVINO Server", "value": "openvino-server"},
        {"label": "其他（通用 API）", "value": "generic"},
    ]

    return {
        "type": "page",
        "title": "模型管理",
        "body": [
            # ============================================
            # 1. Service 保存选中状态
            # ============================================
            {
                "type": "service",
                "name": "modelSelection",
                "data": {"selectedId": "", "selectedProfile": None},
            },
            {
                "type": "tpl",
                "tpl": "<h2>模型管理</h2><p style='color: #666; margin-bottom: 16px;'>管理你的 AI 供应商和模型配置</p>",
            },
            # ============================================
            # 2. 上半部分：供应商卡片列表
            # ============================================
            {
                "type": "crud",
                "api": {
                    "method": "get",
                    "url": "/api/profiles",
                    "responseData": {"items": "${profiles}", "total": "${profiles.length}"},
                },
                "perPage": 12,
                "mode": "cards",
                "headerToolbar": [
                    "reload",
                    {
                        "type": "button",
                        "label": "新增供应商",
                        "level": "primary",
                        "actionType": "dialog",
                        "dialog": {
                            "title": "新增供应商配置",
                            "size": "md",
                            "body": {
                                "type": "form",
                                "api": "post:/api/profiles",
                                "redirectText": "创建成功",
                                "messages": {"success": "创建成功", "failed": "创建失败"},
                                "body": [
                                    {
                                        "type": "select",
                                        "name": "provider",
                                        "label": "AI 供应商",
                                        "required": True,
                                        "options": provider_options,
                                        "description": "选择供应商类型",
                                    },
                                    {
                                        "type": "input-text",
                                        "name": "name",
                                        "label": "配置名称",
                                        "required": True,
                                        "placeholder": "例如: My OpenAI",
                                    },
                                    {
                                        "type": "input-text",
                                        "name": "description",
                                        "label": "描述",
                                        "placeholder": "可选描述",
                                    },
                                    {
                                        "type": "input-text",
                                        "name": "base_url",
                                        "label": "API Base URL",
                                        "placeholder": "例如: https://api.openai.com/v1",
                                    },
                                    {
                                        "type": "input-password",
                                        "name": "api_key",
                                        "label": "API Key",
                                        "placeholder": "输入你的 API Key",
                                    },
                                    {
                                        "type": "hidden",
                                        "name": "model",
                                        "value": "",
                                    },
                                    {
                                        "type": "hidden",
                                        "name": "temperature",
                                        "value": 0.7,
                                    },
                                    {
                                        "type": "hidden",
                                        "name": "max_tokens",
                                        "value": None,
                                    },
                                ],
                                "watch": {
                                    "provider": {
                                        "actions": [
                                            {
                                                "actionType": "setValue",
                                                "componentId": "add_base_url",
                                                "args": {
                                                    "value": "${IF(provider == 'openai', 'https://api.openai.com/v1', provider == 'deepseek', 'https://api.deepseek.com', provider == 'gemini', 'https://generativelanguage.googleapis.com/v1beta', provider == 'anthropic', 'https://api.anthropic.com', provider == 'ollama', 'http://localhost:11434/v1', provider == 'openvino-server', 'http://localhost:8000/v1', '')}"
                                                },
                                            },
                                        ]
                                    }
                                },
                            },
                        },
                    },
                ],
                "card": {
                    "title": "${name}",
                    "subTitle": "${IF(provider == 'openai', 'OpenAI', provider == 'openai-compat', 'OpenAI 兼容', provider == 'deepseek', 'DeepSeek', provider == 'gemini', 'Google Gemini', provider == 'anthropic', 'Anthropic Claude', provider == 'ollama', 'Ollama', provider == 'openvino-server', 'OpenVINO Server', '其他 API')}",
                    "body": {
                        "type": "tpl",
                        "tpl": '<div style="display: flex; flex-direction: column; gap: 4px;"><div style="color: #666; font-size: 13px; font-weight: 500;">模型: ${model || "未配置"}</div><div style="color: #999; font-size: 12px;">${description || "无描述"}</div><div style="display: flex; gap: 8px; margin-top: 8px;"><span style="${is_active ? "background: #4caf50; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;" : "display: none;"}">激活中</span></div></div>',
                    },
                    "actions": [
                        {
                            "type": "button",
                            "label": "编辑",
                            "level": "info",
                            "size": "sm",
                            "actionType": "dialog",
                            "dialog": {
                                "title": "编辑供应商配置",
                                "size": "md",
                                "body": {
                                    "type": "form",
                                    "api": "put:/api/profiles/${id}",
                                    "initApi": "get:/api/profiles/${id}",
                                    "messages": {"success": "保存成功", "failed": "保存失败"},
                                    "body": [
                                        {
                                            "type": "select",
                                            "name": "provider",
                                            "label": "AI 供应商",
                                            "required": True,
                                            "options": provider_options,
                                        },
                                        {
                                            "type": "input-text",
                                            "name": "name",
                                            "label": "配置名称",
                                            "required": True,
                                        },
                                        {
                                            "type": "input-text",
                                            "name": "description",
                                            "label": "描述",
                                        },
                                        {
                                            "type": "input-text",
                                            "name": "base_url",
                                            "label": "API Base URL",
                                        },
                                        {
                                            "type": "input-password",
                                            "name": "api_key",
                                            "label": "API Key",
                                        },
                                        {
                                            "type": "input-text",
                                            "name": "model",
                                            "label": "模型 ID",
                                            "required": True,
                                            "placeholder": "例如: gpt-4o, llama3, deepseek-chat",
                                            "description": "输入要使用的模型名称",
                                        },
                                    ],
                                },
                            },
                        },
                        {
                            "type": "button",
                            "label": "删除",
                            "level": "danger",
                            "size": "sm",
                            "confirmText": "确定要删除此配置吗？",
                            "actionType": "ajax",
                            "api": "delete:/api/profiles/${id}",
                        },
                        {
                            "type": "button",
                            "label": "激活",
                            "level": "success",
                            "size": "sm",
                            "visibleOn": "!is_active",
                            "actionType": "ajax",
                            "api": "post:/api/profiles/${id}/activate",
                        },
                        {
                            "type": "button",
                            "label": "取消激活",
                            "level": "default",
                            "size": "sm",
                            "visibleOn": "is_active",
                            "actionType": "ajax",
                            "api": "post:/api/profiles/deactivate",
                        },
                    ],
                    "onEvent": {
                        "click": {
                            "actions": [
                                {
                                    "actionType": "setValue",
                                    "componentName": "modelSelection",
                                    "args": {"selectedId": "${id}"},
                                },
                                {
                                    "actionType": "setValue",
                                    "componentName": "modelSelection",
                                    "args": {"selectedProfile": "${this}"},
                                },
                                {
                                    "actionType": "refresh",
                                    "componentName": "detailPanel",
                                },
                            ]
                        }
                    },
                },
            },
            # ============================================
            # 3. 下半部分：配置详情面板（用间隔线分开）
            # ============================================
            {
                "type": "service",
                "name": "detailPanel",
                "dataSource": "${modelSelection}",
                "body": [
                    # 详情面板（有选中时显示）
                    {
                        "type": "wrapper",
                        "visibleOn": "selectedId",
                        "body": [
                            {"type": "divider", "lineStyle": "solid"},
                            {"type": "heading", "text": "配置详情", "level": 3},
                            {
                                "type": "form",
                                "api": "put:/api/profiles/${selectedId}",
                                "initApi": "get:/api/profiles/${selectedId}",
                                "submitText": "保存配置",
                                "messages": {"success": "保存成功", "failed": "保存失败"},
                                "body": [
                                    {
                                        "type": "group",
                                        "label": "基础配置",
                                        "body": [
                                            {
                                                "type": "select",
                                                "name": "provider",
                                                "label": "AI 供应商",
                                                "required": True,
                                                "options": provider_options,
                                            },
                                            {
                                                "type": "input-text",
                                                "name": "name",
                                                "label": "配置名称",
                                                "required": True,
                                                "description": "用于识别此配置的唯一名称",
                                            },
                                            {
                                                "type": "input-text",
                                                "name": "description",
                                                "label": "描述",
                                            },
                                        ],
                                    },
                                    {
                                        "type": "group",
                                        "label": "连接配置",
                                        "body": [
                                            {
                                                "type": "input-text",
                                                "name": "base_url",
                                                "label": "API Base URL",
                                                "description": "API 服务器地址",
                                            },
                                            {
                                                "type": "input-password",
                                                "name": "api_key",
                                                "label": "API Key",
                                                "description": "API 密钥（可选）",
                                                "visibleOn": "provider !== 'ollama' && provider !== 'openvino-server'",
                                            },
                                        ],
                                    },
                                    {
                                        "type": "group",
                                        "label": "模型选择",
                                        "body": [
                                            {
                                                "type": "input-text",
                                                "name": "model",
                                                "label": "当前模型 ID",
                                                "required": True,
                                                "placeholder": "例如: gpt-4o, llama3, deepseek-chat",
                                                "description": "输入要使用的模型名称",
                                            },
                                            {
                                                "type": "html",
                                                "html": '<p style="color: #666; margin-bottom: 10px; margin-top: 10px;">管理可用模型列表（可选）</p>',
                                            },
                                            {
                                                "type": "button",
                                                "label": "从 API 获取模型列表",
                                                "level": "primary",
                                                "size": "sm",
                                                "actionType": "ajax",
                                                "api": {
                                                    "method": "post",
                                                    "url": "/api/profiles/fetch-models",
                                                    "data": {
                                                        "provider": "${provider}",
                                                        "base_url": "${base_url}",
                                                        "api_key": "${api_key}",
                                                    },
                                                },
                                                "onEvent": {
                                                    "success": {
                                                        "actions": [
                                                            {
                                                                "actionType": "setValue",
                                                                "componentId": "model_select",
                                                                "args": {"options": "${event.data.models}"},
                                                            }
                                                        ]
                                                    }
                                                },
                                            },
                                            {
                                                "type": "select",
                                                "name": "enabled_models",
                                                "id": "model_select",
                                                "label": "可用模型列表",
                                                "multiple": True,
                                                "creatable": True,
                                                "searchable": True,
                                                "clearable": True,
                                                "placeholder": "选择或输入模型 ID",
                                                "description": "可从列表选择，也可手动输入自定义模型 ID",
                                                "options": [],
                                            },
                                        ],
                                    },
                                    {
                                        "type": "group",
                                        "label": "高级配置",
                                        "body": [
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
                                                "description": "单位：K (1000 tokens)",
                                            },
                                        ],
                                    },
                                ],
                            },
                        ],
                    },
                    # 空状态提示（无选中时显示）
                    {
                        "type": "wrapper",
                        "visibleOn": "!selectedId",
                        "body": [
                            {"type": "divider", "lineStyle": "solid"},
                            {
                                "type": "alert",
                                "level": "info",
                                "body": "请点击上方的供应商卡片来查看和编辑配置详情",
                            },
                        ],
                    },
                ],
            },
        ],
    }
