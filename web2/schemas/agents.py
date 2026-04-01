"""
Agent 管理页面 schema
直接使用字典构建，不依赖amis-python
"""


def get_agents_schema() -> dict:
    """Agent 管理页面 schema，直接字典构建"""

    return {
        "type": "page",
        "title": "Agent 管理",
        "body": [
            {
                "type": "crud",
                "api": {
                    "method": "get",
                    "url": "/api/agents/list",
                    "responseData": {"items": "${items}", "total": "$total"},
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
                            "title": "新建 Agent",
                            "body": {
                                "type": "form",
                                "api": "/api/agents/create",
                                "body": [
                                    {
                                        "type": "input-text",
                                        "name": "name",
                                        "label": "Agent 名称",
                                        "required": True,
                                    },
                                    {
                                        "type": "textarea",
                                        "name": "description",
                                        "label": "描述",
                                    },
                                    {
                                        "type": "switch",
                                        "name": "enabled",
                                        "label": "启用",
                                        "value": True,
                                    },
                                ],
                                "buttons": [{"type": "submit", "label": "创建", "primary": True}],
                            },
                        },
                    },
                ],
                "mode": "cards",
                "card": {
                    "title": "${name}",
                    "subTitle": "${enabled ? '启用' : '禁用'}",
                    "body": [
                        {
                            "type": "tpl",
                            "tpl": "<div style=\"color: #999; font-size: 13px; margin: 8px 0;\">${description || '无描述'}</div>",
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
                                    "type": "group",
                                    "buttons": [
                                        {
                                            "type": "button",
                                            "label": "编辑",
                                            "level": "info",
                                            "actionType": "dialog",
                                            "dialog": {
                                                "title": "编辑 Agent",
                                                "body": {
                                                    "type": "form",
                                                    "api": "put:/api/agents/save/${id}",
                                                    "initApi": "get:/api/agents/get/${id}",
                                                    "body": [
                                                        {
                                                            "type": "input-text",
                                                            "name": "name",
                                                            "label": "Agent 名称",
                                                            "required": True,
                                                        },
                                                        {
                                                            "type": "textarea",
                                                            "name": "description",
                                                            "label": "描述",
                                                        },
                                                        {
                                                            "type": "switch",
                                                            "name": "enabled",
                                                            "label": "启用",
                                                        },
                                                    ],
                                                },
                                            },
                                        },
                                        {
                                            "type": "button",
                                            "label": "${enabled ? '禁用' : '启用'}",
                                            "level": "${enabled ? 'default' : 'success'}",
                                            "actionType": "ajax",
                                            "api": "put:/api/agents/save/${id}",
                                            "data": {"enabled": "${!enabled}"},
                                        },
                                        {
                                            "type": "button",
                                            "label": "删除",
                                            "level": "danger",
                                            "actionType": "ajax",
                                            "confirmText": "确定要删除这个 Agent 吗？",
                                            "api": "delete:/api/agents/delete/${id}",
                                        },
                                    ],
                                },
                            ],
                        },
                    ],
                },
                "bulkActions": [
                    {
                        "label": "批量删除",
                        "type": "button",
                        "level": "danger",
                        "api": "/api/agents/bulk-delete",
                        "confirmText": "确定要删除选中吗？",
                    }
                ],
            }
        ],
    }
