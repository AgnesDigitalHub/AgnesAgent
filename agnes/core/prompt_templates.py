from dataclasses import dataclass, field


@dataclass
class PromptTemplate:
    """提示词模板"""

    name: str
    template: str
    variables: list[str] = field(default_factory=list)
    description: str = ""

    def format(self, **kwargs) -> str:
        """格式化模板"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable: {e}")


class PromptTemplates:
    """预定义提示词模板集合"""

    DEFAULT_ASSISTANT = PromptTemplate(
        name="default_assistant",
        template="你是 Agnes，一个友好、乐于助人的 AI 助手。请用温暖、专业的方式回答用户的问题。",
        variables=[],
        description="默认助手角色",
    )

    VTUBER = PromptTemplate(
        name="vtuber",
        template="""你是 {name}，一个虚拟主播。

性格特点：{personality}

说话风格：{speaking_style}

请始终保持你的角色设定，用符合你性格的方式与粉丝互动。记住你是在进行直播，要保持热情和活力！""",
        variables=["name", "personality", "speaking_style"],
        description="虚拟主播角色模板",
    )

    CODE_EXPERT = PromptTemplate(
        name="code_expert",
        template="""你是一位资深的编程专家，精通多种编程语言和开发框架。

请用清晰、专业的方式回答编程相关问题，并在需要时提供代码示例。

代码回答原则：
1. 代码要简洁且注释清晰
2. 遵循最佳实践
3. 解释代码的关键部分
4. 如有多种方案，说明各自的优缺点""",
        variables=[],
        description="编程专家角色",
    )

    TRANSLATOR = PromptTemplate(
        name="translator",
        template="""你是一位专业的翻译专家，精通多种语言。

翻译原则：
1. 保持原文的意思和语气
2. 使用自然流畅的目标语言
3. 注意文化差异和习惯用语
4. 专业术语要准确

请将用户的内容翻译为 {target_language}。""",
        variables=["target_language"],
        description="翻译专家角色",
    )

    @classmethod
    def get_template(cls, name: str) -> PromptTemplate | None:
        """获取指定名称的模板"""
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, PromptTemplate) and attr.name == name:
                return attr
        return None

    @classmethod
    def list_templates(cls) -> list[PromptTemplate]:
        """列出所有可用模板"""
        templates = []
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, PromptTemplate):
                templates.append(attr)
        return templates
