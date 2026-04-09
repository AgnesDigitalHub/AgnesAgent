"""
Agent 基础使用示例
演示如何使用 Agnes Agent 进行对话和工具调用
"""

import asyncio
import os

from agnes.core import Agent, AgentConfig
from agnes.providers.openai import OpenAIProvider


async def basic_chat():
    """基础对话示例"""
    # 创建 LLM Provider
    llm = OpenAIProvider(
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key"),
        model="gpt-3.5-turbo",
    )

    # 使用模板创建 Agent
    agent = Agent.create(llm, template="default")

    # 简单对话
    response = await agent.run("你好，请介绍一下自己")
    print(f"Agent: {response.content}")
    print(f"成功: {response.success}")


async def with_callbacks():
    """带回调的 Agent 示例"""
    llm = OpenAIProvider(
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key"),
        model="gpt-3.5-turbo",
    )

    agent = Agent.create(llm, template="coder")

    # 注册回调
    def on_step(step):
        print(f"[步骤] {step.step_type.name}: {step.content[:50]}...")

    def on_tool_call(name, params):
        print(f"[工具调用] {name}({params})")

    def on_tool_result(result):
        print(f"[工具结果] 成功={result.success}")

    agent.on_step(on_step).on_tool_call(on_tool_call).on_tool_result(on_tool_result)

    # 运行
    response = await agent.run("计算 123 * 456")
    print(f"\n最终答案: {response.content}")


async def stream_chat():
    """流式对话示例"""
    llm = OpenAIProvider(
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key"),
        model="gpt-3.5-turbo",
    )

    agent = Agent.create(llm, template="default")

    print("Agent: ", end="", flush=True)
    async for token in agent.run_stream("讲一个短故事"):
        print(token, end="", flush=True)
    print()


async def custom_config():
    """自定义配置示例"""
    llm = OpenAIProvider(
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key"),
        model="gpt-4",
    )

    # 从文件加载配置
    config = AgentConfig.from_dict(
        {
            "name": "custom_assistant",
            "description": "自定义助手",
            "capabilities": {
                "function_calling": True,
                "multi_step": True,
                "max_steps": 20,
            },
            "behavior": {
                "temperature": 0.5,
                "system_prompt": "你是一个专业的数据分析助手。",
            },
        }
    )

    agent = Agent(llm=llm, config=config)

    response = await agent.run("分析以下数据: [1, 2, 3, 4, 5]")
    print(f"结果: {response.content}")


async def multi_turn_chat():
    """多轮对话示例"""
    llm = OpenAIProvider(
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key"),
        model="gpt-3.5-turbo",
    )

    agent = Agent.create(llm, template="default")

    # 第一轮
    r1 = await agent.run("我叫张三")
    print(f"Agent: {r1.content}")

    # 第二轮（应该记住名字）
    r2 = await agent.run("我叫什么名字？")
    print(f"Agent: {r2.content}")

    # 查看历史
    history = agent.get_history()
    print(f"\n对话历史 ({len(history)} 条消息)")


async def main():
    """运行所有示例"""
    print("=" * 60)
    print("Agnes Agent 基础示例")
    print("=" * 60)

    examples = [
        ("基础对话", basic_chat),
        ("带回调", with_callbacks),
        ("流式对话", stream_chat),
        ("自定义配置", custom_config),
        ("多轮对话", multi_turn_chat),
    ]

    for name, func in examples:
        print(f"\n{'=' * 60}")
        print(f"示例: {name}")
        print("=" * 60)
        try:
            await func()
        except Exception as e:
            print(f"错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())
