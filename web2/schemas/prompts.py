"""
Prompt IDE 页面 Schema - Prompt 编辑、测试和管理
"""


def get_prompts_schema() -> dict:
    """获取 Prompt IDE 页面 amis Schema"""

    return {
        "type": "page",
        "title": "Prompt IDE",
        "body": [
            # 页面头部
            {
                "type": "flex",
                "justify": "space-between",
                "alignItems": "center",
                "className": "p-1",
                "items": [
                    {
                        "type": "tpl",
                        "tpl": "<div class='flex items-center gap-2'><span class='text-2xl'>💬</span><span class='text-xl font-bold'>Prompt IDE</span></div>",
                    },
                    {
                        "type": "button",
                        "label": "新建 Prompt",
                        "level": "primary",
                        "icon": "fa fa-plus",
                        "actionType": "dialog",
                        "dialog": {
                            "title": "新建 Prompt",
                            "size": "lg",
                            "body": {
                                "type": "form",
                                "api": "post:/api/prompts/create",
                                "body": [
                                    {
                                        "type": "input-text",
                                        "name": "name",
                                        "label": "名称",
                                        "required": True,
                                        "placeholder": "输入 Prompt 名称",
                                    },
                                    {
                                        "type": "textarea",
                                        "name": "description",
                                        "label": "描述",
                                        "placeholder": "简要描述这个 Prompt 的用途",
                                        "rows": 2,
                                    },
                                    {
                                        "type": "textarea",
                                        "name": "content",
                                        "label": "内容",
                                        "required": True,
                                        "placeholder": "输入 Prompt 内容，使用 {{variable}} 定义变量",
                                        "rows": 10,
                                        "className": "font-mono",
                                    },
                                    {
                                        "type": "input-tag",
                                        "name": "tags",
                                        "label": "标签",
                                        "placeholder": "添加标签，按回车确认",
                                        "clearable": True,
                                    },
                                ],
                            },
                            "actions": [
                                {
                                    "type": "button",
                                    "actionType": "submit",
                                    "label": "创建",
                                    "level": "primary",
                                },
                                {
                                    "type": "button",
                                    "actionType": "cancel",
                                    "label": "取消",
                                },
                            ],
                        },
                    },
                ],
            },
            # 搜索栏
            {
                "type": "form",
                "mode": "inline",
                "className": "m-b",
                "wrapWithPanel": False,
                "body": [
                    {
                        "type": "input-text",
                        "name": "keywords",
                        "placeholder": "搜索 Prompt...",
                        "addOn": {
                            "type": "button",
                            "icon": "fa fa-search",
                            "level": "primary",
                            "actionType": "submit",
                        },
                    },
                ],
                "api": "get:/api/prompts/search?q=${keywords}",
                "target": "prompts_crud",
            },
            # CRUD 表格
            {
                "type": "crud",
                "name": "prompts_crud",
                "api": "/api/prompts/list",
                "syncLocation": False,
                "headerToolbar": [
                    "bulk-actions",
                    {
                        "type": "button",
                        "label": "刷新",
                        "icon": "fa fa-refresh",
                        "actionType": "reload",
                        "target": "prompts_crud",
                    },
                ],
                "footerToolbar": ["statistics", "pagination"],
                "columns": [
                    {
                        "name": "name",
                        "label": "名称",
                        "type": "text",
                        "width": 200,
                    },
                    {
                        "name": "description",
                        "label": "描述",
                        "type": "text",
                        "width": 300,
                    },
                    {
                        "name": "tags",
                        "label": "标签",
                        "type": "each",
                        "items": {
                            "type": "tag",
                            "label": "${item}",
                            "className": "m-r-xs",
                        },
                        "width": 200,
                    },
                    {
                        "name": "variables",
                        "label": "变量",
                        "type": "each",
                        "items": {
                            "type": "code",
                            "value": "${item}",
                            "className": "text-xs m-r-xs",
                        },
                        "width": 150,
                    },
                    {
                        "name": "version",
                        "label": "版本",
                        "type": "text",
                        "width": 80,
                    },
                    {
                        "name": "updated_at",
                        "label": "更新时间",
                        "type": "date",
                        "format": "YYYY-MM-DD HH:mm",
                        "width": 150,
                    },
                    {
                        "type": "operation",
                        "label": "操作",
                        "width": 200,
                        "buttons": [
                            {
                                "type": "button",
                                "icon": "fa fa-play",
                                "level": "success",
                                "size": "sm",
                                "tooltip": "测试",
                                "actionType": "dialog",
                                "dialog": {
                                    "title": "测试 Prompt: ${name}",
                                    "size": "xl",
                                    "body": {
                                        "type": "form",
                                        "api": "post:/api/prompts/test",
                                        "body": [
                                            {
                                                "type": "hidden",
                                                "name": "content",
                                                "value": "${content}",
                                            },
                                            {
                                                "type": "tpl",
                                                "tpl": "<div class='mb-2'><strong>原始 Prompt:</strong></div><pre class='bg-gray-100 p-2 rounded text-sm'>${content}</pre>",
                                                "visibleOn": "!variables || variables.length === 0",
                                            },
                                            {
                                                "type": "tpl",
                                                "tpl": "<div class='mb-2'><strong>变量值:</strong></div>",
                                                "visibleOn": "variables && variables.length > 0",
                                            },
                                            {
                                                "type": "each",
                                                "name": "variables",
                                                "items": {
                                                    "type": "input-text",
                                                    "name": "variables.${item}",
                                                    "label": "${item}",
                                                    "placeholder": "输入 ${item} 的值",
                                                },
                                                "visibleOn": "variables && variables.length > 0",
                                            },
                                            {
                                                "type": "divider",
                                            },
                                            {
                                                "type": "button",
                                                "label": "运行测试",
                                                "level": "primary",
                                                "actionType": "submit",
                                                "block": True,
                                            },
                                            {
                                                "type": "divider",
                                                "visibleOn": "response",
                                            },
                                            {
                                                "type": "tpl",
                                                "tpl": "<div class='mb-2'><strong>渲染后的 Prompt:</strong></div><pre class='bg-blue-50 p-2 rounded text-sm'>${rendered_prompt}</pre>",
                                                "visibleOn": "rendered_prompt",
                                            },
                                            {
                                                "type": "tpl",
                                                "tpl": "<div class='mb-2'><strong>LLM 响应:</strong></div><div class='bg-green-50 p-3 rounded text-sm border border-green-200'>${response}</div>",
                                                "visibleOn": "response",
                                            },
                                            {
                                                "type": "tpl",
                                                "tpl": "<div class='text-red-500'><strong>错误:</strong> ${error}</div>",
                                                "visibleOn": "error",
                                            },
                                        ],
                                    },
                                },
                            },
                            {
                                "type": "button",
                                "icon": "fa fa-edit",
                                "level": "primary",
                                "size": "sm",
                                "tooltip": "编辑",
                                "actionType": "dialog",
                                "dialog": {
                                    "title": "编辑 Prompt",
                                    "size": "lg",
                                    "body": {
                                        "type": "form",
                                        "api": "put:/api/prompts/update/${id}",
                                        "initApi": "/api/prompts/get/${id}",
                                        "body": [
                                            {
                                                "type": "hidden",
                                                "name": "id",
                                            },
                                            {
                                                "type": "input-text",
                                                "name": "name",
                                                "label": "名称",
                                                "required": True,
                                            },
                                            {
                                                "type": "textarea",
                                                "name": "description",
                                                "label": "描述",
                                                "rows": 2,
                                            },
                                            {
                                                "type": "textarea",
                                                "name": "content",
                                                "label": "内容",
                                                "required": True,
                                                "rows": 12,
                                                "className": "font-mono",
                                            },
                                            {
                                                "type": "input-tag",
                                                "name": "tags",
                                                "label": "标签",
                                                "placeholder": "添加标签，按回车确认",
                                                "clearable": True,
                                            },
                                        ],
                                    },
                                },
                            },
                            {
                                "type": "button",
                                "icon": "fa fa-trash",
                                "level": "danger",
                                "size": "sm",
                                "tooltip": "删除",
                                "actionType": "ajax",
                                "confirmText": "确定要删除 Prompt \"${name}\" 吗？",
                                "api": "delete:/api/prompts/delete/${id}",
                            },
                        ],
                    },
                ],
                "bulkActions": [
                    {
                        "type": "button",
                        "label": "批量删除",
                        "level": "danger",
                        "actionType": "ajax",
                        "api": "post:/api/prompts/bulk-delete",
                        "confirmText": "确定要删除选中的 ${ids|raw|pick:length} 个 Prompt 吗？",
                    },
                ],
                "itemActions": [],
            },
            # 使用提示
            {
                "type": "card",
                "className": "mt-4",
                "body": {
                    "type": "tpl",
                    "tpl": """
                    <div class="text-sm text-gray-600">
                        <div class="font-bold mb-2">💡 使用提示:</div>
                        <ul class="list-disc pl-4 space-y-1">
                            <li>在 Prompt 内容中使用 <code>{{variable_name}}</code> 定义变量</li>
                            <li>测试时会自动提取变量并提示输入值</li>
                            <li>Prompt 会自动保存版本历史</li>
                            <li>可以使用标签对 Prompt 进行分类管理</li>
                        </ul>
                    </div>
                    """,
                },
            },
        ],
    }
