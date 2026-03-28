from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatMessage:
    """聊天消息"""

    role: str
    content: str
    timestamp: float = field(default_factory=lambda: __import__("time").time())
    metadata: dict[str, Any] = field(default_factory=dict)


class ChatHistory:
    """对话历史管理器"""

    def __init__(self, max_messages: int | None = None, system_prompt: str | None = None):
        """
        初始化对话历史

        Args:
            max_messages: 最大消息数量，超过后会自动删除最早的消息
            system_prompt: 系统提示词
        """
        self.messages: list[ChatMessage] = []
        self.max_messages = max_messages
        self.system_prompt = system_prompt

        if system_prompt:
            self.add_system_message(system_prompt)

    def add_message(self, role: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        """
        添加消息

        Args:
            role: 角色 (system, user, assistant)
            content: 消息内容
            metadata: 元数据
        """
        message = ChatMessage(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.messages.append(message)
        self._trim_history()

    def add_user_message(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """添加用户消息"""
        self.add_message("user", content, metadata)

    def add_assistant_message(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """添加助手消息"""
        self.add_message("assistant", content, metadata)

    def add_system_message(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """添加系统消息"""
        # 如果已存在系统消息，更新它
        for i, msg in enumerate(self.messages):
            if msg.role == "system":
                self.messages[i] = ChatMessage(
                    role="system",
                    content=content,
                    metadata=metadata or {},
                )
                return
        # 否则添加到开头
        self.messages.insert(0, ChatMessage(role="system", content=content, metadata=metadata or {}))

    def to_openai_format(self) -> list[dict[str, str]]:
        """转换为 OpenAI API 格式"""
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]

    def clear(self) -> None:
        """清空对话历史"""
        self.messages = []
        if self.system_prompt:
            self.add_system_message(self.system_prompt)

    def _trim_history(self) -> None:
        """裁剪历史记录"""
        if self.max_messages is None:
            return

        # 保留系统消息
        system_messages = [msg for msg in self.messages if msg.role == "system"]
        other_messages = [msg for msg in self.messages if msg.role != "system"]

        # 裁剪其他消息
        if len(other_messages) > self.max_messages:
            other_messages = other_messages[-self.max_messages :]

        self.messages = system_messages + other_messages

    def __len__(self) -> int:
        return len(self.messages)

    def __getitem__(self, index: int) -> ChatMessage:
        return self.messages[index]

    def __iter__(self):
        return iter(self.messages)
