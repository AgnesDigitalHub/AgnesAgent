"""
设置页面 schema
演示如何使用 python-amis Pydantic 模型构建 schema
"""

from amis.components.Page import Page
from amis.components.Form import Form
from amis.components.InputText import InputText
from amis.components.InputNumber import InputNumber
from amis.components.Textarea import Textarea
from amis.components.Switch import Switch
from amis.components.Button import Button
from amis.components.Plain import Plain
from amis.components.Static import Static


def get_settings_schema() -> dict:
    """
    使用 python-amis Pydantic 模型构建设置页面 schema
    返回的 dict 会直接嵌入 App 配置的 pages 中
    """

    # 系统设置表单
    form = Form().api("/api/settings/save").initApi("/api/settings/get")\
        .body([
            Plain()\
                .value("<div class='m-b-xl'><h3>基本设置</h3></div>"),

            InputText()\
                .name("site_name")\
                .label("网站名称")\
                .value("Agents Dashboard"),

            InputText()\
                .name("site_description")\
                .label("网站描述"),

            Textarea()\
                .name("site_intro")\
                .label("网站介绍"),

            Plain()\
                .value("<div class='m-t-xl m-b-xl'><h3>LLM 设置</h3></div>"),

            InputText()\
                .name("openai_api_key")\
                .label("OpenAI API Key")\
                .type("password"),

            InputText()\
                .name("openai_base_url")\
                .label("OpenAI Base URL"),

            InputNumber()\
                .name("max_tokens")\
                .label("最大 Token 数")\
                .value(4096)\
                .min(1024)\
                .max(16384),

            Plain()\
                .value("<div class='m-t-xl m-b-xl'><h3>功能开关</h3></div>"),

            Switch()\
                .name("enable_registration")\
                .label("允许注册")\
                .value(True),

            Switch()\
                .name("enable_analytics")\
                .label("启用统计")\
                .value(False),

            Switch()\
                .name("debug_mode")\
                .label("调试模式")\
                .value(False),

            Button()\
                .type("submit")\
                .label("保存设置")\
                .primary(True),
        ])

    # 组合成完整页面
    page = Page()\
        .title("系统设置")\
        .body([form])

    # 转换为 dict
    return page.to_dict()