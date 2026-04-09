"""
知识库管理页面 Schema - 完整 CRUD 版本
支持文档管理、搜索、分类标签等功能
"""


def get_knowledge_schema() -> dict:
    """获取知识库页面 amis Schema"""

    return {
        "type": "page",
        "title": "知识库管理",
        "body": [
            {
                "type": "crud",
                "api": {
                    "method": "get",
                    "url": "/api/knowledge/list",
                    "responseData": {"items": "${items}", "total": "$total"},
                },
                "perPage": 12,
                "headerToolbar": [
                    "reload",
                    {
                        "type": "button",
                        "label": "新建条目",
                        "level": "primary",
                        "actionType": "dialog",
                        "dialog": {
                            "title": "新建知识库条目",
                            "body": {
                                "type": "form",
                                "api": "/api/knowledge/create",
                                "body": [
                                    {"type": "input-text", "name": "title", "label": "标题", "required": True},
                                    {
                                        "type": "textarea",
                                        "name": "content",
                                        "label": "内容",
                                        "required": True,
                                        "rows": 6,
                                    },
                                    {"type": "input-text", "name": "category", "label": "分类"},
                                    {
                                        "type": "input-tag",
                                        "name": "tags",
                                        "label": "标签",
                                        "placeholder": "输入标签后回车",
                                    },
                                    {"type": "switch", "name": "enabled", "label": "启用", "value": True},
                                ],
                            },
                        },
                    },
                    {
                        "type": "button",
                        "label": "搜索",
                        "level": "info",
                        "actionType": "dialog",
                        "dialog": {
                            "title": "搜索知识库",
                            "body": {
                                "type": "form",
                                "api": "/api/knowledge/search",
                                "body": [
                                    {"type": "input-text", "name": "query", "label": "搜索关键词", "required": True}
                                ],
                            },
                        },
                    },
                ],
                "mode": "cards",
                "card": {
                    "title": "${title}",
                    "subTitle": "${category || '未分类'} · ${enabled ? '启用' : '禁用'}",
                    "body": [
                        {
                            "type": "tpl",
                            "tpl": "<div style=\"color: #999; font-size: 13px; margin: 8px 0; max-height: 60px; overflow: hidden; text-overflow: ellipsis;\">${content || '无内容'}</div>",
                        },
                        {
                            "type": "flex",
                            "className": "flex justify-between items-center mt-4",
                            "items": [
                                {
                                    "type": "tag",
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
                                                "title": "编辑知识库条目",
                                                "body": {
                                                    "type": "form",
                                                    "api": "put:/api/knowledge/save/${id}",
                                                    "initApi": "get:/api/knowledge/get/${id}",
                                                    "body": [
                                                        {
                                                            "type": "input-text",
                                                            "name": "title",
                                                            "label": "标题",
                                                            "required": True,
                                                        },
                                                        {
                                                            "type": "textarea",
                                                            "name": "content",
                                                            "label": "内容",
                                                            "required": True,
                                                            "rows": 8,
                                                        },
                                                        {"type": "input-text", "name": "category", "label": "分类"},
                                                        {"type": "input-tag", "name": "tags", "label": "标签"},
                                                        {"type": "switch", "name": "enabled", "label": "启用"},
                                                    ],
                                                },
                                            },
                                        },
                                        {
                                            "type": "button",
                                            "label": "${enabled ? '禁用' : '启用'}",
                                            "level": "${enabled ? 'default' : 'success'}",
                                            "actionType": "ajax",
                                            "api": "put:/api/knowledge/save/${id}",
                                            "data": {"enabled": "${!enabled}"},
                                        },
                                        {
                                            "type": "button",
                                            "label": "删除",
                                            "level": "danger",
                                            "actionType": "ajax",
                                            "confirmText": "确定要删除这个条目吗？",
                                            "api": "delete:/api/knowledge/delete/${id}",
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
                        "api": "/api/knowledge/bulk-delete",
                        "confirmText": "确定要删除选中吗？",
                    }
                ],
            }
        ],
    }
