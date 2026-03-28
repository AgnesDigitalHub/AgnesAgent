"""
Agent 管理页面 schema
演示如何使用 python-amis Pydantic 模型构建 schema
"""

from amis.amis import amis


def get_agents_schema() -> dict:
    """
    使用 python-amis Pydantic 模型构建 Agent 管理页面 schema
    返回的 dict 会直接嵌入 App 配置的 pages 中
    """
    a = amis()

    # Add dialog
    add_dialog = a.Dialog()
    add_dialog.title("新建 Agent")
    add_dialog.body(
        a.Form()
        .api("/api/agents/create")
        .body(
            [
                a.InputText().name("name").label("Agent 名称").required(True),
                a.Textarea().name("description").label("描述"),
                a.Switch().name("enabled").label("启用").value(True),
            ]
        )
        .set("buttons", [{"type": "submit", "label": "创建", "primary": True}])
    )

    add_btn = a.Button()
    add_btn.type("button").label("新建 Agent").level("primary")
    add_btn.actionType("dialog").dialog(add_dialog)

    # Edit dialog
    edit_dialog = a.Dialog()
    edit_dialog.title("编辑 Agent")
    edit_dialog.body(
        a.Form()
        .api("put:/api/agents/save/${id}")
        .initApi("get:/api/agents/get/${id}")
        .body(
            [
                a.InputText().name("name").label("Agent 名称").required(True),
                a.Textarea().name("description").label("描述"),
                a.Switch().name("enabled").label("启用"),
            ]
        )
    )

    # Actions
    toggle_btn = a.Button()
    toggle_btn.type("button").label("${enabled ? '禁用' : '启用'}")
    toggle_btn.level("${enabled ? 'default' : 'success'}")
    toggle_btn.actionType("ajax")
    toggle_btn.api("put:/api/agents/save/${id}")
    toggle_btn.data({"enabled": "${!enabled}"})

    edit_btn = a.Button()
    edit_btn.type("button").label("编辑").level("info")
    edit_btn.actionType("dialog").dialog(edit_dialog)

    delete_btn = a.Button()
    delete_btn.type("button").label("删除").level("danger")
    delete_btn.actionType("ajax").confirmText("确定要删除这个 Agent 吗？")
    delete_btn.api("delete:/api/agents/delete/${id}")

    # CRUD Cards 卡片布局
    crud = a.CRUD()
    crud.api(
        {
            "method": "get",
            "url": "/api/agents/list",
            "responseData": {"items": "${items}", "total": "$total"},
        }
    )
    crud.perPage(12)
    crud.headerToolbar(["reload", add_btn])
    crud.mode("cards")
    crud.card(
        a.Card()
        .title("${name}")
        .subTitle("${enabled ? '启用' : '禁用'}")
        .body(
            [
                a.Tpl().tpl(
                    "<div style=\"color: #999; font-size: 13px; margin: 8px 0;\">${description || '无描述'}</div>"
                ),
                a.Flex()
                .className("flex justify-between items-center mt-4")
                .items(
                    [
                        a.Badge().label("${enabled ? '启用' : '禁用'}").level("${enabled ? 'success' : 'default'}"),
                        a.Group().buttons([edit_btn, toggle_btn, delete_btn]),
                    ]
                ),
            ]
        )
    )

    crud.bulkActions(
        [
            {
                "label": "批量删除",
                "type": "button",
                "level": "danger",
                "api": "/api/agents/bulk-delete",
                "confirmText": "确定要删除选中吗？",
            }
        ]
    )

    # 组合成完整页面
    page = a.Page().title("Agent 管理").body([crud])

    # 转换为 dict
    return page.to_dict()
