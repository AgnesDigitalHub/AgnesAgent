"""
API/集成发布页面 Schema（开发中）
"""


def get_publish_schema():
    """获取 API/集成发布页面 amis Schema"""
    return {
        "type": "page",
        "title": "API/集成发布",
        "body": [
            {
                "type": "alert",
                "level": "warning",
                "body": "🚧 此功能正在开发中，敬请期待...",
            },
            {
                "type": "card",
                "title": "API/集成发布",
                "body": [
                    {
                        "type": "tpl",
                        "tpl": "<div class='text-center py-8'><div class='text-6xl mb-4'>🔌</div><div class='text-xl text-gray-500'>API/集成发布功能即将上线</div><div class='text-gray-400 mt-2'>生成 API Key 和 Webhook 集成</div></div>",
                    }
                ],
            },
        ],
    }
