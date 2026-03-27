"""
工具/插件管理页面 Schema（开发中）
"""


def get_tools_schema():
    """获取工具管理页面 amis Schema"""
    return {
        "type": "page",
        "title": "工具/插件管理",
        "body": [
            {
                "type": "alert",
                "level": "warning",
                "body": "🚧 此功能正在开发中，敬请期待...",
            },
            {
                "type": "card",
                "title": "工具/插件管理",
                "body": [
                    {
                        "type": "tpl",
                        "tpl": "<div class='text-center py-8'><div class='text-6xl mb-4'>🔧</div><div class='text-xl text-gray-500'>工具/插件管理功能即将上线</div><div class='text-gray-400 mt-2'>注册和管理您的工具与插件</div></div>",
                    }
                ],
            },
        ],
    }
