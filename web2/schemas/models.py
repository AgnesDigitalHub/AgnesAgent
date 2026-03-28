"""
模型管理页面 Schema - 使用 python-amis 构建
"""

from amis.amis import amis


def get_models_schema():
    """获取模型管理页面 amis Schema"""
    a = amis()
    
    # 主流 AI 供应商列表
    provider_options = [
        {"label": "OpenAI", "value": "openai"},
        {"label": "OpenAI 兼容（Azure / 第三方代理）", "value": "openai-compat"},
        {"label": "DeepSeek", "value": "deepseek"},
        {"label": "Google Gemini", "value": "gemini"},
        {"label": "Anthropic Claude", "value": "anthropic"},
        {"label": "Ollama", "value": "ollama"},
        {"label": "OpenVINO Server", "value": "openvino-server"},
        {"label": "其他（通用 API）", "value": "generic"},
    ]
    
    # Create add dialog form fields
    # 第一步：选择供应商
    it1 = a.InputText()
    it1.name("name").label("ID / 唯一名称").required(True)\
        .description("用于识别此配置的唯一名称，例如：openai-gpt-4o")

    it2 = a.InputText()
    it2.name("description").label("描述")

    sel1 = a.Select()
    sel1.name("provider").label("AI 供应商").required(True)\
        .options(provider_options)\
        .description("选择 AI 供应商后将自动填充默认配置")

    # 基础配置 - 根据供应商自动填充
    it4 = a.InputText()
    it4.name("base_url").label("API Base URL")\
        .placeholder("留空使用供应商默认地址")

    ipw = a.InputPassword()
    ipw.name("api_key").label("API Key")\
        .visibleOn("provider !== 'ollama' && provider !== 'openvino-server'")

    # 模型选择：先让用户填好供应商和认证信息，然后点击获取模型列表
    fetch_btn = a.Button()
    fetch_btn.label("获取可用模型").level("primary").size("sm")
    fetch_btn.actionType("ajax")
    fetch_btn.api({
        "method": "post",
        "url": "/api/profiles/fetch-models",
        "data": {
            "provider": "${provider}",
            "base_url": "${base_url}",
            "api_key": "${api_key}"
        }
    })
    # 请求成功后把 models 选项设置到 model 下拉框
    fetch_btn.onEvent("success", {
        "actions": [
            {
                "actionType": "setValue",
                "componentName": "model_select",
                "args": {
                    "value": "${event.data.models}"
                }
            }
        ]
    })

    # 模型下拉选择框，动态加载，获取后选择
    sel_model = a.Select()
    sel_model.name("model").label("选择模型").required(True)\
        .id("model_select")\
        .options([])\
        .clearable(True)\
        .placeholder("请先填写供应商信息并点击'获取可用模型'")

    # 高级参数区域 - 对大多数供应商都显示
    inn1 = a.InputNumber()
    inn1.name("temperature").label("Temperature").value(0.7).min(0).max(2).step(0.1)

    inn2 = a.InputNumber()
    inn2.name("max_tokens").label("Max Tokens")\
        .description("最大生成 token 数，留空使用默认值")

    # 组织表单：分组更清晰
    basic_group = a.Group()
    basic_group.label("基础配置")
    basic_group.body([sel1, it1, it2])
    
    connection_group = a.Group()
    connection_group.label("连接配置")
    connection_group.body([it4, ipw])
    
    # 模型选择分组
    model_group = a.Group()
    model_group.label("模型选择")
    model_group.body([
        a.Html().html('<p style="color: #666; margin-bottom: 10px;">填写供应商和认证信息后，点击按钮获取可用模型列表，然后选择模型</p>'),
        fetch_btn,
        sel_model
    ])
    
    advanced_group = a.Group()
    advanced_group.label("高级配置")
    advanced_group.body([inn1, inn2])

    add_form = a.Form()
    add_form.api("post:/api/profiles")
    add_form.body([basic_group, connection_group, model_group, advanced_group])\
        .redirectText("创建成功")\
        .messages({"success": "创建成功", "failed": "创建失败"})

    # 使用 setDefault 自动填充供应商默认值
    # 当供应商选择变化时，自动填充 base_url
    add_form.watch("provider", {
        "type": "setValue",
        "value": "${provider === 'openai' ? 'https://api.openai.com/v1' : provider === 'deepseek' ? 'https://api.deepseek.com' : provider === 'gemini' ? 'https://generativelanguage.googleapis.com/v1beta' : provider === 'anthropic' ? 'https://api.anthropic.com' : provider === 'ollama' ? 'http://localhost:11434/v1' : provider === 'openvino-server' ? 'http://localhost:8000/v1' : ''}"
    })

    add_dialog = a.Dialog()
    add_dialog.title("新增模型配置")
    add_dialog.size("md")
    add_dialog.body(add_form)

    add_btn = a.Button()
    add_btn.type("button").label("新增配置").level("primary")
    add_btn.actionType("dialog").dialog(add_dialog)

    # Edit dialog
    # 第一步：选择供应商
    eit1 = a.InputText()
    eit1.name("name").label("ID / 唯一名称").required(True)\
        .description("用于识别此配置的唯一名称")

    eit2 = a.InputText()
    eit2.name("description").label("描述")

    esel1 = a.Select()
    esel1.name("provider").label("AI 供应商").required(True)\
        .options(provider_options)

    # 基础配置 - 根据供应商自动填充
    eit4 = a.InputText()
    eit4.name("base_url").label("API Base URL")

    eipw = a.InputPassword()
    eipw.name("api_key").label("API Key")\
        .visibleOn("provider !== 'ollama' && provider !== 'openvino-server'")

    # 获取模型按钮（编辑模式）
    e_fetch_btn = a.Button()
    e_fetch_btn.label("刷新可用模型").level("primary").size("sm")
    e_fetch_btn.actionType("ajax")
    e_fetch_btn.api({
        "method": "post",
        "url": "/api/profiles/fetch-models",
        "data": {
            "provider": "${provider}",
            "base_url": "${base_url}",
            "api_key": "${api_key}"
        }
    })
    e_fetch_btn.onEvent("success", {
        "actions": [
            {
                "actionType": "setValue",
                "componentName": "edit_model_select",
                "args": {
                    "value": "${event.data.models}"
                }
            }
        ]
    })

    # 模型下拉选择框
    e_sel_model = a.Select()
    e_sel_model.name("model").label("选择模型").required(True)\
        .id("edit_model_select")\
        .options([])\
        .clearable(True)\
        .placeholder("请先填写供应商信息并点击'获取可用模型'")

    # 高级参数
    einn1 = a.InputNumber()
    einn1.name("temperature").label("Temperature").min(0).max(2).step(0.1)

    einn2 = a.InputNumber()
    einn2.name("max_tokens").label("Max Tokens")

    # 分组编辑表单
    e_basic_group = a.Group()
    e_basic_group.label("基础配置")
    e_basic_group.body([esel1, eit1, eit2])
    
    e_connection_group = a.Group()
    e_connection_group.label("连接配置")
    e_connection_group.body([eit4, eipw])
    
    # 模型选择分组
    e_model_group = a.Group()
    e_model_group.label("模型选择")
    e_model_group.body([
        a.Html().html('<p style="color: #666; margin-bottom: 10px;">填写完成后点击按钮刷新模型列表</p>'),
        e_fetch_btn,
        e_sel_model
    ])
    
    e_advanced_group = a.Group()
    e_advanced_group.label("高级配置")
    e_advanced_group.body([einn1, einn2])

    edit_form = a.Form()
    edit_form.api("put:/api/profiles/${id}")
    edit_form.initApi("get:/api/profiles/${id}")
    edit_form.body([e_basic_group, e_connection_group, e_model_group, e_advanced_group])

    # 同样支持自动填充
    edit_form.watch("provider", {
        "type": "setValue",
        "value": "${provider === 'openai' ? 'https://api.openai.com/v1' : provider === 'deepseek' ? 'https://api.deepseek.com' : provider === 'gemini' ? 'https://generativelanguage.googleapis.com/v1beta' : provider === 'anthropic' ? 'https://api.anthropic.com' : provider === 'ollama' ? 'http://localhost:11434/v1' : provider === 'openvino-server' ? 'http://localhost:8000/v1' : ''}"
    })

    edit_dialog = a.Dialog()
    edit_dialog.title("编辑配置")
    edit_dialog.size("md")
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

    # CRUD Cards 卡片布局
    crud = a.CRUD()
    crud.api({
        "method": "get",
        "url": "/api/profiles",
        "responseData": {"items": "${profiles}", "total": "${profiles.length}"},
    })
    crud.perPage(12)
    crud.headerToolbar(["reload", add_btn])
    crud.mode("cards")
    crud.card(
        a.Card()\
            .title("${name}")\
            .subTitle("${provider} - ${model}")\
            .body([
                a.Tpl()\
                    .tpl("<div style=\"color: #999; font-size: 13px; margin: 8px 0;\">${description || '无描述'}</div>"),
                a.Flex()\
                    .className("flex justify-between items-center mt-4")\
                    .items([
                        a.Badge()\
                            .label("${is_active ? '激活中' : '未激活'}")\
                            .level("${is_active ? 'success' : 'info'}"),
                        a.Group()\
                            .buttons([edit_btn, activate_btn, delete_btn])
                    ])
            ])
    )

    page = a.Page()
    page.title("模型管理")
    page.body([crud])

    return page.to_dict()
