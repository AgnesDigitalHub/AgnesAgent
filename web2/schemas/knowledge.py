"""
知识库管理页面 Schema - 使用 python-amis 构建（开发中）
"""

from amis.amis import amis


def get_knowledge_schema():
    """获取知识库页面 amis Schema"""
    a = amis()
    
    alert = a.Alert()
    alert.level("warning")
    alert.body("🚧 此功能正在开发中，敬请期待...")

    tpl = a.Tpl()
    tpl.tpl("<div class='text-center py-8'><div class='text-6xl mb-4'>📚</div><div class='text-xl text-gray-500'>知识库/RAG 功能即将上线</div><div class='text-gray-400 mt-2'>上传文档并构建您的知识库</div></div>")

    card = a.Card()
    card.title("知识库/RAG")
    card.body([tpl])

    page = a.Page()
    page.title("知识库/RAG")
    page.body([alert, card])

    return page.to_dict()
