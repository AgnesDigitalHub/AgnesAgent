"""
MCP Schema 拆分部分 - 避免单个文件过大导致截断
"""


def _market_gallery_section():
    """MCP市场卡片画廊"""
    from .mcp import MCP_MARKET

    def _market_card(mcp):
        def _install_dialog(mcp):
            form_body = []
            if mcp.get("needs_token"):
                form_body.append(
                    {
                        "type": "input-text",
                        "name": "token",
                        "label": mcp["token_name"],
                        "required": True,
                        "description": mcp["token_help"],
                    }
                )
            if mcp.get("needs_path"):
                form_body.append(
                    {
                        "type": "input-text",
                        "name": "path",
                        "label": mcp["path_name"],
                        "required": True,
                        "description": mcp["path_help"],
                    }
                )
            return {
                "title": f"安装 {mcp['name']}",
                "size": "md",
                "body": {
                    "type": "form",
                    "api": {
                        "method": "post",
                        "url": "/api/mcp/install",
                        "data": {
                            "mcp_id": mcp["id"],
                            "token": "${token}",
                            "path": "${path}",
                        },
                    },
                    "messages": {"success": f"{mcp['name']} 安装成功！"},
                    "body": [
                        {
                            "type": "alert",
                            "level": "info",
                            "body": f"即将安装 {mcp['name']}，这将自动配置以下工具：{', '.join(mcp['tools'])}",
                        },
                        *form_body,
                    ],
                },
            }

        def _detail_dialog(mcp):
            return {
                "title": f"{mcp['name']} 详情",
                "size": "lg",
                "body": [
                    {
                        "type": "tpl",
                        "tpl": f'<div style="text-align: center; padding: 20px;"><span style="font-size: 64px;">{mcp["icon"]}</span><h2>{mcp["name"]}</h2><p style="color: #666;">{mcp["description"]}</p></div>',
                    },
                    {"type": "divider"},
                    {
                        "type": "tpl",
                        "tpl": f"<h4>提供的工具</h4><ul>{''.join([f'<li><code>{tool}</code></li>' for tool in mcp['tools']])}</ul>",
                    },
                    {"type": "divider"},
                    {
                        "type": "tpl",
                        "tpl": f"<h4>安装方式</h4><pre>{mcp['install_command']} {' '.join(mcp['install_args'])}</pre>",
                    },
                ],
            }

        install_btn = {
            "type": "button",
            "label": "安装",
            "level": "primary",
            "size": "sm",
            "actionType": "dialog",
            "dialog": _install_dialog(mcp),
        }
        detail_btn = {
            "type": "button",
            "label": "详情",
            "level": "light",
            "size": "sm",
            "actionType": "dialog",
            "dialog": _detail_dialog(mcp),
        }
        return {
            "type": "card",
            "className": "m-b-sm",
            "header": {
                "title": mcp["name"],
                "subTitle": mcp["category"],
                "avatar": mcp["icon"],
            },
            "body": [
                {
                    "type": "tpl",
                    "tpl": f'<p style="color: #666; font-size: 13px; margin: 8px 0;">{mcp["description"]}</p>',
                },
                {
                    "type": "flex",
                    "justify": "flex-end",
                    "className": "mt-4",
                    "items": [{"type": "button-group", "buttons": [install_btn, detail_btn]}],
                },
            ],
        }

    cards = []
    for mcp in MCP_MARKET:
        cards.append(_market_card(mcp))
    return {
        "type": "panel",
        "title": "🔍 可用 MCP",
        "body": [
            {
                "type": "grid",
                "columns": 3,
                "gap": "md",
                "items": cards,
            }
        ],
    }


