"""
Agent 管理页面 schema
演示如何使用 python-amis Pydantic 模型构建 schema
"""

from amis.components.Page import Page
from amis.components.CRUD2 import CRUD2
from amis.components.CRUD2Table import CRUD2Table
from amis.components.CRUD2Cards import CRUD2Cards
from amis.components.Button import Button
from amis.components.Dialog import Dialog
from amis.components.Form import Form
from amis.components.InputText import InputText
from amis.components.Textarea import Textarea
from amis.components.Switch import Switch
from amis.components.Column import Column
from amis.components.Status import Status
from amis.components.Operation import Operation
from amis.components.Action import Action
from amis.components.DialogAction import DialogAction


def get_agents_schema() -> dict:
    """
    使用 python-amis Pydantic 模型构建 Agent 管理页面 schema
    返回的 dict 会直接嵌入 App 配置的 pages 中
    """

    # 表格列配置
    columns = [
        Column()\
            .name("id")\
            .label("ID")\
            .width("60"),

        Column()\
            .name("name")\
            .label("名称"),

        Column()\
            .name("description")\
            .label("描述")\
            .breakpoint("md"),

        Column()\
            .name("enabled")\
            .label("状态")\
            .width("100")\
            .type("status")\
            .mapping({
                "true": {"label": "启用", "color": "green"},
                "false": {"label": "禁用", "color": "red"},
            }),

        Column()\
            .name("created_at")\
            .label("创建时间")\
            .type("datetime")\
            .format("YYYY-MM-DD HH:mm")\
            .breakpoint("lg"),

        Operation()\
            .label("操作")\
            .width("200")\
            .fixed("right")\
            .buttons([
                DialogAction()\
                    .label("编辑")\
                    .level("link")\
                    .dialog(Dialog()\
                        .title("编辑 Agent")\
                        .body([
                            Form()\
                                .api("/api/agents/save/$id")\
                                .initApi("/api/agents/get/$id")\
                                .body([
                                    InputText()\
                                        .name("name")\
                                        .label("Agent 名称")\
                                        .required(True),
                                    Textarea()\
                                        .name("description")\
                                        .label("描述"),
                                    Switch()\
                                        .name("enabled")\
                                        .label("启用")\
                                        .value(True),
                                ])
                                .set("buttons", [
                                    {"type": "submit", "label": "保存", "primary": True}
                                ])
                        ])
                    ),
                Action()\
                    .label("删除")\
                    .level("link")\
                    .type("submit")\
                    .api("/api/agents/delete/$id")\
                    .confirmText("确定要删除这个 Agent 吗？"),
            ]),
    ]

    # CRUD 配置
    crud = CRUD2()\
        .api("/api/agents/list")\
        .addDialog(Dialog()\
            .title("新建 Agent")\
            .body([
                Form()\
                    .api("/api/agents/create")\
                    .body([
                        InputText()\
                            .name("name")\
                            .label("Agent 名称")\
                            .required(True),
                        Textarea()\
                            .name("description")\
                            .label("描述"),
                        Switch()\
                            .name("enabled")\
                            .label("启用")\
                            .value(True),
                    ])
                    .set("buttons", [
                        {"type": "submit", "label": "创建", "primary": True}
                    ])
            ])
        )\
        .set("columns", columns)\
        .bulkActions([
            {"label": "批量删除", "type": "button", "level": "danger", "api": "/api/agents/bulk-delete", "confirmText": "确定要删除选中吗？"}
        ])

    # 组合成完整页面
    page = Page()\
        .title("Agent 管理")\
        .body([crud])

    # 转换为 dict
    return page.to_dict()