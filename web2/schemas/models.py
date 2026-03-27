"""
模型管理页面 Schema - 使用 python-amis 构建
"""

from amis.amis import amis


def get_models_schema():
    """获取模型管理页面 amis Schema"""
    a = amis()
    
    # Create add dialog form fields
    it1 = a.InputText()
    it1.name("name").label("名称").required(True)

    it2 = a.InputText()
    it2.name("description").label("描述")

    sel1 = a.Select()
    sel1.name("provider").label("Provider").required(True)
    sel1.options([
        {"label": "OpenAI", "value": "openai"},
        {"label": "Ollama", "value": "ollama"},
        {"label": "OpenVINO Server", "value": "openvino-server"},
        {"label": "其他本地模型", "value": "local-api"},
    ])

    it3 = a.InputText()
    it3.name("model").label("Model").required(True)

    it4 = a.InputText()
    it4.name("base_url").label("Base URL")

    ipw = a.InputPassword()
    ipw.name("api_key").label("API Key")

    inn1 = a.InputNumber()
    inn1.name("temperature").label("Temperature").value(0.7).min(0).max(2).step(0.1)

    inn2 = a.InputNumber()
    inn2.name("max_tokens").label("Max Tokens")

    add_form = a.Form()
    add_form.api("post:/api/profiles")
    add_form.body([it1, it2, sel1, it3, it4, ipw, inn1, inn2])

    add_dialog = a.Dialog()
    add_dialog.title("新增模型配置")
    add_dialog.body(add_form)

    add_btn = a.Button()
    add_btn.type("button").label("新增配置").level("primary")
    add_btn.actionType("dialog").dialog(add_dialog)

    # Edit dialog
    eit1 = a.InputText()
    eit1.name("name").label("名称").required(True)

    eit2 = a.InputText()
    eit2.name("description").label("描述")

    esel1 = a.Select()
    esel1.name("provider").label("Provider").required(True)
    esel1.options([
        {"label": "OpenAI", "value": "openai"},
        {"label": "Ollama", "value": "ollama"},
        {"label": "OpenVINO Server", "value": "openvino-server"},
        {"label": "其他本地模型", "value": "local-api"},
    ])

    eit3 = a.InputText()
    eit3.name("model").label("Model").required(True)

    eit4 = a.InputText()
    eit4.name("base_url").label("Base URL")

    eipw = a.InputPassword()
    eipw.name("api_key").label("API Key")

    einn1 = a.InputNumber()
    einn1.name("temperature").label("Temperature").min(0).max(2).step(0.1)

    einn2 = a.InputNumber()
    einn2.name("max_tokens").label("Max Tokens")

    edit_form = a.Form()
    edit_form.api("put:/api/profiles/${id}")
    edit_form.initApi("get:/api/profiles/${id}")
    edit_form.body([eit1, eit2, esel1, eit3, eit4, eipw, einn1, einn2])

    edit_dialog = a.Dialog()
    edit_dialog.title("编辑配置")
    edit_dialog.body(edit_form)

    # Actions
    activate_btn = a.Button()
    activate_btn.type("button").label("激活").level("success")
    activate_btn.actionType("ajax").api("post:/api/profiles/${id}/activate")
    activate_btn.visibleOn("!data.is_active")

    edit_btn = a.Button()
    edit_btn.type("button").label("编辑").level("info")
    edit_btn.actionType("dialog").dialog(edit_dialog)

    delete_btn = a.Button()
    delete_btn.type("button").label("删除").level("danger")
    delete_btn.actionType("ajax").confirmText("确定要删除此配置吗？")
    delete_btn.api("delete:/api/profiles/${id}")

    # CRUD
    crud = a.CRUD()
    crud.api({
        "method": "get",
        "url": "/api/profiles",
        "responseData": {"items": "${profiles}", "total": "${profiles.length}"},
    })
    crud.perPage(10)
    crud.headerToolbar(["reload", add_btn])
    crud.columns([
        {"name": "name", "label": "名称", "type": "text"},
        {"name": "provider", "label": "Provider", "type": "tag"},
        {"name": "model", "label": "Model", "type": "text"},
        {
            "name": "is_active",
            "label": "状态",
            "type": "mapping",
            "map": {
                "True": {"label": "激活中", "level": "success"},
                "False": {"label": "未激活", "level": "info"},
            },
        },
        {"name": "updated_at", "label": "更新时间", "type": "datetime"},
    ])
    crud.itemActions([activate_btn, edit_btn, delete_btn])

    page = a.Page()
    page.title("模型管理")
    page.body([crud])

    return page.to_dict()
