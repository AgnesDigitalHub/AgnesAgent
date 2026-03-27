"""
发布部署页面 Schema - 使用 python-amis 构建（开发中）
"""

from amis.amis import amis


def get_publish_schema():
    """获取 API/集成发布页面 amis Schema"""
    a = amis()
    
    alert = a.Alert()
    alert.level("warning")
    alert.body("🚧 此功能正在开发中，敬请期待...")

    tpl = a.Tpl()
    tpl.tpl("<div class='text-center py-8'><div class='text-6xl mb-4'>🔌</div><div class='text-xl text-gray-500'>API/集成发布功能即将上线</div><div class='text-gray-400 mt-2'>生成 API Key 和 Webhook 集成</div></div>")

    card = a.Card()
    card.title("API/集成发布")
    card.body([tpl])

    page = a.Page()
    page.title("API/集成发布")
    page.body([alert, card])

    return page.to_dict()
