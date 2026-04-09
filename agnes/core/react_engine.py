"""
ReAct (Reasoning + Acting) 推理引擎
实现推理-行动循环，支持 Function Calling 和文本解析两种模式
"""

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, AsyncGenerator

from agnes.core.chat_history import ChatHistory
from agnes.skills.base import SkillResult
from agnes.skills.engine import SkillCallEngine

logger = logging.getLogger(__name__)


class StepType(Enum):
    """步骤类型"""

    THOUGHT = auto()  # 思考
    ACTION = auto()  # 行动（工具调用）
    OBSERVATION = auto()  # 观察（工具结果）
    FINAL = auto()  # 最终答案


@dataclass
class ReActStep:
    """ReAct 单步记录"""

    step_type: StepType
    content: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: __import__("time").time())

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.step_type.name,
            "content": self.content,
            "data": self.data,
            "timestamp": self.timestamp,
        }


@dataclass
class ToolCall:
    """工具调用定义"""

    name: str
    parameters: dict[str, Any]
    id: str = field(default_factory=lambda: __import__("uuid").uuid4().hex[:8])


@dataclass
class ReActResult:
    """ReAct 执行结果"""

    success: bool
    answer: str
    steps: list[ReActStep]
    tool_calls: list[ToolCall]
    tool_results: list[SkillResult]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def tool_call_count(self) -> int:
        return len(self.tool_calls)


