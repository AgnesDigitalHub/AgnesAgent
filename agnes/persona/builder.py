"""
提示词构建器

根据 Persona 定义自动生成系统提示词
"""

from agnes.persona.core import Persona


class PromptBuilder:
    """
    系统提示词构建器

    将 Persona 定义转换为结构化的系统提示词
    """

    @classmethod
    def build(cls, persona: Persona) -> str:
        """
        构建完整系统提示词

        Args:
            persona: 角色定义

        Returns:
            str: 系统提示词
        """
        parts = []

        # 1. 身份部分
        identity_part = cls._build_identity(persona)
        if identity_part:
            parts.append(identity_part)

        # 2. 风格部分
        style_part = cls._build_style(persona)
        if style_part:
            parts.append(style_part)

        # 3. 约束部分
        constraint_part = cls._build_constraints(persona)
        if constraint_part:
            parts.append(constraint_part)

        return "\n\n".join(parts)

    @classmethod
    def _build_identity(cls, persona: Persona) -> str:
        """构建身份提示词"""
        identity = persona.identity
        parts = []

        if identity.name:
            parts.append(f"你是{identity.name}。")

        if identity.role:
            parts.append(f"你的身份是{identity.role}。")

        if identity.bio:
            parts.append(identity.bio)

        if identity.core_values:
            parts.append(f"你的核心价值观：{'、'.join(identity.core_values)}。")

        if identity.traits:
            parts.append(f"你的性格特点：{'、'.join(identity.traits)}。")

        return " ".join(parts) if parts else ""

    @classmethod
    def _build_style(cls, persona: Persona) -> str:
        """构建风格提示词"""
        style = persona.stylistics
        parts = []

        # 语气
        tone_map = {
            "friendly": "友好、亲切的语气",
            "professional": "专业、正式的语气",
            "casual": "轻松、随意的语气",
            "formal": "严肃、正式的语气",
            "neutral": "中性的语气",
        }
        if style.tone and style.tone in tone_map:
            parts.append(f"使用{tone_map[style.tone]}。")

        # 词汇
        vocab_map = {
            "simple": "简单、易懂的词汇",
            "technical": "专业、技术性的词汇",
            "literary": "文学性、富有表现力的词汇",
            "standard": "标准、通用的词汇",
        }
        if style.vocabulary and style.vocabulary in vocab_map:
            parts.append(f"使用{vocab_map[style.vocabulary]}。")

        # 句式
        structure_map = {
            "short": "简短的句子",
            "long": "完整、详细的句子",
            "varied": "长短结合的句式",
            "normal": "正常的句式",
        }
        if style.sentence_structure and style.sentence_structure in structure_map:
            parts.append(f"使用{structure_map[style.sentence_structure]}。")

        # Emoji
        if style.use_emojis:
            parts.append("可以适当使用emoji表情。")
        else:
            parts.append("不要使用emoji表情。")

        # 语体特征
        if style.language_style:
            parts.append(f"语体特征：{'、'.join(style.language_style)}。")

        return " ".join(parts) if parts else ""

    @classmethod
    def _build_constraints(cls, persona: Persona) -> str:
        """构建约束提示词"""
        constraint = persona.constraints
        parts = []

        # 禁止话题
        if constraint.forbidden_topics:
            parts.append(f"禁止讨论以下话题：{'、'.join(constraint.forbidden_topics)}。")

        # 禁止行为
        if constraint.forbidden_behaviors:
            parts.append(f"禁止以下行为：{'、'.join(constraint.forbidden_behaviors)}。")

        # 知识边界
        if constraint.knowledge_boundaries:
            parts.append(f"你的知识边界：{'、'.join(constraint.knowledge_boundaries)}。")

        # 交互守则
        if constraint.interaction_rules:
            parts.append(constraint.interaction_rules)

        return " ".join(parts) if parts else ""

    @classmethod
    def build_with_context(cls, persona: Persona, context: str) -> str:
        """
        构建带上下文的系统提示词

        Args:
            persona: 角色定义
            context: 额外上下文

        Returns:
            str: 系统提示词
        """
        base_prompt = cls.build(persona)

        if context:
            return f"{base_prompt}\n\n当前上下文：\n{context}"

        return base_prompt
