"""
工作流管理页面 Schema - 使用 python-amis 构建（开发中）
"""

from amis.amis import amis


def get_workflows_schema():
    """获取 Workflow 编排页面 amis Schema"""
    a = amis()
    
    alert = a.Alert()
    alert.level("warning")
    alert.body("🚧 此功能正在开发中，敬请期待...")

    tpl = a.Tpl()
    tpl.tpl("<div class='text-center py-8'><div class='text-6xl mb-4'>🔗</div><div class='text-xl text-gray-500'>Workflow 编排功能即将上线</div><div class='text-gray-400 mt-2'>可视化编排您的工作流程</div></div>")

    card = a.Card()
    card.title("Workflow 编排")
    card.body([tpl])

    page = a.Page()
    page.title("Workflow 编排")
    page.body([alert, card])

    return page.to_dict()
