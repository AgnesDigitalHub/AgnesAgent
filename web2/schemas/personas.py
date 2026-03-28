"""
人格管理页面 Schema - 使用 python-amis 构建
"""

from amis.amis import amis


def get_personas_schema():
    """获取人格管理页面 amis Schema"""
    a = amis()

    # Create add dialog form fields
    it1 = a.InputText()
    it1.name("full_name").label("全名").required(True)

    it2 = a.InputText()
    it2.name("nickname").label("昵称")

    it3 = a.InputText()
    it3.name("role").label("角色")

    it4 = a.Textarea()
    it4.name("personality").label("性格描述").description("描述这个AI人格的性格特点")

    it5 = a.Textarea()
    it5.name("scenario").label("场景设定").description("描述对话发生的场景")

    it6 = a.Textarea()
    it6.name("system_prompt").label("系统提示词").required(True).description("原始系统提示词，会自动组合其他信息生成最终prompt")

    it7 = a.InputText()
    it7.name("description").label("描述")

    sw_enabled = a.Switch()
    sw_enabled.name("enabled").label("启用").value(True).description("禁用后该Agent无法使用")

    sel1 = a.Select()
    sel1.name("llm_profile_id").label("绑定模型").clearable(True).placeholder("使用全局激活模型")
    sel1.sourceApi("/api/profiles")
    sel1.options="${profiles.map(p => ({label: p.name, value: p.id}))}"

    # MCP Settings
    sw_mcp = a.Switch()
    sw_mcp.name("mcp_enabled").label("启用 MCP").value(False).description("连接 MCP 服务器提供工具能力")

    # 预定义的 MCP 服务器选项 - 后续可以改为动态配置管理
    mcp_checkboxes = a.Checkboxes()
    mcp_checkboxes.name("mcp_servers").label("启用 MCP 服务器")
    mcp_checkboxes.options([
        {"label": "Github", "value": "github"},
        {"label": "Fetch", "value": "fetch"},
        {"label": "Filesystem", "value": "filesystem"},
        {"label": "Postgres", "value": "postgres"},
        {"label": "Brave Search", "value": "brave-search"},
    ])
    mcp_checkboxes.visibleOn("data.mcp_enabled == true")

    # Skills Options
    skills_checkboxes = a.Checkboxes()
    skills_checkboxes.name("skills").label("启用技能工具")
    skills_checkboxes.options([
        {"label": "网页搜索", "value": "web_search"},
        {"label": "网页抓取", "value": "web_fetch"},
        {"label": "文件读取", "value": "file_read"},
        {"label": "文件写入", "value": "file_write"},
        {"label": "代码执行", "value": "code_interpreter"},
        {"label": "命令行执行", "value": "shell_exec"},
    ])

    add_form = a.Form()
    add_form.api("post:/api/personas")
    add_form.body([it1, it2, it3, it4, it5, it7, sel1, sw_enabled, sw_mcp, mcp_checkboxes, skills_checkboxes, it6])

    add_dialog = a.Dialog()
    add_dialog.title("新增 Agent (人格)")
    add_dialog.body(add_form)

    add_btn = a.Button()
    add_btn.type("button").label("新建 Agent").level("primary")
    add_btn.actionType("dialog").dialog(add_dialog)

    # Edit dialog
    eit1 = a.InputText()
    eit1.name("full_name").label("全名").required(True)

    eit2 = a.InputText()
    eit2.name("nickname").label("昵称")

    eit3 = a.InputText()
    eit3.name("role").label("角色")

    eit4 = a.Textarea()
    eit4.name("personality").label("性格描述")

    eit5 = a.Textarea()
    eit5.name("scenario").label("场景设定")

    eit6 = a.Textarea()
    eit6.name("system_prompt").label("系统提示词").required(True)

    eit7 = a.InputText()
    eit7.name("description").label("描述")

    esw_enabled = a.Switch()
    esw_enabled.name("enabled").label("启用").description("禁用后该Agent无法使用")

    esel1 = a.Select()
    esel1.name("llm_profile_id").label("绑定模型").clearable(True).placeholder("使用全局激活模型")
    esel1.sourceApi("/api/profiles")
    esel1.options="${profiles.map(p => ({label: p.name, value: p.id}))}"

    esw_mcp = a.Switch()
    esw_mcp.name("mcp_enabled").label("启用 MCP").description("连接 MCP 服务器提供工具能力")

    emcp_checkboxes = a.Checkboxes()
    emcp_checkboxes.name("mcp_servers").label("启用 MCP 服务器")
    emcp_checkboxes.options([
        {"label": "Github", "value": "github"},
        {"label": "Fetch", "value": "fetch"},
        {"label": "Filesystem", "value": "filesystem"},
        {"label": "Postgres", "value": "postgres"},
        {"label": "Brave Search", "value": "brave-search"},
    ])
    emcp_checkboxes.visibleOn("data.mcp_enabled == true")

    eskills_checkboxes = a.Checkboxes()
    eskills_checkboxes.name("skills").label("启用技能工具")
    eskills_checkboxes.options([
        {"label": "网页搜索", "value": "web_search"},
        {"label": "网页抓取", "value": "web_fetch"},
        {"label": "文件读取", "value": "file_read"},
        {"label": "文件写入", "value": "file_write"},
        {"label": "代码执行", "value": "code_interpreter"},
        {"label": "命令行执行", "value": "shell_exec"},
    ])

    edit_form = a.Form()
    edit_form.api("put:/api/personas/${id}")
    edit_form.initApi("get:/api/personas/${id}")
    edit_form.body([eit1, eit2, eit3, eit4, eit5, eit7, esel1, esw_enabled, esw_mcp, emcp_checkboxes, eskills_checkboxes, eit6])

    edit_dialog = a.Dialog()
    edit_dialog.title("编辑人格")
    edit_dialog.body(edit_form)

    # Actions
    activate_btn = a.Button()
    activate_btn.type("button").label("激活").level("success")
    activate_btn.actionType("ajax").api("post:/api/personas/${id}/activate")
    activate_btn.visibleOn("!data.is_active")

    edit_btn = a.Button()
    edit_btn.type("button").label("编辑").level("info")
    edit_btn.actionType("dialog").dialog(edit_dialog)

    delete_btn = a.Button()
    delete_btn.type("button").label("删除").level("danger")
    delete_btn.actionType("ajax").confirmText("确定要删除此人格吗？")
    delete_btn.api("delete:/api/personas/${id}")

    # CRUD Cards 卡片布局
    crud = a.CRUD()
    crud.api({
        "method": "get",
        "url": "/api/personas",
        "responseData": {"items": "${personas}", "total": "${personas.length}"},
    })
    crud.perPage(12)
    crud.headerToolbar(["reload", add_btn])
    crud.mode("cards")
    crud.card(
        a.Card()\
            .title("${full_name}")\
            .subTitle("${role || '通用'}")\
            .body([
                a.Tpl()\
                    .tpl("<div style=\"color: #666; font-size: 13px; margin: 8px 0;\">${description || (nickname ? nickname : '无描述')}</div>"),
                a.Flex()\
                    .className("flex justify-between items-center mt-4")\
                    .items([
                        a.Badge()\
                            .label("${enabled ? '启用' : '禁用'}")\
                            .level("${enabled ? 'success' : 'default'}"),
                        a.Badge()\
                            .label("${is_active ? '激活中' : '未激活'}")\
                            .level("${is_active ? 'primary' : 'info'}"),
                        a.Group()\
                            .buttons([edit_btn, activate_btn, delete_btn])
                    ])
            ])
    )

    page = a.Page()
    page.title("人格管理")
    page.body([crud])

    return page.to_dict()


