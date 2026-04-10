"""Agent 协调器 - 整合 LLM、Skills、Memory、Persona、Planning"""

from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any, Callable

from agnes.core.chat_history import ChatHistory
from agnes.core.llm_provider import LLMProvider
from agnes.core.react_engine import ReActEngine, ReActResult, ReActStep
from agnes.core.agent_config import AgentConfig, AgentTemplates
from agnes.memory.manager import MemoryManager
from agnes.persona.core import Persona, PersonaTemplates
from agnes.planning.planner import Planner, Plan
from agnes.skills.engine import SkillCallEngine
from agnes.telemetry.instrumentation import instrument_llm_call, instrument_skill_call
from agnes.telemetry.tracer import start_span
from agnes.utils import metrics, timed
from agnes.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AgentResponse:
    content: str
    success: bool = True
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentState:
    is_running: bool = False
    current_step: int = 0
    total_steps: int = 0
    last_error: str | None = None


class Agent:
    """Agent 协调器

    职责：
    1. 接收用户输入，协调 LLM 进行推理
    2. 管理工具调用（Skills + MCP）
    3. 维护对话历史和上下文
    4. 提供流式输出支持
    5. 集成遥测追踪
    6. 长期记忆管理
    7. 角色扮演（Persona）
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        skill_engine: SkillCallEngine | None = None,
        config: AgentConfig | None = None,
        chat_history: ChatHistory | None = None,
        memory_manager: MemoryManager | None = None,
        persona: Persona | None = None,
    ):
        """
        初始化 Agent

        Args:
            llm_provider: LLM 提供商
            skill_engine: Skill 调用引擎（可选，默认创建新实例）
            config: Agent 配置（可选，使用默认配置）
            chat_history: 对话历史（可选，创建新的）
            memory_manager: 记忆管理器（可选，默认创建新实例）
            persona: 角色定义（可选）
        """
        self.llm = llm_provider
        self.config = config or AgentTemplates.default()
        self.skill_engine = skill_engine or SkillCallEngine()
        self.chat_history = chat_history or ChatHistory()
        self.memory = memory_manager
        self.persona = persona

        # 如果配置启用记忆但没有提供管理器，创建一个
        if self.config.capabilities.memory_enabled and self.memory is None:
            self.memory = MemoryManager()

        # 初始化 ReAct 引擎
        self.react_engine = ReActEngine(
            skill_engine=self.skill_engine,
            max_steps=self.config.capabilities.max_steps,
            tool_timeout=self.config.constraints.tool_timeout,
        )

        # 状态管理
        self.state = AgentState()

        # 回调函数
        self._on_step: Callable[[ReActStep], None] | None = None
        self._on_tool_call: Callable[[str, dict], None] | None = None
        self._on_tool_result: Callable[[Any], None] | None = None

        persona_name = self.persona.name if self.persona else "default"
        logger.info(
            f"Agent '{self.config.name}' initialized (memory={'enabled' if self.memory else 'disabled'}, persona={persona_name})"
        )

    def on_step(self, callback: Callable[[ReActStep], None]) -> "Agent":
        """注册步骤回调"""
        self._on_step = callback
        return self

    def on_tool_call(self, callback: Callable[[str, dict], None]) -> "Agent":
        """注册工具调用回调"""
        self._on_tool_call = callback
        return self

    def on_tool_result(self, callback: Callable[[Any], None]) -> "Agent":
        """注册工具结果回调"""
        self._on_tool_result = callback
        return self

    @timed("agent.run", tags={"mode": "standard"})
    async def run(
        self,
        query: str,
        system_prompt: str | None = None,
        use_react: bool = True,
    ) -> AgentResponse:
        """
        运行 Agent 处理用户查询

        Args:
            query: 用户输入
            system_prompt: 自定义系统提示词（可选）
            use_react: 是否使用 ReAct 模式（多步推理）

        Returns:
            AgentResponse: 响应结果
        """
        with start_span(f"agent.run.{self.config.name}"):
            self.state.is_running = True
            self.state.current_step = 0
            self.state.last_error = None
            metrics.increment("agent.run.count", tags={"name": self.config.name})

            try:
                # 添加用户消息到历史
                self.chat_history.add_user_message(query)

                # 确定系统提示词（优先级：传入 > Persona > 配置）
                if system_prompt:
                    sys_prompt = system_prompt
                elif self.persona:
                    sys_prompt = self.persona.get_effective_system_prompt()
                else:
                    sys_prompt = self.config.behavior.system_prompt

                # 如果启用了记忆，检索相关记忆并增强系统提示词
                if self.memory and self.config.capabilities.memory_enabled:
                    memory_context = await self.memory.get_context_for_query(
                        query,
                        max_tokens=1000,
                    )
                    if memory_context:
                        sys_prompt = f"{sys_prompt}\n\n{memory_context}"

                if use_react and self.config.capabilities.multi_step:
                    # ReAct 模式：多步推理
                    result = await self._run_react(query, sys_prompt)
                else:
                    # 简单模式：单轮对话
                    result = await self._run_simple(query, sys_prompt)

                # 添加助手回复到历史
                if result.success:
                    self.chat_history.add_assistant_message(result.content)

                    # 如果启用了记忆，保存重要信息
                    if self.memory and self.config.capabilities.memory_enabled:
                        await self._save_to_memory(query, result.content, result.tool_calls)

                return result

            except Exception as e:
                logger.error(f"Agent run failed: {e}", exc_info=True)
                self.state.last_error = str(e)
                return AgentResponse(
                    content=f"执行出错: {str(e)}",
                    success=False,
                    metadata={"error": str(e)},
                )
            finally:
                self.state.is_running = False

    async def run_stream(
        self,
        query: str,
        system_prompt: str | None = None,
        use_react: bool = True,
    ) -> AsyncGenerator[str, None]:
        """
        流式运行 Agent

        Args:
            query: 用户输入
            system_prompt: 自定义系统提示词（可选）
            use_react: 是否使用 ReAct 模式

        Yields:
            str: 流式输出的文本片段
        """
        with start_span(f"agent.run_stream.{self.config.name}"):
            self.state.is_running = True

            try:
                self.chat_history.add_user_message(query)
                sys_prompt = system_prompt or self.config.behavior.system_prompt

                if use_react and self.config.capabilities.multi_step:
                    # 流式 ReAct
                    full_response = ""
                    async for step in self.react_engine.run_stream(
                        query=query,
                        chat_history=self.chat_history,
                        system_prompt=sys_prompt,
                        llm_stream_func=self._llm_stream_wrapper,
                        use_native_fc=self.config.capabilities.function_calling,
                    ):
                        if self._on_step:
                            self._on_step(step)

                        if step.step_type.name == "FINAL":
                            full_response = step.content
                            yield step.content
                        elif step.step_type.name == "THOUGHT":
                            # 可以配置是否输出思考过程
                            if self.config.metadata.get("show_thoughts", False):
                                yield f"[思考] {step.content}\n"
                        elif step.step_type.name == "ACTION":
                            if self.config.metadata.get("show_actions", False):
                                yield f"[行动] {step.content}\n"

                    if full_response:
                        self.chat_history.add_assistant_message(full_response)
                else:
                    # 简单流式
                    messages = self.chat_history.to_openai_format()
                    messages.insert(0, {"role": "system", "content": sys_prompt})

                    full_content = ""
                    async for token in self.llm.chat_stream(
                        messages=messages,
                        temperature=self.config.behavior.temperature,
                        max_tokens=self.config.behavior.max_tokens,
                    ):
                        full_content += token
                        yield token

                    self.chat_history.add_assistant_message(full_content)

            except Exception as e:
                logger.error(f"Agent stream failed: {e}", exc_info=True)
                yield f"\n[错误] {str(e)}"
            finally:
                self.state.is_running = False

    async def _run_react(self, query: str, system_prompt: str) -> AgentResponse:
        """运行 ReAct 模式"""

        # 包装 LLM 调用以添加追踪
        async def llm_chat_wrapper(messages, tools=None):
            instrument_llm_call(
                provider_name=self.config.name,
                model=getattr(self.llm, "model", "unknown"),
                prompt_tokens=len(str(messages)),
            )

            if tools and self.config.capabilities.function_calling:
                return await self.llm.chat(
                    messages=messages,
                    temperature=self.config.behavior.temperature,
                    max_tokens=self.config.behavior.max_tokens,
                    tools=tools,
                    tool_choice="auto",
                )
            else:
                return await self.llm.chat(
                    messages=messages,
                    temperature=self.config.behavior.temperature,
                    max_tokens=self.config.behavior.max_tokens,
                )

        result: ReActResult = await self.react_engine.run(
            query=query,
            chat_history=self.chat_history,
            system_prompt=system_prompt,
            llm_chat_func=llm_chat_wrapper,
            use_native_fc=self.config.capabilities.function_calling,
        )

        # 触发回调
        for step in result.steps:
            if self._on_step:
                self._on_step(step)

        for tc in result.tool_calls:
            if self._on_tool_call:
                self._on_tool_call(tc.name, tc.parameters)

        for tr in result.tool_results:
            if self._on_tool_result:
                self._on_tool_result(tr)

        return AgentResponse(
            content=result.answer,
            success=result.success,
            tool_calls=[{"name": tc.name, "params": tc.parameters} for tc in result.tool_calls],
            metadata={
                "steps": result.step_count,
                "tool_calls": result.tool_call_count,
                "react_result": result.to_dict() if hasattr(result, "to_dict") else {},
            },
        )

    async def _run_simple(self, query: str, system_prompt: str) -> AgentResponse:
        """运行简单模式（单轮）"""
        messages = self.chat_history.to_openai_format()
        messages.insert(0, {"role": "system", "content": system_prompt})

        # 检查是否需要工具
        tools = None
        if self.config.capabilities.function_calling:
            tools = self.skill_engine.registry.get_all_openai_functions()

        instrument_llm_call(
            provider_name=self.config.name,
            model=getattr(self.llm, "model", "unknown"),
            prompt_tokens=len(str(messages)),
        )

        if tools:
            response = await self.llm.chat(
                messages=messages,
                temperature=self.config.behavior.temperature,
                max_tokens=self.config.behavior.max_tokens,
                tools=tools,
                tool_choice="auto",
            )
        else:
            response = await self.llm.chat(
                messages=messages,
                temperature=self.config.behavior.temperature,
                max_tokens=self.config.behavior.max_tokens,
            )

        # 处理工具调用
        tool_calls = []
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                tool_name = tc.function.name
                tool_params = __import__("json").loads(tc.function.arguments)

                if self._on_tool_call:
                    self._on_tool_call(tool_name, tool_params)

                instrument_skill_call(tool_name, tool_params)

                result = await self.skill_engine.call(tool_name, tool_params)

                if self._on_tool_result:
                    self._on_tool_result(result)

                tool_calls.append(
                    {
                        "name": tool_name,
                        "params": tool_params,
                        "result": result.data if result.success else result.error_message,
                    }
                )

        return AgentResponse(
            content=response.content or "",
            success=True,
            tool_calls=tool_calls,
            metadata={
                "model": getattr(response, "model", "unknown"),
                "usage": getattr(response, "usage", None),
            },
        )

    async def _llm_stream_wrapper(self, messages, **kwargs):
        """包装 LLM 流式调用"""
        async for token in self.llm.chat_stream(
            messages=messages,
            temperature=self.config.behavior.temperature,
            max_tokens=self.config.behavior.max_tokens,
            **kwargs,
        ):
            yield token

    def clear_history(self) -> None:
        """清空对话历史"""
        self.chat_history.clear()
        logger.debug("Chat history cleared")

    def get_history(self) -> list[dict[str, Any]]:
        """获取对话历史"""
        return [msg.__dict__ for msg in self.chat_history.messages]

    def get_state(self) -> AgentState:
        """获取当前状态"""
        return self.state

    async def _save_to_memory(
        self,
        query: str,
        response: str,
        tool_calls: list[dict[str, Any]],
    ) -> None:
        """
        保存对话到长期记忆

        智能判断哪些信息值得保存
        """
        if not self.memory:
            return

        # 保存用户查询（如果是事实性问题或重要信息）
        if len(query) > 10 and not query.startswith("你好") and not query.startswith("hi"):
            # 判断是否是事实性问题
            fact_indicators = [
                "是什么",
                "什么是",
                "为什么",
                "怎么",
                "如何",
                "what",
                "why",
                "how",
                "who",
                "when",
                "where",
            ]
            is_fact_question = any(indicator in query.lower() for indicator in fact_indicators)

            if is_fact_question:
                await self.memory.add(
                    content=f"Q: {query}\nA: {response}",
                    memory_type="fact",
                    source="conversation",
                    importance=0.7,
                    metadata={"query": query, "has_tools": len(tool_calls) > 0},
                )

        # 保存工具调用结果（如果有）
        if tool_calls:
            for tc in tool_calls:
                await self.memory.add(
                    content=f"使用了工具 {tc['name']} 处理: {tc.get('params', {})}",
                    memory_type="context",
                    source="agent",
                    importance=0.5,
                    metadata={"tool": tc["name"]},
                )

    async def remember(self, content: str, importance: float = 0.8, **kwargs) -> str | None:
        """
        显式保存记忆

        Args:
            content: 记忆内容
            importance: 重要性 (0-1)
            **kwargs: 额外元数据

        Returns:
            str | None: 记忆 ID
        """
        if not self.memory:
            logger.warning("Memory is not enabled for this agent")
            return None

        memory_id = await self.memory.add(
            content=content,
            importance=importance,
            **kwargs,
        )
        logger.debug(f"Explicitly saved memory: {memory_id}")
        return memory_id

    async def recall(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        """
        显式检索记忆

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            list[tuple[str, float]]: (内容, 相似度) 列表
        """
        if not self.memory:
            return []

        results = await self.memory.search(query, top_k=top_k)
        return [(entry.content, score) for entry, score in results]

    @classmethod
    def create(
        cls,
        llm_provider: LLMProvider,
        template: str = "default",
        persona: Persona | None = None,
        **kwargs,
    ) -> "Agent":
        """
        使用模板快速创建 Agent

        Args:
            llm_provider: LLM 提供商
            template: 模板名称 (default/coder/researcher/executor)
            persona: 角色定义（可选，覆盖模板中的配置）
            **kwargs: 额外配置参数

        Returns:
            Agent: 配置好的 Agent 实例
        """
        templates = {
            "default": AgentTemplates.default(),
            "coder": AgentTemplates.coder(),
            "researcher": AgentTemplates.researcher(),
            "executor": AgentTemplates.executor(),
        }

        config = templates.get(template, AgentTemplates.default())

        # 应用额外配置
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
            elif key.startswith("behavior_"):
                attr = key.replace("behavior_", "")
                if hasattr(config.behavior, attr):
                    setattr(config.behavior, attr, value)
            elif key.startswith("capabilities_"):
                attr = key.replace("capabilities_", "")
                if hasattr(config.capabilities, attr):
                    setattr(config.capabilities, attr, value)

        return cls(llm_provider=llm_provider, config=config, persona=persona)

    async def execute_plan(
        self,
        task_description: str,
        template: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        执行复杂任务计划

        自动分解任务并执行

        Args:
            task_description: 任务描述
            template: 模板名称 (research/code/analysis)
            context: 上下文

        Returns:
            dict: 执行结果
        """
        from agnes.planning.planner import Planner

        planner = Planner(skill_engine=self.skill_engine)

        plan, result = await planner.plan_and_execute(
            task_description=task_description,
            context=context,
            template=template,
        )

        return {
            "plan": plan.to_dict(),
            "result": result.to_dict(),
            "success": result.success,
        }
