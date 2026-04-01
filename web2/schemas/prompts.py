"""
提示词管理页面 Schema - 直接字典构建
"""


def get_prompts_schema() -> dict:
    """获取 Prompt IDE 页面 amis Schema"""

    return {
        "type": "page",
        "title": "Prompt IDE",
        "body": [
            {
                "type": "alert",
                "level": "warning",
                "body": "🚧 此功能正在开发中，敬请期待...",
            },
            {
                "type": "card",
                "title": "Prompt IDE",
                "body": [
                    {
                        "type": "tpl",
                        "tpl": "<div class='text-center py-8'><div class='text-6xl mb-4'>💬</div><div class='text-xl text-gray-500'>Prompt IDE 功能即将上线</div><div class='text-gray-400 mt-2'>编辑、测试和管理您的 Prompt</div></div>",
                    }
                ],
            },
        ],
    }
