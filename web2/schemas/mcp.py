"""
MCP 市场页面 Schema - 用户友好的MCP管理
提供预置MCP列表，一键安装，简化配置流程
"""

import json
from pathlib import Path


def _load_mcp_market():
    """从JSON文件加载MCP市场数据"""
    market_file = Path(__file__).parent.parent.parent / "config" / "mcp" / "market.json"
    try:
        with open(market_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"[MCP] 成功加载市场数据: {len(data)} 条记录")
            return data
    except Exception as e:
        print(f"[MCP] 加载MCP市场数据失败: {e}")
        print(f"[MCP] 尝试加载的文件路径: {market_file}")
        return []


# 预置的 MCP 服务器市场数据
MCP_MARKET = _load_mcp_market()


def get_mcp_schema():
    """获取 MCP 市场页面 amis Schema"""

    # 市场卡片 - 单个MCP
    def _market_card(mcp):
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
                    "items": [
                        {
                            "type": "button-group",
                            "buttons": [install_btn, detail_btn],
                        },
                    ],
                },
            ],
        }

    # 安装对话框
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

    # 详情对话框
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

    # 已安装的MCP列表
    def _installed_list():
        return {
            "type": "crud",
            "api": "/api/mcp/list",
            "name": "installed-mcp",
            "primaryField": "id",
            "perPage": 20,
            "headerToolbar": ["reload"],
            "columns": [
                {
                    "name": "name",
                    "label": "名称",
                    "type": "text",
                },
                {
                    "name": "connected",
                    "label": "状态",
                    "type": "status",
                    "map": {
                        "true": {"label": "已连接", "type": "success"},
                        "false": {"label": "未连接", "type": "default"},
                    },
                },
                {"name": "tool_count", "label": "工具数", "type": "number"},
                {
                    "type": "operation",
                    "label": "操作",
                    "buttons": [
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

    # 市场列表
    market_cards = [_market_card(mcp) for mcp in MCP_MARKET]
    print(f"[MCP] 生成 market_cards: {len(market_cards)} 个卡片")

    # 将 market_cards 分成两列（二维数组格式）
    col1_cards = [card for i, card in enumerate(market_cards) if i % 2 == 0]
    col2_cards = [card for i, card in enumerate(market_cards) if i % 2 == 1]
    print(f"[MCP] 分列完成: 第一列 {len(col1_cards)} 个, 第二列 {len(col2_cards)} 个")

    # 组合页面
    return {
        "type": "page",
        "title": "MCP 市场",
        "body": [
            {
                "type": "alert",
                "level": "info",
                "body": "💡 MCP (Model Context Protocol) 可以为 AI 添加额外能力，如文件操作、网页搜索、数据库访问等。选择需要的功能一键安装即可！",
            },
            {
                "type": "tabs",
                "tabs": [
                    {
                        "title": "🏪 MCP 市场",
                        "body": [
                            {
                                "type": "grid",
                                "columns": [{"md": 6}, {"md": 6}],
                                "gap": "md",
                                "items": [
                                    {"body": col1_cards},  # 包装成对象
                                    {"body": col2_cards},  # 包装成对象
                                ],
                            }
                        ],
                    },
                    {
                        "title": "📦 已安装",
                        "body": [_installed_list()],
                    },
                ],
            },
        ],
    }
