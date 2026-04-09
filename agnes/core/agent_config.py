"""
Agent 配置管理
定义 Agent 的行为、能力和约束
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentCapability:
    """Agent 能力配置"""

    # 是否启用 Function Calling
    function_calling: bool = True
    # 是否启用流式输出
    streaming: bool = True
    # 是否启用多步骤推理
    multi_step: bool = True
    # 最大推理步数
    max_steps: int = 10
    # 是否允许并行工具调用
    parallel_tools: bool = False
    # 是否启用记忆
    memory_enabled: bool = False
    # 是否启用 RAG
    rag_enabled: bool = False


@dataclass
class AgentBehavior:
    """Agent 行为配置"""

    # 温度参数
    temperature: float = 0.7
    # 最大 token 数
    max_tokens: int | None = None
    # 系统提示词
    system_prompt: str = "你是一个有用的AI助手。"
    # 响应格式: text/json/markdown
    response_format: str = "text"
    # 是否要求确认危险操作
    require_confirmation: bool = True
    # 危险操作列表
    dangerous_operations: list[str] = field(default_factory=lambda: ["delete", "remove", "exec", "eval"])


@dataclass
class AgentConstraints:
    """Agent 约束配置"""

    # 单次最大工具调用数
    max_tools_per_step: int = 5
    # 工具调用超时(秒)
    tool_timeout: float = 30.0
    # 最大重试次数
    max_retries: int = 2
    # 允许的工具列表 (空表示全部)
    allowed_tools: list[str] = field(default_factory=list)
    # 禁止的工具列表
    blocked_tools: list[str] = field(default_factory=list)
    # 最大上下文长度
    max_context_length: int = 4000


@dataclass
class AgentConfig:
    """
    Agent 完整配置

    包含能力、行为、约束三个维度的配置
    """

    # Agent 标识
    name: str = "default_agent"
    description: str = ""
    version: str = "1.0.0"

    # 能力配置
    capabilities: AgentCapability = field(default_factory=AgentCapability)
    # 行为配置
    behavior: AgentBehavior = field(default_factory=AgentBehavior)
    # 约束配置
    constraints: AgentConstraints = field(default_factory=AgentConstraints)

    # 扩展配置
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentConfig":
        """从字典创建配置"""
        capabilities_data = data.get("capabilities", {})
        behavior_data = data.get("behavior", {})
        constraints_data = data.get("constraints", {})

        return cls(
            name=data.get("name", "default_agent"),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            capabilities=AgentCapability(**capabilities_data),
            behavior=AgentBehavior(**behavior_data),
            constraints=AgentConstraints(**constraints_data),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": {
                "function_calling": self.capabilities.function_calling,
                "streaming": self.capabilities.streaming,
                "multi_step": self.capabilities.multi_step,
                "max_steps": self.capabilities.max_steps,
                "parallel_tools": self.capabilities.parallel_tools,
                "memory_enabled": self.capabilities.memory_enabled,
                "rag_enabled": self.capabilities.rag_enabled,
            },
            "behavior": {
                "temperature": self.behavior.temperature,
                "max_tokens": self.behavior.max_tokens,
                "system_prompt": self.behavior.system_prompt,
                "response_format": self.behavior.response_format,
                "require_confirmation": self.behavior.require_confirmation,
                "dangerous_operations": self.behavior.dangerous_operations,
            },
            "constraints": {
                "max_tools_per_step": self.constraints.max_tools_per_step,
                "tool_timeout": self.constraints.tool_timeout,
                "max_retries": self.constraints.max_retries,
                "allowed_tools": self.constraints.allowed_tools,
                "blocked_tools": self.constraints.blocked_tools,
                "max_context_length": self.constraints.max_context_length,
            },
            "metadata": self.metadata,
        }


# 预定义配置模板
class AgentTemplates:
    """Agent 配置模板"""

    @staticmethod
    def default() -> AgentConfig:
        """默认配置"""
        return AgentConfig(
            name="default",
            description="通用助手",
        )

    @staticmethod
    def coder() -> AgentConfig:
        """代码助手配置"""
        return AgentConfig(
            name="coder",
            description="专业代码助手",
            behavior=AgentBehavior(
                system_prompt="你是一个专业的编程助手。擅长代码编写、调试、重构和解释。",
                temperature=0.3,
                response_format="markdown",
            ),
            capabilities=AgentCapability(
                function_calling=True,
                multi_step=True,
                max_steps=15,
            ),
        )

    @staticmethod
    def researcher() -> AgentConfig:
        """研究助手配置"""
        return AgentConfig(
            name="researcher",
            description="研究分析助手",
            behavior=AgentBehavior(
                system_prompt="你是一个研究分析助手。擅长信息收集、分析和总结。",
                temperature=0.5,
            ),
            capabilities=AgentCapability(
                function_calling=True,
                multi_step=True,
                max_steps=20,
                memory_enabled=True,
                rag_enabled=True,
            ),
        )

    @staticmethod
    def executor() -> AgentConfig:
        """任务执行助手配置"""
        return AgentConfig(
            name="executor",
            description="任务执行助手",
            behavior=AgentBehavior(
                system_prompt="你是一个任务执行助手。擅长分解任务并逐步执行。",
                temperature=0.2,
                require_confirmation=True,
            ),
            capabilities=AgentCapability(
                function_calling=True,
                multi_step=True,
                max_steps=50,
                parallel_tools=True,
            ),
            constraints=AgentConstraints(
                max_tools_per_step=10,
                tool_timeout=60.0,
            ),
        )
