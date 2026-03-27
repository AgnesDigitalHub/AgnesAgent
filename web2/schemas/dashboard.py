"""
Dashboard 页面 schema
演示如何使用 python-amis Pydantic 模型构建 schema
"""

from amis.components.Page import Page
from amis.components.Card import Card
from amis.components.Flex import Flex
from amis.components.Grid import Grid
from amis.components.GridColumnObject import GridColumnObject as GridColumn
from amis.components.Button import Button
from amis.components.Chart import Chart
from amis.components.Table import Table
from amis.components.Status import Status


def get_dashboard_schema() -> dict:
    """
    使用 python-amis Pydantic 模型构建 Dashboard 页面 schema
    返回的 dict 会直接嵌入 App 配置的 pages 中
    """
    
    # 统计卡片
    stats_cards = Flex().items([
        Card().className("m-b-sm text-center").body([
            {
                "type": "tpl",
                "tpl": "<div class='text-lg font-bold'>$totalChats</div><div class='text-gray-500'>总对话数</div>"
            }
        ]),
        Card().className("m-b-sm text-center ml-2").body([
            {
                "type": "tpl",
                "tpl": "<div class='text-lg font-bold'>$activeAgents</div><div class='text-gray-500'>活跃 Agent</div>"
            }
        ]),
        Card().className("m-b-sm text-center ml-2").body([
            {
                "type": "tpl",
                "tpl": "<div class='text-lg font-bold'>$totalDocs</div><div class='text-gray-500'>知识库文档</div>"
            }
        ]),
        Card().className("m-b-sm text-center ml-2").body([
            {
                "type": "tpl",
                "tpl": "<div class='text-lg font-bold'>$todayTokens</div><div class='text-gray-500'>今天 Token 用量</div>"
            }
        ]),
    ])

    # 最近活动表格
    recent_activities = Table()\
        .title("最近活动")\
        .source("${recentActivities}")\
        .columns([
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
        ])\
        .affixHeader(True)

    # 使用流量图表
    usage_chart = Chart()\
        .type("line")\
        .title("Token 使用趋势")\
        .api("/api/dashboard/tokens")

    # 组合成完整页面
    page = Page()\
        .title("概览")\
        .body([
            stats_cards,
            Grid().columns([
                GridColumn().body(usage_chart).md(8),
                GridColumn().body(recent_activities).md(4),
            ]),
        ])

    # 转换为 dict
    return page.to_dict()
