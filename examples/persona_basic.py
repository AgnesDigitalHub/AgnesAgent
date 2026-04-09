"""
Persona 系统使用示例
演示如何使用 Agnes Persona 定义角色
"""

import asyncio

from agnes.persona import Persona, PersonaLoader, PromptBuilder
from agnes.persona.core import PersonaTemplates


def basic_persona():
    """基础角色创建"""
    print("=" * 60)
    print("基础角色创建")
    print("=" * 60)

    # 使用模板
    expert = PersonaTemplates.expert()
    print(f"模板角色: {expert.name}")
    print(f"描述: {expert.description}")

    # 生成系统提示词
    prompt = expert.get_effective_system_prompt()
    print(f"\n生成的系统提示词:\n{prompt[:200]}...")


def custom_persona():
    """自定义角色"""
    print("\n" + "=" * 60)
    print("自定义角色")
    print("=" * 60)

    from agnes.persona.core import PersonaIdentity, PersonaStylistics, PersonaConstraints

    # 创建自定义角色
    custom = Persona(
        id="my_assistant",
        name="小助手",
        description="我的专属助手",
        identity=PersonaIdentity(
            name="小助手",
            role="个人助理",
            bio="我是你的专属助手，了解你的喜好和习惯。",
            traits=["贴心", "高效", "可靠"],
        ),
        stylistics=PersonaStylistics(
            tone="friendly",
            use_emojis=True,
        ),
        constraints=PersonaConstraints(
            interaction_rules="优先理解用户意图，提供简洁有用的回答。",
        ),
    )

    print(f"自定义角色: {custom.name}")
    print(f"系统提示词:\n{custom.get_effective_system_prompt()}")


async def with_agent():
    """与 Agent 结合使用"""
    print("\n" + "=" * 60)
    print("与 Agent 结合")
    print("=" * 60)

    from agnes.core import Agent
    from agnes.persona.core import PersonaTemplates

    # 创建带角色的 Agent（这里使用 mock，实际需要 LLM provider）
    persona = PersonaTemplates.concise()

    print(f"创建带角色的 Agent: {persona.name}")
    print(f"系统提示词:\n{persona.get_effective_system_prompt()}")

    # 实际使用：
    # llm = OpenAIProvider(api_key="...")
    # agent = Agent.create(llm, persona=persona)
    # response = await agent.run("你好")


def save_and_load():
    """保存和加载角色"""
    print("\n" + "=" * 60)
    print("保存和加载角色")
    print("=" * 60)

    import tempfile
    import os

    # 创建角色
    persona = PersonaTemplates.creative()

    # 保存到临时文件
    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_path = os.path.join(tmpdir, "creative.yaml")

        # 保存
        PersonaLoader.save_to_yaml(persona, yaml_path)
        print(f"保存到: {yaml_path}")

        # 加载
        loaded = PersonaLoader.from_yaml(yaml_path)
        print(f"加载成功: {loaded.name}")
        print(f"描述: {loaded.description}")


def main():
    """运行所有示例"""
    basic_persona()
    custom_persona()

    # 异步示例
    asyncio.run(with_agent())

    save_and_load()

    print("\n" + "=" * 60)
    print("所有示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
