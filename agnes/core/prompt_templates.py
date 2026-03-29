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

    @classmethod
    def list_templates(cls) -> list[str]:
        """列出所有模板名称"""
        return list(cls._templates.keys())

    @classmethod
    def get_template(cls, name: str) -> "PromptTemplate | None":
        """获取指定模板"""
        return cls._templates.get(name)

    # 预定义模板
    TRANSLATOR = None
    VTUBER = None


# 初始化预定义模板
PromptTemplate.TRANSLATOR = PromptTemplate(
    name="translator",
    template="你是一个专业的翻译助手。请将以下内容翻译成{target_language}",
    variables=["target_language"],
    description="翻译模板",
)

PromptTemplate.VTUBER = PromptTemplate(
    name="vtuber",
    template="你是一个虚拟主播{name}。请用可爱的语气回复粉丝的留言：\n\n{message}",
    variables=["name", "message"],
    description="VTuber模板",
)

# 默认助手模板
default_assistant = PromptTemplate(
    name="default_assistant",
    template="你是一个有用的AI助手。请用简洁明了的语言回答问题。",
    variables=[],
    description="默认助手模板",
)

# 将模板添加到类的模板字典中
PromptTemplate._templates = {
    "default_assistant": default_assistant,
    "translator": PromptTemplate.TRANSLATOR,
    "vtuber": PromptTemplate.VTUBER,
}