class ReActEngine:
    """
    ReAct 推理引擎

    支持两种模式：
    1. Native Function Calling: LLM 原生支持 function calling
    2. Text Parsing: 从文本中解析工具调用
    """

    def __init__(
        self,
        skill_engine: SkillCallEngine,
        max_steps: int = 10,
        tool_timeout: float = 30.0,
    ):
        self.skill_engine = skill_engine
        self.max_steps = max_steps
        self.tool_timeout = tool_timeout

    async def run(
        self,
        query: str,
        chat_history: ChatHistory,
        system_prompt: str,
        llm_chat_func: Any,
        use_native_fc: bool = True,
    ) -> ReActResult:
        """
        执行 ReAct 循环

        Args:
            query: 用户查询
            chat_history: 对话历史
            system_prompt: 系统提示词
            llm_chat_func: LLM 调用函数
            use_native_fc: 是否使用原生 Function Calling

        Returns:
            ReActResult: 执行结果
        """
        steps: list[ReActStep] = []
        tool_calls: list[ToolCall] = []
        tool_results: list[SkillResult] = []

        # 构建 ReAct 系统提示词
        react_system_prompt = self._build_react_prompt(system_prompt, use_native_fc)

        # 初始化对话
        current_messages = chat_history.to_openai_format()
        current_messages.insert(0, {"role": "system", "content": react_system_prompt})
        current_messages.append({"role": "user", "content": query})

        for step in range(self.max_steps):
            logger.debug(f"ReAct step {step + 1}/{self.max_steps}")

            # 调用 LLM
            try:
                if use_native_fc:
                    response = await llm_chat_func(
                        messages=current_messages,
                        tools=self.skill_engine.registry.get_all_openai_functions(),
                    )
                else:
                    response = await llm_chat_func(messages=current_messages)
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return ReActResult(
                    success=False,
                    answer=f"LLM调用失败: {str(e)}",
                    steps=steps,
                    tool_calls=tool_calls,
                    tool_results=tool_results,
                )

            llm_content = response.content if hasattr(response, "content") else str(response)

            # 检查是否是最终答案
            if self._is_final_answer(llm_content, use_native_fc, response):
                final_answer = self._extract_final_answer(llm_content, response)
                steps.append(ReActStep(StepType.FINAL, final_answer))
                return ReActResult(
                    success=True,
                    answer=final_answer,
                    steps=steps,
                    tool_calls=tool_calls,
                    tool_results=tool_results,
                )

            # 解析工具调用
            calls = self._parse_tool_calls(llm_content, response, use_native_fc)

            if not calls:
                # 没有工具调用，视为思考步骤
                steps.append(ReActStep(StepType.THOUGHT, llm_content))
                current_messages.append({"role": "assistant", "content": llm_content})
                continue

            # 执行工具调用
            for call in calls:
                tool_calls.append(call)
                steps.append(ReActStep(StepType.ACTION, f"调用 {call.name}", {"tool": call.name, "params": call.parameters}))

                # 检查是否是危险操作
                if self._is_dangerous_operation(call.name):
                    observation = f"⚠️ 危险操作 '{call.name}' 需要用户确认"
                    result = SkillResult.error("dangerous_operation", observation)
                else:
                    # 执行工具
                    result = await self.skill_engine.call(
                        call.name,
                        call.parameters,
                        timeout=self.tool_timeout,
                    )

                tool_results.append(result)

                # 构建观察结果
                if result.success:
                    observation = self._format_observation(result.data)
                else:
                    observation = f"错误: {result.error_message}"

                steps.append(ReActStep(StepType.OBSERVATION, observation, {"tool": call.name}))

                # 添加到消息历史
                current_messages.append({"role": "assistant", "content": f"我将使用 {call.name} 工具"})
                current_messages.append({"role": "user", "content": f"观察结果: {observation}"})

        # 达到最大步数
        logger.warning(f"ReAct reached max steps ({self.max_steps})")
        return ReActResult(
            success=False,
            answer="达到最大推理步数限制，未能完成",
            steps=steps,
            tool_calls=tool_calls,
            tool_results=tool_results,
            metadata={"max_steps_reached": True},
        )

    async def run_stream(
        self,
        query: str,
        chat_history: ChatHistory,
        system_prompt: str,
        llm_stream_func: Any,
        use_native_fc: bool = True,
    ) -> AsyncGenerator[ReActStep, None]:
        """
        流式执行 ReAct 循环

        每完成一个步骤就 yield 结果
        """
        react_system_prompt = self._build_react_prompt(system_prompt, use_native_fc)

        current_messages = chat_history.to_openai_format()
        current_messages.insert(0, {"role": "system", "content": react_system_prompt})
        current_messages.append({"role": "user", "content": query})

        for step in range(self.max_steps):
            # 收集流式输出
            full_content = ""
            async for token in llm_stream_func(messages=current_messages):
                full_content += token
                # 可以在这里 yield 部分思考过程

            # 检查是否是最终答案
            if self._is_final_answer(full_content, use_native_fc, None):
                final_step = ReActStep(StepType.FINAL, full_content)
                yield final_step
                return

            # 解析工具调用
            calls = self._parse_tool_calls(full_content, None, use_native_fc)

            if not calls:
                thought_step = ReActStep(StepType.THOUGHT, full_content)
                yield thought_step
                current_messages.append({"role": "assistant", "content": full_content})
                continue

            # 执行工具调用
            for call in calls:
                action_step = ReActStep(StepType.ACTION, f"调用 {call.name}", {"tool": call.name})
                yield action_step

                result = await self.skill_engine.call(call.name, call.parameters, timeout=self.tool_timeout)

                if result.success:
                    observation = self._format_observation(result.data)
                else:
                    observation = f"错误: {result.error_message}"

                obs_step = ReActStep(StepType.OBSERVATION, observation, {"tool": call.name})
                yield obs_step

                current_messages.append({"role": "assistant", "content": f"使用 {call.name}"})
                current_messages.append({"role": "user", "content": f"结果: {observation}"})

        yield ReActStep(StepType.FINAL, "达到最大推理步数限制", {"max_steps_reached": True})

    def _build_react_prompt(self, base_prompt: str, use_native_fc: bool) -> str:
        """构建 ReAct 系统提示词"""
        react_instructions = """
你可以使用工具来完成任务。遵循以下格式：

思考: 分析当前情况，决定下一步行动
行动: 使用工具（如果需要）
观察: 查看工具返回的结果
...（重复思考-行动-观察直到完成任务）

最终答案: 给出最终回复

可用工具:
"""
        if not use_native_fc:
            # 文本模式需要更详细的说明
            react_instructions += """
当你需要使用工具时，请按以下 JSON 格式输出：
```json
{
  "name": "工具名称",
  "parameters": {"参数名": "参数值"}
}
```
"""

        return f"{base_prompt}\n\n{react_instructions}"

    def _parse_tool_calls(
        self, content: str, response: Any, use_native_fc: bool
    ) -> list[ToolCall]:
        """解析工具调用"""
        calls = []

        if use_native_fc and response and hasattr(response, "tool_calls"):
            # 原生 Function Calling
            for tc in response.tool_calls or []:
                calls.append(ToolCall(
                    name=tc.function.name,
                    parameters=json.loads(tc.function.arguments),
                ))
        else:
            # 文本解析模式
            calls = self._parse_text_tool_calls(content)

        return calls

    def _parse_text_tool_calls(self, content: str) -> list[ToolCall]:
        """从文本中解析工具调用"""
        calls = []

        # 查找 ```json ... ``` 块
        json_blocks = re.findall(r"```json\s*(.*?)\s*```", content, re.DOTALL)

        for block in json_blocks:
            try:
                data = json.loads(block.strip())
                if isinstance(data, dict) and ("name" in data or "function" in data):
                    name = data.get("name") or data.get("function", "")
                    params = data.get("parameters") or data.get("arguments", {})
                    calls.append(ToolCall(name=name, parameters=params))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and ("name" in item or "function" in item):
                            name = item.get("name") or item.get("function", "")
                            params = item.get("parameters") or item.get("arguments", {})
                            calls.append(ToolCall(name=name, parameters=params))
            except json.JSONDecodeError:
                continue

        return calls

    def _is_final_answer(self, content: str, use_native_fc: bool, response: Any) -> bool:
        """检查是否是最终答案"""
        if use_native_fc and response:
            # 原生模式下，没有 tool_calls 就是最终答案
            return not (hasattr(response, "tool_calls") and response.tool_calls)

        # 文本模式：检查是否包含 "最终答案" 或没有工具调用标记
        has_tool_marker = "```json" in content or '"name":' in content
        has_final_marker = "最终答案:" in content or "Final Answer:" in content

        return has_final_marker or not has_tool_marker

    def _extract_final_answer(self, content: str, response: Any) -> str:
        """提取最终答案"""
        if response and hasattr(response, "content") and response.content:
            return response.content

        # 从文本中提取
        patterns = [
            r"最终答案:\s*(.*)",
            r"Final Answer:\s*(.*)",
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return content.strip()

    def _is_dangerous_operation(self, tool_name: str) -> bool:
        """检查是否是危险操作"""
        dangerous = ["delete", "remove", "exec", "eval", "system", "rm", "format"]
        return any(d in tool_name.lower() for d in dangerous)

    def _format_observation(self, data: Any) -> str:
        """格式化观察结果"""
        if isinstance(data, str):
            return data[:1000]  # 限制长度
        elif isinstance(data, dict):
            return json.dumps(data, ensure_ascii=False, indent=2)[:1000]
        else:
            return str(data)[:1000]
