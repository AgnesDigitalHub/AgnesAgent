"""
Skill 调试器页面 Schema
在线调试本地 Skill 和 YAML 定义的 Skill
"""

from amis.components.Alert import Alert
from amis.components.Button import Button
from amis.components.Card import Card
from amis.components.JSONEditorControl import JSONEditorControl
from amis.components.Page import Page
from amis.components.Table import Table
from amis.components.Tabs import Tabs
from amis.components.Tpl import Tpl


def get_skill_schema():
    """获取 Skill 调试器页面 amis Schema"""

    # 说明提示 - 使用 Alert 组件
    info_alert = (
        Alert()
        .title("使用说明")
        .body("在这里可以在线调试 Skill，输入参数并立即查看执行结果。支持原生 Skill 和 YAML 定义的 Skill。")
        .level("info")
        .to_dict()
    )

    # ============ Skill 选择信息卡片 ============
    info_card_content = (
        Tpl()
        .tpl("""
        <div class="text-muted text-center p-md">
            ${selectedSkill ? '' : '请从下方选择一个 Skill'}
        </div>
        <div>
            <h3>${selectedSkill.name}</h3>
            <p class="text-muted">${selectedSkill.description}</p>
            <dl class="dl-horizontal">
                <dt>分类</dt>
                <dd>${selectedSkill.category}</dd>
                <dt>版本</dt>
                <dd>${selectedSkill.version}</dd>
                <dt>标签</dt>
                <dd>
                    ${selectedSkill.tags.map(tag => `<span class="label label-info m-r-xs">${tag}</span>`).join('')}
                </dd>
            </dl>
        </div>
        """)
        .to_dict()
    )

    info_card = Card().title("选择 Skill").body([info_card_content]).to_dict()

    # ============ 已注册 Skill 列表 ============
    skill_table = (
        Table()
        .source("get:/api/skills/list")
        .columns(
            [
                {
                    "name": "name",
                    "label": "名称",
                    "type": "link",
                    "linkAction": {"actionType": "custom", "script": "window.setSelectedSkill(item)"},
                },
                {"name": "category", "label": "分类", "type": "text"},
                {"name": "source", "label": "来源", "type": "badge"},
            ]
        )
        .autoGenerateFilter(False)
        .to_dict()
    )

    list_card = Card().title("已注册 Skill 列表").body([skill_table]).to_dict()

    # ============ 参数输入 ============
    # 参数输入 JSON Editor
    json_editor = (
        JSONEditorControl().name("parameters").label("").placeholder('{"param1": "value1"}').value({}).to_dict()
    )
    # 修正 type - python-amis 对 JSONEditorControl 过度转换
    json_editor["type"] = "json-editor"

    # 执行按钮
    exec_button = (
        Button()
        .label("执行 Skill")
        .level("primary")
        .icon("fa fa-play")
        .actionType("ajax")
        .api("post:/api/skills/execute/${selectedSkill.name}")
        .data({"parameters": "${parameters}"})
        .messages({"success": "执行完成"})
        .onSuccess("setResult(event.data.result)")
        .to_dict()
    )

    # 上传按钮
    upload_button = (
        Button()
        .label("上传 Skills")
        .level("success")
        .icon("fa fa-upload")
        .actionType("dialog")
        .dialog(
            {
                "title": "上传 Skills 压缩包",
                "body": {
                    "type": "form",
                    "api": "post:/api/skills/upload",
                    "messages": {"success": "上传成功", "failed": "上传失败"},
                    "body": [
                        {
                            "type": "input-file",
                            "name": "file",
                            "label": "选择 zip 文件",
                            "accept": ".zip",
                            "required": True,
                            "description": "请上传包含 .yaml 或 .yml 文件的 zip 压缩包",
                        }
                    ],
                },
            }
        )
        .to_dict()
    )

    # 参数卡片
    param_card = (
        Card()
        .title("参数输入 (JSON)")
        .className("m-t-md")
        .body([json_editor, {"type": "wrapper", "className": "m-t-md", "body": [exec_button]}])
        .to_dict()
    )

    # ============ 结果展示 ============
    result_custom = (
        Tpl()
        .tpl("""
        <div class="text-muted text-center p-md">
            ${result ? '' : '尚未执行'}
        </div>
        <div>
            <div class="alert alert-${result.success ? 'success' : 'danger'}">
                <strong>${result.success ? '执行成功' : '执行失败'}</strong>
                <div class="m-t-sm">${result.error_message}</div>
            </div>
            <dl class="dl-horizontal m-t-md">
                <dt>执行耗时</dt>
                <dd>${result.execution_time_ms.toFixed(2)} ms</dt>
            </dl>
            <div>
                <h4>返回数据</h4>
                <pre>${JSON.stringify(result.data, null, 2)}</pre>
            </div>
        </div>
        """)
        .to_dict()
    )

    result_tabs = (
        Tabs()
        .tabs(
            [
                {"title": "JSON 输出", "body": {"type": "json", "value": "${result}", "muteJSON": False}},
                {"title": "格式化查看", "body": result_custom},
            ]
        )
        .to_dict()
    )

    result_card = Card().title("执行结果").className("m-t-md").body([result_tabs]).to_dict()

    # 组合成完整页面 - 简单垂直布局，避免未知渲染器错误
    page = (
        Page()
        .title("Skill 调试器")
        .toolbar([upload_button])
        .body(
            [
                info_alert,
                {"type": "wrapper", "className": "m-t-md", "body": [info_card, list_card, param_card, result_card]},
            ]
        )
    )
    return page.to_dict()
