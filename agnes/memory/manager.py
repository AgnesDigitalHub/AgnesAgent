"""
记忆管理器

记忆系统的核心组件，负责：
1. 文本嵌入和向量化
2. 记忆的增删改查
3. 记忆重要性评估
4. 记忆压缩和清理
5. 与 Agent 的上下文集成
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from agnes.memory.base import MemoryEntry, VectorStore
from agnes.memory.embedder import Embedder, SimpleEmbedder
from agnes.memory.simple_store import SimpleVectorStore

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    记忆管理器

    提供高级记忆管理功能，包括：
    - 自动向量化
    - 智能检索
    - 重要性评估
    - 记忆压缩
    """

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        embedder: Embedder | None = None,
        max_memories: int = 10000,
        consolidation_threshold: int = 8000,
    ):
        """
        初始化记忆管理器

        Args:
            vector_store: 向量存储（默认 SimpleVectorStore）
            embedder: 嵌入器（默认 SimpleEmbedder）
            max_memories: 最大记忆数量
            consolidation_threshold: 触发压缩的阈值
        """
        self.store = vector_store or SimpleVectorStore()
        self.embedder = embedder or SimpleEmbedder()
        self.max_memories = max_memories
        self.consolidation_threshold = consolidation_threshold

        logger.info(
            f"MemoryManager initialized: max={max_memories}, "
            f"threshold={consolidation_threshold}"
        )

    async def add(
        self,
        content: str,
        memory_type: str = "general",
        source: str = "user",
        importance: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        添加记忆

        Args:
            content: 记忆内容
            memory_type: 记忆类型 (general/fact/preference/context)
            source: 来源 (user/agent/system)
            importance: 重要性 (0-1，None 则自动计算)
            metadata: 额外元数据

        Returns:
            str: 记忆 ID
        """
        # 计算嵌入向量
        embedding = await self.embedder.embed(content)

        # 自动计算重要性
        if importance is None:
            importance = self._calculate_importance(content, memory_type)

        # 创建记忆条目
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=content,
            embedding=embedding,
            metadata=metadata or {},
            importance=importance,
            memory_type=memory_type,
            source=source,
        )

        # 存储
        memory_id = await self.store.add(entry)

        # 检查是否需要压缩
        count = await self.store.count()
        if count > self.consolidation_threshold:
            await self._consolidate()

        logger.debug(f"Added memory: {memory_id} (type={memory_type}, importance={importance:.2f})")
        return memory_id

    async def search(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
        min_importance: float = 0.0,
    ) -> list[tuple[MemoryEntry, float]]:
        """
        搜索相关记忆

        Args:
            query: 查询文本
            top_k: 返回结果数量
            memory_type: 按类型过滤
            min_importance: 最小重要性阈值

        Returns:
            list[tuple[MemoryEntry, float]]: (记忆, 相似度) 列表
        """
        # 向量化查询
        query_embedding = await self.embedder.embed(query)

        # 构建过滤条件
        filter_dict = {}
        if memory_type:
            filter_dict["memory_type"] = memory_type

        # 搜索
        results = await self.store.search(query_embedding, top_k=top_k * 2, filter_dict=filter_dict)

        # 按重要性过滤
        filtered_results = [
            (entry, score) for entry, score in results
            if entry.importance >= min_importance
        ]

        return filtered_results[:top_k]

    async def get_context_for_query(
        self,
        query: str,
        max_tokens: int = 2000,
        memory_type: str | None = None,
    ) -> str:
        """
        获取与查询相关的上下文

        用于增强 LLM 的上下文，自动选择最相关的记忆

        Args:
            query: 查询文本
            max_tokens: 最大 token 数（估算）
            memory_type: 记忆类型过滤

        Returns:
            str: 格式化的上下文文本
        """
        # 搜索相关记忆
        results = await self.search(query, top_k=10, memory_type=memory_type)

        if not results:
            return ""

        # 构建上下文（按相似度排序）
        context_parts = []
        current_length = 0
        max_chars = max_tokens * 4  # 粗略估算：1 token ≈ 4 chars

        for entry, score in results:
            part = f"[{entry.memory_type}] {entry.content}"
            if current_length + len(part) > max_chars:
                break
            context_parts.append(part)
            current_length += len(part)

        if not context_parts:
            return ""

        return "相关记忆:\n" + "\n".join(f"- {p}" for p in context_parts)

    async def get(self, memory_id: str) -> MemoryEntry | None:
        """获取指定记忆"""
        return await self.store.get(memory_id)

    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        return await self.store.delete(memory_id)

    async def update_importance(self, memory_id: str, importance: float) -> bool:
        """更新记忆重要性"""
        entry = await self.store.get(memory_id)
        if entry:
            entry.importance = max(0.0, min(1.0, importance))
            return await self.store.update(entry)
        return False

    async def list_recent(
        self,
        hours: int = 24,
        memory_type: str | None = None,
        limit: int = 100,
    ) -> list[MemoryEntry]:
        """
        列出最近添加的记忆

        Args:
            hours: 最近多少小时
            memory_type: 类型过滤
            limit: 最大数量
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        all_entries = await self.store.list_all(memory_type=memory_type, limit=limit * 2)

        recent = [e for e in all_entries if e.timestamp > cutoff]
        return recent[:limit]

    async def list_important(
        self,
        min_importance: float = 0.7,
        limit: int = 50,
    ) -> list[MemoryEntry]:
        """列出重要记忆"""
        all_entries = await self.store.list_all(limit=1000)
        important = [e for e in all_entries if e.importance >= min_importance]
        important.sort(key=lambda x: x.importance, reverse=True)
        return important[:limit]

    async def clear(self) -> None:
        """清空所有记忆"""
        await self.store.clear()
        logger.info("All memories cleared")

    async def get_stats(self) -> dict[str, Any]:
        """获取记忆统计信息"""
        count = await self.store.count()
        store_stats = await self.store.get_stats() if hasattr(self.store, "get_stats") else {}

        return {
            "total_memories": count,
            "max_memories": self.max_memories,
            "usage_percent": (count / self.max_memories * 100) if self.max_memories > 0 else 0,
            "embedder_dimension": self.embedder.dimension(),
            **store_stats,
        }

    def _calculate_importance(self, content: str, memory_type: str) -> float:
        """
        计算记忆重要性

        基于内容特征和类型自动评估
        """
        base_score = 0.5

        # 根据类型调整
        type_weights = {
            "fact": 0.8,      # 事实性知识重要
            "preference": 0.9,  # 用户偏好很重要
            "context": 0.4,     # 上下文相对不重要
            "general": 0.5,
        }
        base_score = type_weights.get(memory_type, 0.5)

        # 根据内容长度调整（太短或太长都降权）
        length = len(content)
        if length < 10:
            base_score -= 0.2
        elif length > 1000:
            base_score -= 0.1

        # 包含关键信息加分
        key_indicators = [
            "重要", "必须", "关键", "记住", "永远",
            "important", "must", "key", "remember", "always",
        ]
        for indicator in key_indicators:
            if indicator in content.lower():
                base_score += 0.1
                break

        return max(0.0, min(1.0, base_score))

    async def _consolidate(self) -> None:
        """
        记忆压缩

        当记忆数量超过阈值时，删除低重要性/低访问频率的记忆
        """
        logger.info("Starting memory consolidation...")

        count = await self.store.count()
        if count <= self.max_memories:
            return

        # 获取所有记忆
        all_entries = await self.store.list_all(limit=count)

        # 计算保留分数（重要性 + 访问频率 + 时间衰减）
        now = datetime.now()

        def retention_score(entry: MemoryEntry) -> float:
            # 重要性权重
            score = entry.importance * 0.5

            # 访问频率权重
            score += min(entry.access_count / 10, 0.3)

            # 时间衰减（越新越好）
            age_days = (now - entry.timestamp).days
            time_score = max(0, 0.2 - age_days * 0.01)
            score += time_score

            return score

        # 按保留分数排序
        all_entries.sort(key=retention_score, reverse=True)

        # 保留前 max_memories * 0.9 条
        keep_count = int(self.max_memories * 0.9)
        to_delete = all_entries[keep_count:]

        # 删除
        deleted = 0
        for entry in to_delete:
            if await self.store.delete(entry.id):
                deleted += 1

        logger.info(f"Consolidation complete: deleted {deleted} memories, kept {keep_count}")

    async def close(self) -> None:
        """关闭管理器"""
        await self.store.close()
        logger.info("MemoryManager closed")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
