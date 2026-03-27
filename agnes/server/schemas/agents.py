"""
Agent 管理页面 Schema（开发中）
"""


def get_agents_schema():
    """获取 Agent 管理页面 amis Schema"""
    return {
        "type": "page",
        "title": "Agent 管理",
        "body": [
            {
                "type": "alert",
                "level": "warning",
                "body": "🚧 此功能正在开发中，敬请期待...",
            },
            {
                "type": "card",
                "title": "Agent 管理",
                "body": [
                    {
                        "type": "tpl",
                        "tpl": "<div class='text-center py-8'><div class='text-6xl mb-4'>🤖</div><div class='text-xl text-gray-500'>Agent 管理功能即将上线</div><div class='text-gray-400 mt-2'>创建、配置和管理您的智能 Agent</div></div>",
                    }
                ],
            },
        ],
    }
