"""
MCP Schema 剩余部分
"""


def _secret_manager_section_continued():
    """继续定义密钥管理区域"""
    return {
        "type": "tabs",
        "tabs": [
            {
                "title": "密钥列表",
                "body": [
                    {
                        "type": "crud",
                        "api": "/api/mcp/secrets/list",
                        "primaryField": "key",
                        "columns": [
                            {"name": "key", "label": "变量名"},
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
                                "type": "operation",
                                "buttons": [
                                    {
                                        "label": "删除",
                                        "level": "danger",
                                        "size": "sm",
                                        "actionType": "ajax",
                                        "api": "delete:/api/mcp/secrets/${key}",
                                        "confirmText": "确定删除？",
                                        "messages": {"success": "已删除"},
                                        "refresh": True,
                                    },
                                ],
                            },
                        ],
                        "headerToolbar": [
                            {
                                "type": "button",
                                "label": "添加密钥",
                                "level": "primary",
                                "actionType": "dialog",
                                "dialog": {
                                    "title": "添加 API Key",
                                    "body": {
                                        "type": "form",
                                        "api": "post:/api/mcp/secrets/add",
                                        "messages": {"success": "添加成功"},
                                        "redirect": "success:refresh",
                                        "body": [
                                            {
                                                "type": "input-text",
                                                "name": "key",
                                                "label": "变量名",
                                                "placeholder": "如 GITHUB_TOKEN",
                                                "required": True,
                                            },
                                            {
                                                "type": "input-password",
                                                "name": "value",
                                                "label": "密钥值",
                                                "required": True,
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
                                        ],
                                    },
                                },
                            },
                            "reload",
                        ],
                    },
                ],
            },
            {
                "title": "环境切换",
                "body": [
                    {
                        "type": "alert",
                        "level": "info",
                        "body": "选择当前使用哪个环境的配置",
                    },
                    {
                        "type": "radio",
                        "name": "current_environment",
                        "options": [
                            {"label": "默认", "value": "default"},
                            {"label": "开发", "value": "development"},
                            {"label": "生产", "value": "production"},
                        ],
                        "value": "${global.current_environment || 'default'}",
                    },
                    {
                        "type": "button",
                        "label": "切换环境",
                        "level": "primary",
                        "actionType": "ajax",
                        "api": "post:/api/mcp/secrets/set-environment",
                        "data": {"environment": "${current_environment}"},
                        "messages": {"success": "环境已切换"},
                    },
                ],
            },
        ],
    }


def _secret_manager_section():
    """完整的密钥管理区域"""
    part1 = {
        "type": "panel",
        "title": "🔑 API 密钥管理 (加密存储)",
        "body": [
            {
                "type": "alert",
                "level": "info",
                "body": "API Keys 会以加密形式保存在本地，启动 MCP 时自动注入环境变量",
            },
        ],
    }
    part2 = _secret_manager_section_continued()
    # 合并 body
    part1["body"].extend(part2["tabs"][0]["body"])
    return part1


def _presets_section():
    """预设包区域"""
    return {
        "type": "panel",
        "title": "📦 预设组合包",
        "body": [
            {
                "type": "alert",
                "level": "info",
                "body": "根据使用场景快速启用一组常用工具",
            },
            {
                "type": "grid",
                "columns": 2,
                "gap": "md",
                "items": [
                    {
                        "type": "card",
                        "header": {
                            "title": "代码助手",
                            "avatar": "💻",
                        },
                        "body": [
                            {
                                "type": "tpl",
                                "tpl": '<p style="color: #666; font-size: 13px;">自动开启 Git + Filesystem + Terminal，适合开发编程</p>',
                            },
                            {
                                "type": "flex",
                                "justify": "flex-end",
                                "items": [
                                    {
                                        "type": "button",
                                        "label": "应用此预设",
                                        "level": "primary",
                                        "size": "sm",
                                        "actionType": "ajax",
                                        "api": "post:/api/mcp/presets/apply",
                                        "data": {"preset": "code_assistant"},
                                        "messages": {"success": "预设已应用，请刷新页面查看"},
                                        "refresh": True,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "type": "card",
                        "header": {
                            "title": "学术搜索",
                            "avatar": "🔬",
                        },
                        "body": [
                            {
                                "type": "tpl",
                                "tpl": '<p style="color: #666; font-size: 13px;">自动开启 Brave Search + Arxiv，适合文献调研</p>',
                            },
                            {
                                "type": "flex",
                                "justify": "flex-end",
                                "items": [
                                    {
                                        "type": "button",
                                        "label": "应用此预设",
                                        "level": "primary",
                                        "size": "sm",
                                        "actionType": "ajax",
                                        "api": "post:/api/mcp/presets/apply",
                                        "data": {"preset": "academic_search"},
                                        "messages": {"success": "预设已应用，请刷新页面查看"},
                                        "refresh": True,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "type": "card",
                        "header": {
                            "title": "数据分析",
                            "avatar": "📊",
                        },
                        "body": [
                            {
                                "type": "tpl",
                                "tpl": '<p style="color: #666; font-size: 13px;">Filesystem + SQLite + Pandas，适合数据分析</p>',
                            },
                            {
                                "type": "flex",
                                "justify": "flex-end",
                                "items": [
                                    {
                                        "type": "button",
                                        "label": "应用此预设",
                                        "level": "primary",
                                        "size": "sm",
                                        "actionType": "ajax",
                                        "api": "post:/api/mcp/presets/apply",
                                        "data": {"preset": "data_analysis"},
                                        "messages": {"success": "预设已应用，请刷新页面查看"},
                                        "refresh": True,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "type": "card",
                        "header": {
                            "title": "网页自动化",
                            "avatar": "🌐",
                        },
                        "body": [
                            {
                                "type": "tpl",
                                "tpl": '<p style="color: #666; font-size: 13px;">Puppeteer + Fetch，适合网页抓取和自动化</p>',
                            },
                            {
                                "type": "flex",
                                "justify": "flex-end",
                                "items": [
                                    {
                                        "type": "button",
                                        "label": "应用此预设",
                                        "level": "primary",
                                        "size": "sm",
                                        "actionType": "ajax",
                                        "api": "post:/api/mcp/presets/apply",
                                        "data": {"preset": "web_automation"},
                                        "messages": {"success": "预设已应用，请刷新页面查看"},
                                        "refresh": True,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    }


def _export_import_section():
    """导出导入区域"""
    return {
        "type": "panel",
        "title": "📤 导出分享配置",
        "body": [
            {
                "type": "alert",
                "level": "info",
                "body": "将当前配置（人格 + MCP 设置）导出为 JSON 文件，可以分享给他人",
            },
            {
                "type": "flex",
                "gap": "md",
                "items": [
                    {
                        "type": "button",
                        "label": "导出配置",
                        "level": "primary",
                        "actionType": "download",
                        "download": {
                            "url": "/api/mcp/export",
                            "filename": "agnes-mcp-config.json",
                        },
                    },
                    {
                        "type": "input-file",
                        "name": "import_file",
                        "label": "导入配置",
                        "accept": ".json",
                    },
                    {
                        "type": "button",
                        "label": "导入配置",
                        "level": "secondary",
                        "actionType": "ajax",
                        "api": "post:/api/mcp/import",
                        "data": {"file": "${import_file}"},
                        "confirmText": "这将覆盖现有配置，确定继续吗？",
                        "messages": {"success": "导入成功"},
                        "refresh": True,
                    },
                ],
            },
        ],
    }


# 导出函数
__all__ = [
    "_secret_manager_section",
    "_presets_section",
    "_export_import_section",
]
