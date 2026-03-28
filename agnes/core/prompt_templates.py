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
