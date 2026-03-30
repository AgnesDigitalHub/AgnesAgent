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

    # 供应商默认配置映射
    provider_defaults = {
        "openai": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o"},
        "openai-compat": {"base_url": "http://localhost:8000/v1", "model": ""},
        "deepseek": {"base_url": "https://api.deepseek.com", "model": "deepseek-chat"},
        "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta", "model": "gemini-pro"},
        "anthropic": {"base_url": "https://api.anthropic.com", "model": "claude-3-sonnet-20240229"},
        "ollama": {"base_url": "http://localhost:11434/v1", "model": "llama3"},
        "openvino-server": {"base_url": "http://localhost:8000/v1", "model": ""},
        "generic": {"base_url": "http://localhost:8000/v1", "model": ""},
    }

    # Create add dialog form fields - 简化版本：只选择供应商
    sel1 = a.Select()
    sel1.name("provider").label("AI 供应商").required(True).options(provider_options).description(
        "选择供应商后将自动创建配置，创建后可编辑详细信息"
    )

    # 自动生成的 ID（隐藏，自动填充）
    it1 = a.Hidden()
    it1.name("name")

    # 隐藏的 model 字段（根据供应商自动填充）
    sel_model = a.Hidden()
    sel_model.name("model")
    sel_model.id("add_model")

    # base_url 字段（隐藏，根据供应商自动填充）
    it4 = a.Hidden()
    it4.name("base_url")

    # api_key 字段（隐藏）
    ipw = a.Hidden()
    ipw.name("api_key")
    ipw.value("")

    it2 = a.Hidden()
    it2.name("description")
    it2.value("")

    inn1 = a.Hidden()
    inn1.name("temperature")
    inn1.value(0.7)

    inn2 = a.Hidden()
    inn2.name("max_tokens")
    inn2.value(None)

    # 简化的表单
    add_form = a.Form()
    add_form.api("post:/api/profiles")
    add_form.body([sel1, it1, sel_model, it4, ipw, it2, inn1, inn2]).redirectText("创建成功").messages(
        {"success": "创建成功", "failed": "创建失败"}
    )

    # 生成唯一ID
    add_form.watch(
        "provider",
        {
            "actions": [
                {
                    "actionType": "ajax",
                    "args": {
                        "api": {
                            "method": "post",
                            "url": "/api/profiles/generate-id",
                            "data": {"provider": "${provider}"},
                        }
                    },
                    "outputVar": "generatedId",
                },
                {
                    "actionType": "setValue",
                    "componentId": "add_name",
                    "args": {"value": "${generatedId.id}"},
                },
            ]
        },
    )

    # 给隐藏字段添加 id 以便 watch 中引用
    it4.id("add_base_url")
    it1.id("add_name")

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
    eit1.name("name").label("ID / 唯一名称").required(True).description("用于识别此配置的唯一名称")

    eit2 = a.InputText()
    eit2.name("description").label("描述")

    esel1 = a.Select()
    esel1.name("provider").label("AI 供应商").required(True).options(provider_options)

    # 基础配置 - 根据供应商自动填充
    eit4 = a.InputText()
    eit4.name("base_url").label("API Base URL").value("${base_url}").description("API服务器地址")

    eipw = a.InputPassword()
    eipw.name("api_key").label("API Key").value("${api_key}").description("API密钥（可选）").visibleOn(
        "provider !== 'ollama' && provider !== 'openvino-server'"
    )

    # 获取模型按钮（编辑模式）
    e_fetch_btn = a.Button()
    e_fetch_btn.label("刷新可用模型").level("primary").size("sm")
    e_fetch_btn.actionType("ajax")
    e_fetch_btn.api(
        {
            "method": "post",
            "url": "/api/profiles/fetch-models",
            "data": {"provider": "${provider}", "base_url": "${base_url}", "api_key": "${api_key}"},
        }
    )
    e_fetch_btn.onEvent(
        "success",
        {
            "actions": [
                {
                    "actionType": "setValue",
                    "componentId": "edit_model_checkboxes",
                    "args": {"value": "${event.data.models}"},
                }
            ]
        },
    )

    # 模型多选列表（Checkboxes形式）
    e_model_checkboxes = a.Checkboxes()
    e_model_checkboxes.name("enabled_models").label("可用模型").id("edit_model_checkboxes")
    e_model_checkboxes.description("选择要启用的模型，可多选")
    e_model_checkboxes.inline(False)  # 垂直排列
    e_model_checkboxes.columns(1)  # 单列显示

    # 高级参数
    einn1 = a.InputNumber()
    einn1.name("temperature").label("Temperature").min(0).max(2).step(0.1)

    einn2 = a.InputNumber()
    einn2.name("max_tokens").label("Max Tokens").value(128).description("单位：K (1000 tokens)")

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
    e_model_group.body(
        [
            a.Html().html('<p style="color: #666; margin-bottom: 10px;">填写完成后点击按钮刷新模型列表</p>'),
            e_fetch_btn,
            e_model_checkboxes,
        ]
    )

    e_advanced_group = a.Group()
    e_advanced_group.label("高级配置")
    e_advanced_group.body([einn1, einn2])

    edit_form = a.Form()
    edit_form.api("put:/api/profiles/${id}")
    edit_form.initApi("get:/api/profiles/${id}")
    edit_form.body([e_basic_group, e_connection_group, e_model_group, e_advanced_group])

    edit_dialog = a.Dialog()
    edit_dialog.title("编辑配置")
    edit_dialog.size("md")
    edit_dialog.body(edit_form)

    # Actions
    edit_btn = a.Button()
    edit_btn.type("button").label("编辑").level("info").size("sm")
    edit_btn.actionType("dialog").dialog(edit_dialog)

    delete_btn = a.Button()
    delete_btn.type("button").label("删除").level("danger").size("sm")
    delete_btn.actionType("ajax").confirmText("确定要删除此配置吗？")
    delete_btn.api("delete:/api/profiles/${id}")

    # CRUD Cards 卡片布局
    crud = a.CRUD()
    crud.api(
        {
            "method": "get",
            "url": "/api/profiles",
            "responseData": {"items": "${profiles}", "total": "${profiles.length}"},
        }
    )
    crud.perPage(12)
    crud.headerToolbar(["reload", add_btn])
    crud.mode("cards")
    crud.card(
        a.Card()
        .title("${name}")
        .subTitle("${provider}")
        .body(
            a.Tpl().tpl(
                '<div class="flex flex-col gap-2">'
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<span style="color: #666; font-size: 12px;">ID:</span>'
                '<code style="background: #f0f0f0; padding: 2px 6px; border-radius: 4px; font-size: 12px;">${name}</code>'
                "</div>"
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<span style="color: #666; font-size: 12px;">模型:</span>'
                "<span style=\"font-size: 12px;\">${model || '未配置'}</span>"
                "</div>"
                "<div style=\"color: #999; font-size: 12px; margin-top: 4px;\">${description || '无描述'}</div>"
                "</div>"
            )
        )
        .actions([edit_btn, delete_btn])
    )

    page = a.Page()
    page.title("模型管理")
    page.body([crud])

    return page.to_dict()