def _installed_servers_section():
    """已安装的服务器列表"""

    def _add_mcp_dialog():
        """添加 MCP 对话框"""
        return {
            "title": "添加 MCP 服务器",
            "size": "lg",
            "body": {
                "type": "form",
                "api": "post:/api/mcp/create",
                "messages": {"success": "创建成功"},
                "redirect": "success:back",
                "body": [
                    {
                        "type": "input-text",
                        "name": "id",
                        "label": "ID",
                        "required": True,
                        "placeholder": "唯一标识符，如 filesystem",
                        "description": "只能包含小写字母、数字和连字符",
                    },
                    {
                        "type": "input-text",
                        "name": "name",
                        "label": "名称",
                        "required": True,
                        "placeholder": "显示名称",
                    },
                    {
                        "type": "select",
                        "name": "environment",
                        "label": "环境",
                        "value": "default",
                        "options": [
                            {"label": "默认", "value": "default"},
                            {"label": "开发", "value": "development"},
                            {"label": "生产", "value": "production"},
                        ],
                    },
                    {
                        "type": "input-text",
                        "name": "command",
                        "label": "命令",
                        "required": True,
                        "value": "npx",
                        "placeholder": "启动命令，如 npx",
                    },
                    {
                        "type": "json-editor",
                        "name": "args",
                        "label": "参数",
                        "description": "参数列表，JSON 数组格式",
                        "value": [],
                    },
                    {
                        "type": "json-editor",
                        "name": "env",
                        "label": "环境变量",
                        "description": "环境变量，JSON 对象格式",
                        "value": {},
                    },
                    {
                        "type": "textarea",
                        "name": "description",
                        "label": "描述",
                        "placeholder": "描述这个 MCP 的用途",
                    },
                    {"type": "divider", "title": "安全配置"},
                    {
                        "type": "switch",
                        "name": "security.readonly",
                        "label": "只读模式",
                        "value": False,
                        "description": "开启后将拦截所有写操作",
                    },
                    {
                        "type": "switch",
                        "name": "security.confirm_on_dangerous",
                        "label": "高危操作需要确认",
                        "value": True,
                        "description": "删除、写入等高危操作需要用户确认才能执行",
                    },
                    {
                        "type": "json-editor",
                        "name": "security.allowed_paths",
                        "label": "允许访问的文件路径",
                        "description": "留空表示允许所有路径，否则只允许列表内路径及其子目录",
                        "value": [],
                    },
                    {
                        "type": "json-editor",
                        "name": "security.allowed_domains",
                        "label": "允许访问的域名",
                        "value": [],
                    },
                    {"type": "switch", "name": "enabled", "label": "启用", "value": True},
                ],
            },
        }

    def _edit_mcp_dialog():
        """编辑 MCP 对话框"""
        return {
            "title": "编辑 MCP 配置",
            "size": "lg",
            "body": {
                "type": "form",
                "api": "put:/api/mcp/update/${id}",
                "initApi": "get:/api/mcp/get/${id}",
                "messages": {"success": "更新成功"},
                "redirect": "success:refresh",
                "body": [
                    {"type": "static", "label": "ID", "name": "id"},
                    {
                        "type": "input-text",
                        "name": "name",
                        "label": "名称",
                        "required": True,
                    },
                    {
                        "type": "select",
                        "name": "environment",
                        "label": "环境",
                        "options": [
                            {"label": "默认", "value": "default"},
                            {"label": "开发", "value": "development"},
                            {"label": "生产", "value": "production"},
                        ],
                    },
                    {
                        "type": "input-text",
                        "name": "command",
                        "label": "命令",
                        "required": True,
                    },
                    {"type": "json-editor", "name": "args", "label": "参数"},
                    {"type": "json-editor", "name": "env", "label": "环境变量"},
                    {"type": "textarea", "name": "description", "label": "描述"},
                    {"type": "divider", "title": "安全配置"},
                    {
                        "type": "switch",
                        "name": "security.readonly",
                        "label": "只读模式",
                        "description": "开启后将拦截所有写操作",
                    },
                    {
                        "type": "switch",
                        "name": "security.confirm_on_dangerous",
                        "label": "高危操作需要确认",
                        "description": "删除、写入等高危操作需要用户确认才能执行",
                    },
                    {
                        "type": "json-editor",
                        "name": "security.allowed_paths",
                        "label": "允许访问的文件路径",
                        "description": "留空表示允许所有路径，否则只允许列表内路径及其子目录",
                    },
                    {
                        "type": "json-editor",
                        "name": "security.allowed_domains",
                        "label": "允许访问的域名",
                    },
                    {"type": "switch", "name": "enabled", "label": "启用"},
                ],
            },
        }

    return {
        "type": "panel",
        "title": "⚙️ 已安装 MCP 服务器",
        "body": [
            {
                "type": "crud",
                "api": "/api/mcp/list",
                "name": "installed-mcp",
                "primaryField": "id",
                "perPage": 20,
                "headerToolbar": [
                    {
                        "type": "button",
                        "label": "添加 MCP",
                        "level": "primary",
                        "actionType": "dialog",
                        "dialog": {"title": "添加 MCP 服务器", "body": _add_mcp_dialog()},
                    },
                    "reload",
                ],
                "columns": [
                    {"name": "name", "label": "名称", "type": "text"},
                    {
                        "name": "environment",
                        "label": "环境",
                        "type": "badge",
                        "map": {
                            "default": "default",
                            "development": "开发",
                            "production": "生产",
                        },
                    },
                    {
                        "name": "connected",
                        "label": "连接",
                        "type": "status",
                        "map": {
                            "True": {"label": "已连接", "type": "success"},
                            "False": {"label": "未连接", "type": "default"},
                        },
                    },
                    {
                        "name": "token_estimate",
                        "label": "预估 Token",
                        "type": "number",
                        "remark": "开启此MCP会增加的上下文Token消耗",
                    },
                    {"name": "tool_count", "label": "工具数", "type": "number"},
                    {
                        "type": "operation",
                        "label": "操作",
                        "buttons": [
                            {
                                "label": "健康检查",
                                "type": "button",
                                "level": "info",
                                "size": "sm",
                                "actionType": "ajax",
                                "api": "get:/api/mcp/check-health/${id}",
                                "onSuccess": "window.alert('状态: ' + event.data.data.status + '\\n健康: ' + event.data.data.health)",
                            },
                            {
                                "label": "查看日志",
                                "type": "button",
                                "level": "light",
                                "size": "sm",
                                "actionType": "link",
                                "link": "/logs?server_id=${id}",
                            },
                            {
                                "label": "配置",
                                "type": "button",
                                "level": "primary",
                                "size": "sm",
                                "actionType": "dialog",
                                "dialog": _edit_mcp_dialog(),
                            },
                            {
                                "label": "启用",
                                "type": "button",
                                "level": "success",
                                "size": "sm",
                                "actionType": "ajax",
                                "api": "post:/api/mcp/connect/${id}",
                                "visibleOn": "!data.connected",
                                "messages": {"success": "已启用"},
                                "refresh": True,
                            },
                            {
                                "label": "停用",
                                "type": "button",
                                "level": "warning",
                                "size": "sm",
                                "actionType": "ajax",
                                "api": "post:/api/mcp/disconnect/${id}",
                                "visibleOn": "data.connected",
                                "messages": {"success": "已停用"},
                                "refresh": True,
                            },
                            {
                                "label": "卸载",
                                "type": "button",
                                "level": "danger",
                                "size": "sm",
                                "actionType": "ajax",
                                "api": "delete:/api/mcp/delete/${id}",
                                "confirmText": "确定要卸载此MCP吗？",
                                "messages": {"success": "已卸载"},
                                "refresh": True,
                            },
                        ],
                    },
                ],
            }
        ],
    }


def _dependency_install_section():
    """依赖安装区域"""
    return {
        "type": "panel",
        "title": "📦 依赖管理",
        "body": [
            {
                "type": "alert",
                "level": "info",
                "body": "如果环境检测显示某些依赖缺失，可以在这里一键安装",
            },
            {
                "type": "flex",
                "items": [
                    {
                        "type": "select",
                        "name": "dependency",
                        "placeholder": "选择要安装的依赖",
                        "options": [
                            {"label": "node", "value": "node"},
                            {"label": "uv", "value": "uv"},
                        ],
                    },
                    {
                        "type": "button",
                        "label": "一键安装",
                        "level": "primary",
                        "actionType": "ajax",
                        "api": "post:/api/mcp/install-dependency",
                        "data": {"dependency": "${dependency}"},
                        "onSuccess": "window.alert(event.data.message)",
                    },
                ],
            },
        ],
    }


# 剩余函数在 mcp_parts2.py 中定义
from .mcp_parts2 import (
    _export_import_section,
    _presets_section,
    _secret_manager_section,
)

__all__ = [
    "_market_gallery_section",
    "_installed_servers_section",
    "_dependency_install_section",
    "_secret_manager_section",
    "_presets_section",
    "_export_import_section",
]
