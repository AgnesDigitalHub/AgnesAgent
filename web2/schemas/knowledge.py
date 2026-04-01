"""
知识库管理页面 Schema - 直接字典构建
"""


def get_knowledge_schema() -> dict:
    """获取知识库页面 amis Schema"""

    return {
        "type": "page",
        "title": "知识库/RAG",
        "body": [
            {
                "type": "alert",
                "level": "warning",
                "body": "🚧 此功能正在开发中，敬请期待...",
            },
            {
                "type": "card",
                "title": "知识库/RAG",
                "body": [
                    {
                        "type": "tpl",
                        "tpl": "<div class='text-center py-8'><div class='text-6xl mb-4'>📚</div><div class='text-xl text-gray-500'>知识库/RAG 功能即将上线</div><div class='text-gray-400 mt-2'>上传文档并构建您的知识库</div></div>",
                    }
                ],
            },
        ],
    }
