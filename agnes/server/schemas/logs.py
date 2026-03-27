"""
运行日志页面 Schema（开发中）
"""


def get_logs_schema():
    """获取运行日志页面 amis Schema"""
    return {
        "type": "page",
        "title": "运行日志",
        "body": [
            {
                "type": "alert",
                "level": "warning",
                "body": "🚧 此功能正在开发中，敬请期待...",
            },
            {
                "type": "card",
                "title": "运行日志",
                "body": [
                    {
                        "type": "tpl",
                        "tpl": "<div class='text-center py-8'><div class='text-6xl mb-4'>📜</div><div class='text-xl text-gray-500'>运行日志功能即将上线</div><div class='text-gray-400 mt-2'>查看和追踪系统运行日志</div></div>",
                    }
                ],
            },
        ],
    }
