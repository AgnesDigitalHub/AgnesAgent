"""
Workflow 编排页面 Schema（开发中）
"""


def get_workflows_schema():
    """获取 Workflow 编排页面 amis Schema"""
    return {
        "type": "page",
        "title": "Workflow 编排",
        "body": [
            {
                "type": "alert",
                "level": "warning",
                "body": "🚧 此功能正在开发中，敬请期待...",
            },
            {
                "type": "card",
                "title": "Workflow 编排",
                "body": [
                    {
                        "type": "tpl",
                        "tpl": "<div class='text-center py-8'><div class='text-6xl mb-4'>🔗</div><div class='text-xl text-gray-500'>Workflow 编排功能即将上线</div><div class='text-gray-400 mt-2'>可视化编排您的工作流程</div></div>",
                    }
                ],
            },
        ],
    }
