"""
Skill 调试器页面 Schema - 直接使用字典构建，不依赖 amis-python
在线调试本地 Skill 和 YAML 定义的 Skill
"""


def get_skill_schema() -> dict:
    """获取 Skill 调试器页面 amis Schema"""
    return {
        "type": "page",
        "title": "Skill 调试器",
        "toolbar": [
            {
                "type": "button",
                "label": "上传 Skills",
                "level": "success",
                "icon": "fa fa-upload",
                "actionType": "dialog",
                "dialog": {
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
                },
            }
        ],
        "body": [
            {
                "type": "alert",
                "title": "使用说明",
                "body": "在这里可以在线调试 Skill，输入参数并立即查看执行结果。支持原生 Skill 和 YAML 定义的 Skill。",
                "level": "info",
            },
            {
                "type": "wrapper",
                "className": "m-t-md",
                "body": [
                    {
                        "type": "card",
                        "title": "选择 Skill",
                        "body": [
                            {
                                "type": "tpl",
                                "tpl": """
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
                                """,
                            }
                        ],
                    },
                    {
                        "type": "card",
                        "title": "已注册 Skill 列表",
                        "body": [
                            {
                                "type": "table",
                                "source": "get:/api/skills/list",
                                "columns": [
                                    {
                                        "name": "name",
                                        "label": "名称",
                                        "type": "link",
                                        "linkAction": {
                                            "actionType": "custom",
                                            "script": "window.setSelectedSkill(item)",
                                        },
                                    },
                                    {"name": "category", "label": "分类", "type": "text"},
                                    {"name": "source", "label": "来源", "type": "badge"},
                                ],
                                "autoGenerateFilter": False,
                            }
                        ],
                    },
                    {
                        "type": "card",
                        "title": "参数输入 (JSON)",
                        "className": "m-t-md",
                        "body": [
                            {
                                "type": "json-editor",
                                "name": "parameters",
                                "label": "",
                                "placeholder": '{"param1": "value1"}',
                                "value": {},
                            },
                            {
                                "type": "wrapper",
                                "className": "m-t-md",
                                "body": [
                                    {
                                        "type": "button",
                                        "label": "执行 Skill",
                                        "level": "primary",
                                        "icon": "fa fa-play",
                                        "actionType": "ajax",
                                        "api": "post:/api/skills/execute/${selectedSkill.name}",
                                        "data": {"parameters": "${parameters}"},
                                        "messages": {"success": "执行完成"},
                                        "onSuccess": "setResult(event.data.result)",
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "type": "card",
                        "title": "执行结果",
                        "className": "m-t-md",
                        "body": [
                            {
                                "type": "tabs",
                                "tabs": [
                                    {
                                        "title": "JSON 输出",
                                        "body": {"type": "json", "value": "${result}", "muteJSON": False},
                                    },
                                    {
                                        "title": "格式化查看",
                                        "body": {
                                            "type": "tpl",
                                            "tpl": """
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
                                                    <dd>${result.execution_time_ms.toFixed(2)} ms</dd>
                                                </dl>
                                                <div>
                                                    <h4>返回数据</h4>
                                                    <pre>${JSON.stringify(result.data, null, 2)}</pre>
                                                </div>
                                            </div>
                                            """,
                                        },
                                    },
                                ],
                            }
                        ],
                    },
                ],
            },
        ],
    }
