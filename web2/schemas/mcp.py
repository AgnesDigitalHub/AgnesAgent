"""
MCP 服务器管理页面 Schema - 使用 python-amis 构建
MCP (Model Context Protocol) 服务器管理，支持添加、删除、测试连接
"""

from amis.components.Button import Button
from amis.components.ButtonToolbar import ButtonToolbar
from amis.components.CRUDTable import CRUDTable
from amis.components.Dialog import Dialog
from amis.components.Form import Form
from amis.components.InputArray import InputArray
from amis.components.InputText import InputText
from amis.components.JSONEditorControl import JSONEditorControl
from amis.components.Page import Page
from amis.components.Select import Select
from amis.components.Switch import Switch
from amis.components.Table import Table


def get_mcp_schema():
    """获取 MCP 管理页面 amis Schema"""

    # 创建表单 - 添加/编辑
    def _get_create_form():
        json_editor = JSONEditorControl().name("env").label("环境变量 (JSON)").placeholder('{"KEY": "value"}').to_dict()
        # 修正 type - python-amis 对 JSONEditorControl 过度转换
        json_editor["type"] = "json-editor"

        form = (
            Form()
            .api("post:/api/mcp/create")
            .submitText("添加并测试连接")
            .body(
                [
                    InputText()
                    .name("id")
                    .label("服务器 ID")
                    .placeholder("唯一标识符，例如: my-mcp-server")
                    .required(True),
                    InputText().name("name").label("服务器名称").placeholder("显示名称").required(True),
                    InputText().name("description").label("描述").placeholder("简单描述这个服务器的用途"),
                    Select()
                    .name("transport_type")
                    .label("传输类型")
                    .options(
                        [
                            {"label": "STDIO", "value": "stdio"},
                        ]
                    )
                    .value("stdio")
                    .required(True),
                    InputText().name("command").label("启动命令").placeholder("例如: python 或 uv").required(True),
                    InputArray()
                    .name("args")
                    .label("命令参数")
                    .placeholder("每个参数一行，例如: -m\nmcp_game_automation"),
                    json_editor,
                    Switch().name("enabled").label("启用").value(True),
                ]
            )
        )
        return form.to_dict()

    # 创建编辑表单 (修改 API)
    def _get_edit_form():
        form = _get_create_form()
        # Already is dict, modify directly
        form["initApi"] = "get:/api/mcp/get/${id}"
        form["api"] = "put:/api/mcp/update/${id}"
        return form

    # 工具列表对话框
    def _get_tools_dialog():
        table = (
            Table()
            .source("${tools|json}")
            .columns(
                [
                    {"name": "name", "label": "工具名称", "type": "text"},
                    {"name": "description", "label": "描述", "type": "text"},
                ]
            )
        )
        return table.to_dict()

    # 组合工具栏和 CRUD
    toolbar = ButtonToolbar().buttons(
        [
            Button()
            .label("添加 MCP 服务器")
            .level("primary")
            .icon("fa fa-plus")
            .actionType("dialog")
            .dialog(Dialog().title("添加 MCP 服务器").body(_get_create_form()).size("lg").to_dict()),
            Button().label("刷新").icon("fa fa-refresh").actionType("reload").target("mcp-table"),
        ]
    )

    crud = (
        CRUDTable()
        .api("/api/mcp/list")
        .name("mcp-table")
        .primaryField("id")
        .columns(
            [
                {"name": "id", "label": "ID", "type": "text"},
                {"name": "name", "label": "名称", "type": "text"},
                {"name": "transport_type", "label": "传输", "type": "text"},
                {"name": "command", "label": "命令", "type": "text"},
                {
                    "name": "connected",
                    "label": "连接状态",
                    "type": "status",
                    "map": {
                        "true": {"label": "已连接", "type": "success"},
                        "false": {"label": "未连接", "type": "danger"},
                    },
                },
                {"name": "tool_count", "label": "工具数", "type": "number"},
                {
                    "type": "operation",
                    "label": "操作",
                    "buttons": [
                        {
                            "label": "测试连接",
                            "type": "button",
                            "level": "success",
                            "actionType": "ajax",
                            "api": "post:/api/mcp/test/${id}",
                            "messages": {"success": "连接成功"},
                            "refresh": True,
                        },
                        {
                            "label": "断开连接",
                            "type": "button",
                            "level": "warning",
                            "actionType": "ajax",
                            "api": "post:/api/mcp/disconnect/${id}",
                            "messages": {"success": "已断开连接"},
                            "refresh": True,
                        },
                        {
                            "label": "编辑",
                            "type": "button",
                            "level": "info",
                            "actionType": "dialog",
                            "dialog": {
                                "title": "编辑 MCP 服务器",
                                "body": _get_edit_form(),
                                "size": "lg",
                            },
                        },
                        {
                            "label": "查看工具",
                            "type": "button",
                            "level": "primary",
                            "actionType": "dialog",
                            "dialog": {
                                "title": "工具列表 - ${name}",
                                "body": _get_tools_dialog(),
                                "size": "lg",
                            },
                        },
                        {
                            "label": "删除",
                            "type": "button",
                            "level": "danger",
                            "actionType": "ajax",
                            "api": "delete:/api/mcp/delete/${id}",
                            "confirmText": "确定要删除这个服务器吗？",
                            "messages": {"success": "删除成功"},
                            "refresh": True,
                        },
                    ],
                },
            ]
        )
    )

    # 组合成完整页面
    page = Page().title("MCP 管理").body([toolbar, crud])

    return page.to_dict()
