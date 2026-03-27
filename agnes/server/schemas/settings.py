"""
系统设置页面 Schema（开发中）
"""


def get_settings_schema():
    """获取系统设置页面 amis Schema"""
    return {
        "type": "page",
        "title": "系统设置",
        "body": [
            {
                "type": "alert",
                "level": "warning",
                "body": "🚧 此功能正在开发中，敬请期待...",
            },
            {
                "type": "card",
                "title": "系统设置",
                "body": [
                    {
                        "type": "tpl",
                        "tpl": "<div class='text-center py-8'><div class='text-6xl mb-4'>⚙️</div><div class='text-xl text-gray-500'>系统设置功能即将上线</div><div class='text-gray-400 mt-2'>配置全局参数和系统选项</div></div>",
                    }
                ],
            },
        ],
    }
