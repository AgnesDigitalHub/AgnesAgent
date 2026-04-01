"""
人格管理页面 Schema - 直接使用字典构建，不依赖 amis-python
"""


def get_personas_schema() -> dict:
    """获取人格管理页面 amis Schema"""
    return {
        "type": "page",
        "title": "人格管理",
        "body": [
            {
                "type": "crud",
                "api": {
                    "method": "get",
                    "url": "/api/personas",
                    "responseData": {"items": "${personas}", "total": "${personas.length}"},
                },
                "perPage": 12,
                "headerToolbar": [
                    "reload",
                    {
                        "type": "button",
                        "label": "新建 Agent",
                        "level": "primary",
                        "actionType": "dialog",
                        "dialog": {
                            "title": "新增 Agent (人格)",
                            "body": {
                                "type": "form",
                                "api": "post:/api/personas",
                                "body": [
                                    {"type": "input-text", "name": "full_name", "label": "全名", "required": True},
                                    {"type": "input-text", "name": "nickname", "label": "昵称"},
                                    {"type": "input-text", "name": "role", "label": "角色"},
                                    {
                                        "type": "textarea",
                                        "name": "personality",
                                        "label": "性格描述",
                                        "description": "描述这个AI人格的性格特点",
                                    },
                                    {
                                        "type": "textarea",
                                        "name": "scenario",
                                        "label": "场景设定",
                                        "description": "描述对话发生的场景",
                                    },
                                    {"type": "input-text", "name": "description", "label": "描述"},
                                    {
                                        "type": "select",
                                        "name": "llm_profile_id",
                                        "label": "绑定模型",
                                        "clearable": True,
                                        "placeholder": "使用全局激活模型",
                                        "sourceApi": "/api/profiles",
                                        "options": "${profiles.map(p => ({label: p.name, value: p.id}))}",
                                    },
                                    {
                                        "type": "switch",
                                        "name": "enabled",
                                        "label": "启用",
                                        "value": True,
                                        "description": "禁用后该Agent无法使用",
                                    },
                                    {
                                        "type": "switch",
                                        "name": "mcp_enabled",
                                        "label": "启用 MCP",
                                        "value": False,
                                        "description": "连接 MCP 服务器提供工具能力",
                                    },
                                    {
                                        "type": "checkboxes",
                                        "name": "mcp_servers",
                                        "label": "启用 MCP 服务器",
                                        "options": [
                                            {"label": "Github", "value": "github"},
                                            {"label": "Fetch", "value": "fetch"},
                                            {"label": "Filesystem", "value": "filesystem"},
                                            {"label": "Postgres", "value": "postgres"},
                                            {"label": "Brave Search", "value": "brave-search"},
                                        ],
                                        "visibleOn": "data.mcp_enabled == true",
                                    },
                                    {
                                        "type": "checkboxes",
                                        "name": "skills",
                                        "label": "启用技能工具",
                                        "options": [
                                            {"label": "网页搜索", "value": "web_search"},
                                            {"label": "网页抓取", "value": "web_fetch"},
                                            {"label": "文件读取", "value": "file_read"},
                                            {"label": "文件写入", "value": "file_write"},
                                            {"label": "代码执行", "value": "code_interpreter"},
                                            {"label": "命令行执行", "value": "shell_exec"},
                                        ],
                                    },
                                    {
                                        "type": "textarea",
                                        "name": "system_prompt",
                                        "label": "系统提示词",
                                        "required": True,
                                        "description": "原始系统提示词，会自动组合其他信息生成最终prompt",
                                    },
                                ],
                            },
                        },
                    },
                    {
                        "type": "group",
                        "label": "从模板创建",
                        "buttons": [
                            {
                                "type": "button",
                                "label": "通用助手",
                                "level": "light",
                                "size": "sm",
                                "actionType": "dialog",
                                "dialog": {
                                    "title": "创建通用助手",
                                    "body": {
                                        "type": "form",
                                        "api": "post:/api/personas",
                                        "body": [
                                            {
                                                "type": "input-text",
                                                "name": "full_name",
                                                "label": "全名",
                                                "value": "通用助手",
                                                "required": True,
                                            },
                                            {
                                                "type": "input-text",
                                                "name": "nickname",
                                                "label": "昵称",
                                                "value": "小通",
                                            },
                                            {
                                                "type": "input-text",
                                                "name": "role",
                                                "label": "角色",
                                                "value": "通用AI助手",
                                            },
                                            {
                                                "type": "textarea",
                                                "name": "personality",
                                                "label": "性格描述",
                                                "value": "友好、耐心、乐于助人，能够处理各种日常问题",
                                            },
                                            {
                                                "type": "textarea",
                                                "name": "scenario",
                                                "label": "场景设定",
                                                "value": "适用于各种通用场景，提供信息查询、建议和帮助",
                                            },
                                            {
                                                "type": "textarea",
                                                "name": "system_prompt",
                                                "label": "系统提示词",
                                                "value": "你是一个通用AI助手，名叫小通。你的任务是帮助用户解决各种问题，提供准确、有用的信息。请保持友好、耐心的态度，用简洁明了的语言回答问题。",
                                                "required": True,
                                            },
                                            {
                                                "type": "input-text",
                                                "name": "description",
                                                "label": "描述",
                                                "value": "一个全能型AI助手，适合日常使用",
                                            },
                                        ],
                                    },
                                },
                            },
                            {
                                "type": "button",
                                "label": "代码专家",
                                "level": "light",
                                "size": "sm",
                                "actionType": "dialog",
                                "dialog": {
                                    "title": "创建代码专家",
                                    "body": {
                                        "type": "form",
                                        "api": "post:/api/personas",
                                        "body": [
                                            {
                                                "type": "input-text",
                                                "name": "full_name",
                                                "label": "全名",
                                                "value": "代码专家",
                                                "required": True,
                                            },
                                            {
                                                "type": "input-text",
                                                "name": "nickname",
                                                "label": "昵称",
                                                "value": "码神",
                                            },
                                            {
                                                "type": "input-text",
                                                "name": "role",
                                                "label": "角色",
                                                "value": "高级软件工程师",
                                            },
                                            {
                                                "type": "textarea",
                                                "name": "personality",
                                                "label": "性格描述",
                                                "value": "严谨、专业、注重细节，热爱技术",
                                            },
                                            {
                                                "type": "textarea",
                                                "name": "scenario",
                                                "label": "场景设定",
                                                "value": "专注于代码开发、调试、架构设计等技术问题",
                                            },
                                            {
                                                "type": "textarea",
                                                "name": "system_prompt",
                                                "label": "系统提示词",
                                                "value": "你是一个资深的代码专家，名叫码神。你精通多种编程语言和开发框架，能够帮助用户编写高质量的代码、调试问题、优化性能。请提供清晰的代码示例和详细的技术解释。",
                                                "required": True,
                                            },
                                            {
                                                "type": "input-text",
                                                "name": "description",
                                                "label": "描述",
                                                "value": "专业的编程助手，适合开发者使用",
                                            },
                                        ],
                                    },
                                },
                            },
                            {
                                "type": "button",
                                "label": "写作助手",
                                "level": "light",
                                "size": "sm",
                                "actionType": "dialog",
                                "dialog": {
                                    "title": "创建写作助手",
                                    "body": {
                                        "type": "form",
                                        "api": "post:/api/personas",
                                        "body": [
                                            {
                                                "type": "input-text",
                                                "name": "full_name",
                                                "label": "全名",
                                                "value": "写作助手",
                                                "required": True,
                                            },
                                            {
                                                "type": "input-text",
                                                "name": "nickname",
                                                "label": "昵称",
                                                "value": "文笔",
                                            },
                                            {
                                                "type": "input-text",
                                                "name": "role",
                                                "label": "角色",
                                                "value": "专业写作顾问",
                                            },
                                            {
                                                "type": "textarea",
                                                "name": "personality",
                                                "label": "性格描述",
                                                "value": "富有创意、文采斐然、善于表达",
                                            },
                                            {
                                                "type": "textarea",
                                                "name": "scenario",
                                                "label": "场景设定",
                                                "value": "专注于文章写作、文案创作、内容优化",
                                            },
                                            {
                                                "type": "textarea",
                                                "name": "system_prompt",
                                                "label": "系统提示词",
                                                "value": "你是一个专业的写作助手，名叫文笔。你擅长各种文体的写作，包括文章、文案、报告等。请帮助用户提升文字表达能力，提供写作建议和修改意见。",
                                                "required": True,
                                            },
                                            {
                                                "type": "input-text",
                                                "name": "description",
                                                "label": "描述",
                                                "value": "专业的写作助手，提升文字质量",
                                            },
                                        ],
                                    },
                                },
                            },
                        ],
                    },
                ],
                "mode": "cards",
                "card": {
                    "title": "${full_name}",
                    "subTitle": "${role || '通用'}",
                    "body": [
                        {
                            "type": "tpl",
                            "tpl": "<div style=\"color: #666; font-size: 13px; margin: 8px 0;\">${description || (nickname ? nickname : '无描述')}</div>",
                        },
                        {
                            "type": "flex",
                            "className": "flex justify-between items-center mt-4",
                            "items": [
                                {
                                    "type": "badge",
                                    "label": "${enabled ? '启用' : '禁用'}",
                                    "level": "${enabled ? 'success' : 'default'}",
                                },
                                {
                                    "type": "badge",
                                    "label": "${is_active ? '激活中' : '未激活'}",
                                    "level": "${is_active ? 'primary' : 'info'}",
                                },
                                {
                                    "type": "group",
                                    "buttons": [
                                        {
                                            "type": "button",
                                            "label": "编辑",
                                            "level": "info",
                                            "actionType": "dialog",
                                            "dialog": {
                                                "title": "编辑人格",
                                                "body": {
                                                    "type": "form",
                                                    "api": "put:/api/personas/${id}",
                                                    "initApi": "get:/api/personas/${id}",
                                                    "body": [
                                                        {
                                                            "type": "input-text",
                                                            "name": "full_name",
                                                            "label": "全名",
                                                            "required": True,
                                                        },
                                                        {"type": "input-text", "name": "nickname", "label": "昵称"},
                                                        {"type": "input-text", "name": "role", "label": "角色"},
                                                        {
                                                            "type": "textarea",
                                                            "name": "personality",
                                                            "label": "性格描述",
                                                        },
                                                        {"type": "textarea", "name": "scenario", "label": "场景设定"},
                                                        {"type": "input-text", "name": "description", "label": "描述"},
                                                        {
                                                            "type": "select",
                                                            "name": "llm_profile_id",
                                                            "label": "绑定模型",
                                                            "clearable": True,
                                                            "placeholder": "使用全局激活模型",
                                                            "sourceApi": "/api/profiles",
                                                            "options": "${profiles.map(p => ({label: p.name, value: p.id}))}",
                                                        },
                                                        {
                                                            "type": "switch",
                                                            "name": "enabled",
                                                            "label": "启用",
                                                            "description": "禁用后该Agent无法使用",
                                                        },
                                                        {
                                                            "type": "switch",
                                                            "name": "mcp_enabled",
                                                            "label": "启用 MCP",
                                                            "description": "连接 MCP 服务器提供工具能力",
                                                        },
                                                        {
                                                            "type": "checkboxes",
                                                            "name": "mcp_servers",
                                                            "label": "启用 MCP 服务器",
                                                            "options": [
                                                                {"label": "Github", "value": "github"},
                                                                {"label": "Fetch", "value": "fetch"},
                                                                {"label": "Filesystem", "value": "filesystem"},
                                                                {"label": "Postgres", "value": "postgres"},
                                                                {"label": "Brave Search", "value": "brave-search"},
                                                            ],
                                                            "visibleOn": "data.mcp_enabled == true",
                                                        },
                                                        {
                                                            "type": "checkboxes",
                                                            "name": "skills",
                                                            "label": "启用技能工具",
                                                            "options": [
                                                                {"label": "网页搜索", "value": "web_search"},
                                                                {"label": "网页抓取", "value": "web_fetch"},
                                                                {"label": "文件读取", "value": "file_read"},
                                                                {"label": "文件写入", "value": "file_write"},
                                                                {"label": "代码执行", "value": "code_interpreter"},
                                                                {"label": "命令行执行", "value": "shell_exec"},
                                                            ],
                                                        },
                                                        {
                                                            "type": "textarea",
                                                            "name": "system_prompt",
                                                            "label": "系统提示词",
                                                            "required": True,
                                                        },
                                                    ],
                                                },
                                            },
                                        },
                                        {
                                            "type": "button",
                                            "label": "激活",
                                            "level": "success",
                                            "actionType": "ajax",
                                            "api": "post:/api/personas/${id}/activate",
                                            "visibleOn": "!data.is_active",
                                        },
                                        {
                                            "type": "button",
                                            "label": "删除",
                                            "level": "danger",
                                            "actionType": "ajax",
                                            "confirmText": "确定要删除此人格吗？",
                                            "api": "delete:/api/personas/${id}",
                                        },
                                    ],
                                },
                            ],
                        },
                    ],
                },
            }
        ],
    }
