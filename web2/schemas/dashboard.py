"""
Dashboard 页面 schema
演示如何使用 python-amis Pydantic 模型构建 schema
"""

from amis.components.Card import Card
from amis.components.Chart import Chart
from amis.components.Flex import Flex
from amis.components.Page import Page
from amis.components.Table import Table


def get_dashboard_schema() -> dict:
    """
    使用 python-amis Pydantic 模型构建 Dashboard 页面 schema
    返回的 dict 会直接嵌入 App 配置的 pages 中
    """

    # 统计卡片
    stats_cards = Flex().items(
        [
            Card()
            .className("m-b-sm text-center")
            .body(
                [
                    {
                        "type": "tpl",
                        "tpl": "<div class='text-lg font-bold'>$connected_agents</div><div class='text-gray-500'>连接 Agent 数</div>",
                    }
                ]
            ),
            Card()
            .className("m-b-sm text-center ml-2")
            .body(
                [
                    {
                        "type": "tpl",
                        "tpl": "<div class='text-lg font-bold'>$total_messages</div><div class='text-gray-500'>消息总数</div>",
                    }
                ]
            ),
            Card()
            .className("m-b-sm text-center ml-2")
            .body(
                [
                    {
                        "type": "tpl",
                        "tpl": "<div class='text-lg font-bold'>$uptime</div><div class='text-gray-500'>运行时间</div>",
                    }
                ]
            ),
            Card()
            .className("m-b-sm text-center ml-2")
            .body(
                [
                    {
                        "type": "tpl",
                        "tpl": "<div class='text-lg font-bold'>$memory_usage</div><div class='text-gray-500'>内存占用</div>",
                    }
                ]
            ),
        ]
    )

    # 最近活动表格
    recent_activities = (
        Table()
        .title("最近活动")
        .source("${recentActivities}")
        .columns(
            [
                {
                    "name": "time",
                    "label": "时间",
                    "type": "datetime",
                    "format": "YYYY-MM-DD HH:mm",
                },
                {
                    "name": "type",
                    "label": "类型",
                    "type": "mapping",
                    "map": {
                        "chat": "对话",
                        "agent_created": "创建 Agent",
                        "doc_uploaded": "上传文档",
                        "workflow_run": "运行工作流",
                    },
                },
                {
                    "name": "user",
                    "label": "用户",
                },
                {
                    "name": "status",
                    "label": "状态",
                    "type": "status",
                    "map": {
                        "success": {"label": "成功", "value": 1, "color": "green"},
                        "error": {"label": "失败", "value": 0, "color": "red"},
                        "running": {"label": "运行中", "value": 2, "color": "blue"},
                    },
                },
            ]
        )
        .affixHeader(True)
    )

    # 使用流量图表
    usage_chart = Chart().chartType("line").title("消息趋势").api("/api/dashboard/messages")

    # 组合成完整页面
    # 使用 flex 布局而不是 grid，避免类型错误
    page = Page().title("概览").api("/api/dashboard/stats").body([stats_cards, usage_chart, recent_activities])

    # 转换为 dict
    result = page.to_dict()

    return result
