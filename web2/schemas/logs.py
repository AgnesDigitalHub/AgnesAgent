"""
运行日志页面 Schema - 使用 python-amis 构建（开发中）
"""

from amis.amis import amis


def get_logs_schema():
    """获取运行日志页面 amis Schema"""
    a = amis()

    alert = a.Alert()
    alert.level("warning")
    alert.body("🚧 此功能正在开发中，敬请期待...")

    tpl = a.Tpl()
    tpl.tpl(
        "<div class='text-center py-8'><div class='text-6xl mb-4'>📜</div><div class='text-xl text-gray-500'>运行日志功能即将上线</div><div class='text-gray-400 mt-2'>查看和追踪系统运行日志</div></div>"
    )

    card = a.Card()
    card.title("运行日志")
    card.body([tpl])

    page = a.Page()
    page.title("运行日志")
    page.body([alert, card])

    return page.to_dict()
