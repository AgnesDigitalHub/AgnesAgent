"""
用户管理页面 Schema - 直接字典构建
"""


def get_users_schema() -> dict:
    """获取用户权限页面 amis Schema"""

    return {
        "type": "page",
        "title": "用户权限",
        "body": [
            {
                "type": "alert",
                "level": "warning",
                "body": "🚧 此功能正在开发中，敬请期待...",
            },
            {
                "type": "card",
                "title": "用户权限",
                "body": [
                    {
                        "type": "tpl",
                        "tpl": "<div class='text-center py-8'><div class='text-6xl mb-4'>👥</div><div class='text-xl text-gray-500'>用户权限功能即将上线</div><div class='text-gray-400 mt-2'>管理用户和权限控制</div></div>",
                    }
                ],
            },
        ],
    }
