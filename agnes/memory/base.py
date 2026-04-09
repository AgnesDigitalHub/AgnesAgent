"""
记忆系统基础抽象类
定义向量存储和记忆条目的标准接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MemoryEntry:
    """
    记忆条目

    存储一条可检索的记忆，包含内容、元数据和向量表示
    """

    id: str
    content: str
    embedding: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 1.0  # 重要性评分 0-1
    memory_type: str = "general"  # general/fact/preference/context
    source: str = "user"  # user/agent/system
    access_count: int = 0  # 访问次数（用于 LRU）
    last_accessed: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "memory_type": self.memory_type,
            "source": self.source,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
        }

    def touch(self) -> None:
        """更新访问记录"""
        self.access_count += 1
        self.last_accessed = datetime.now()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryEntry":
        """从字典创建"""
        return cls(
            id=data["id"],
            content=data["content"],
            embedding=data.get("embedding"),
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            importance=data.get("importance", 1.0),
            memory_type=data.get("memory_type", "general"),
            source=data.get("source", "user"),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None,
        )


class VectorStore(ABC):
    """
    向量存储抽象基类

    所有向量存储实现（ChromaDB、Milvus、内存等）都应继承此类
    """

    @abstractmethod
    async def add(self, entry: MemoryEntry) -> str:
        """
        添加记忆条目

        Args:
            entry: 记忆条目

        Returns:
            str: 条目 ID
        """
        pass

    @abstractmethod
    async def get(self, entry_id: str) -> MemoryEntry | None:
        """
        获取指定 ID 的记忆条目

        Args:
            entry_id: 条目 ID

        Returns:
            MemoryEntry | None: 记忆条目或 None
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter_dict: dict[str, Any] | None = None,
    ) -> list[tuple[MemoryEntry, float]]:
        """
        向量相似度搜索

        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            filter_dict: 过滤条件

        Returns:
            list[tuple[MemoryEntry, float]]: (条目, 相似度分数) 列表
        """
        pass

    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """
        删除记忆条目

        Args:
            entry_id: 条目 ID

        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    async def update(self, entry: MemoryEntry) -> bool:
        """
        更新记忆条目

        Args:
            entry: 记忆条目

        Returns:
            bool: 是否成功
        """
        pass

    @abstractmethod
    async def list_all(
        self,
        memory_type: str | None = None,
        source: str | None = None,
        limit: int = 100,
    ) -> list[MemoryEntry]:
        """
        列出所有记忆条目

        Args:
            memory_type: 按类型过滤
            source: 按来源过滤
            limit: 最大数量

        Returns:
            list[MemoryEntry]: 记忆条目列表
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """获取记忆条目总数"""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """清空所有记忆"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭存储连接"""
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
