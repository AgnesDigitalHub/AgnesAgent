"""内存向量存储，支持缓存和索引加速"""

import logging
import math
from typing import Any

from agnes.memory.base import MemoryEntry, VectorStore
from agnes.utils.cache import LRUCache

logger = logging.getLogger(__name__)


class SimpleVectorStore(VectorStore):
    """内存向量存储，支持缓存和索引"""

    def __init__(self, name: str = "default", enable_cache: bool = True, enable_index: bool = True):
        """初始化存储"""
        self.name = name
        self._storage: dict[str, MemoryEntry] = {}
        self._cache = LRUCache(maxsize=100) if enable_cache else None
        self._enable_index = enable_index

        # 索引结构
        self._index_by_type: dict[str, set[str]] = {}  # memory_type -> entry_ids
        self._index_by_source: dict[str, set[str]] = {}  # source -> entry_ids
        self._vector_norms: dict[str, float] = {}  # entry_id -> precomputed norm

        logger.info(f"SimpleVectorStore '{name}' initialized (cache={'enabled' if enable_cache else 'disabled'}, index={'enabled' if enable_index else 'disabled'})")

    def _add_to_index(self, entry: MemoryEntry) -> None:
        if not self._enable_index:
            return

        # 类型索引
        if entry.memory_type not in self._index_by_type:
            self._index_by_type[entry.memory_type] = set()
        self._index_by_type[entry.memory_type].add(entry.id)

        # 来源索引
        if entry.source not in self._index_by_source:
            self._index_by_source[entry.source] = set()
        self._index_by_source[entry.source].add(entry.id)

        # 预计算向量范数
        if entry.embedding:
            self._vector_norms[entry.id] = math.sqrt(sum(x * x for x in entry.embedding))

    def _remove_from_index(self, entry_id: str) -> None:
        if not self._enable_index:
            return

        entry = self._storage.get(entry_id)
        if entry:
            # 从类型索引移除
            if entry.memory_type in self._index_by_type:
                self._index_by_type[entry.memory_type].discard(entry_id)

            # 从来源索引移除
            if entry.source in self._index_by_source:
                self._index_by_source[entry.source].discard(entry_id)

        # 移除向量范数
        self._vector_norms.pop(entry_id, None)

    def _get_candidates_by_filter(self, filter_dict: dict[str, Any] | None) -> set[str] | None:
        if not self._enable_index or not filter_dict:
            return None

        candidates: set[str] | None = None

        for key, value in filter_dict.items():
            if key == "memory_type" and value in self._index_by_type:
                ids = self._index_by_type[value]
                if candidates is None:
                    candidates = ids.copy()
                else:
                    candidates &= ids
            elif key == "source" and value in self._index_by_source:
                ids = self._index_by_source[value]
                if candidates is None:
                    candidates = ids.copy()
                else:
                    candidates &= ids
            else:
                # 无法使用索引，需要扫描全部
                return None

        return candidates

    async def add(self, entry: MemoryEntry) -> str:
        """添加记忆条目"""
        self._storage[entry.id] = entry
        # 添加到索引
        self._add_to_index(entry)
        # 清除缓存，因为新数据可能影响搜索结果
        if self._cache is not None:
            self._cache.clear()
        logger.debug(f"Added memory entry: {entry.id}")
        return entry.id

    async def get(self, entry_id: str) -> MemoryEntry | None:
        """获取记忆条目"""
        entry = self._storage.get(entry_id)
        if entry:
            entry.touch()
        return entry

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter_dict: dict[str, Any] | None = None,
    ) -> list[tuple[MemoryEntry, float]]:
        """
        向量相似度搜索

        使用余弦相似度计算，返回最相似的 top_k 条记忆
        支持查询缓存和索引加速以优化性能
        """
        if not self._storage:
            return []

        # 生成缓存键
        cache_key = self._generate_cache_key(query_embedding, top_k, filter_dict)

        # 检查缓存
        if self._cache is not None:
            cached_result = self._cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for search query")
                # 更新访问记录
                for entry, _ in cached_result:
                    entry.touch()
                return cached_result
            logger.debug(f"Cache miss for search query")

        results = []

        # 使用索引获取候选集
        candidate_ids = self._get_candidates_by_filter(filter_dict)

        if candidate_ids is not None:
            # 使用索引过滤，只扫描候选集
            entries_to_scan = [self._storage[eid] for eid in candidate_ids if eid in self._storage]
        else:
            # 无法使用索引，扫描全部
            entries_to_scan = list(self._storage.values())

        # 预计算查询向量范数
        query_norm = math.sqrt(sum(x * x for x in query_embedding))

        for entry in entries_to_scan:
            # 应用元数据过滤（索引无法处理的过滤条件）
            if filter_dict:
                match = True
                for key, value in filter_dict.items():
                    # 跳过已由索引处理的字段
                    if key in ("memory_type", "source"):
                        continue
                    if key in entry.metadata and entry.metadata[key] != value:
                        match = False
                        break
                if not match:
                    continue

            # 计算相似度（使用预计算的范数优化）
            if entry.embedding:
                if self._enable_index and entry.id in self._vector_norms:
                    # 使用预计算的范数
                    similarity = self._cosine_similarity_fast(
                        query_embedding, entry.embedding, query_norm, self._vector_norms[entry.id]
                    )
                else:
                    similarity = self._cosine_similarity(query_embedding, entry.embedding)
                results.append((entry, similarity))

        # 按相似度排序并返回 top_k
        results.sort(key=lambda x: x[1], reverse=True)
        top_results = results[:top_k]

        # 更新访问记录
        for entry, _ in top_results:
            entry.touch()

        # 存入缓存
        if self._cache is not None:
            self._cache.set(cache_key, top_results)

        return top_results

    def _cosine_similarity_fast(
        self,
        vec1: list[float],
        vec2: list[float],
        norm1: float,
        norm2: float,
    ) -> float:
        """
        快速余弦相似度计算（使用预计算的范数）

        Args:
            vec1: 向量1
            vec2: 向量2
            norm1: 向量1的预计算范数
            norm2: 向量2的预计算范数

        Returns:
            float: 相似度分数 [-1, 1]，越高越相似
        """
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _generate_cache_key(
        self,
        query_embedding: list[float],
        top_k: int,
        filter_dict: dict[str, Any] | None,
    ) -> str:
        """生成搜索缓存键"""
        import hashlib

        # 将向量转换为字符串（取前10维作为特征）
        vector_str = ",".join(f"{x:.6f}" for x in query_embedding[:10])

        # 组合过滤条件
        filter_str = ""
        if filter_dict:
            filter_str = str(sorted(filter_dict.items()))

        # 生成哈希
        key_str = f"{vector_str}|{top_k}|{filter_str}"
        return hashlib.md5(key_str.encode()).hexdigest()

    async def delete(self, entry_id: str) -> bool:
        """删除记忆条目"""
        if entry_id in self._storage:
            # 从索引移除
            self._remove_from_index(entry_id)
            del self._storage[entry_id]
            # 清除缓存
            if self._cache is not None:
                self._cache.clear()
            logger.debug(f"Deleted memory entry: {entry_id}")
            return True
        return False

    async def update(self, entry: MemoryEntry) -> bool:
        """更新记忆条目"""
        if entry.id in self._storage:
            # 从旧索引移除
            self._remove_from_index(entry.id)
            # 更新数据
            self._storage[entry.id] = entry
            # 添加到新索引
            self._add_to_index(entry)
            # 清除缓存
            if self._cache is not None:
                self._cache.clear()
            logger.debug(f"Updated memory entry: {entry.id}")
            return True
        return False

    async def list_all(
        self,
        memory_type: str | None = None,
        source: str | None = None,
        limit: int = 100,
    ) -> list[MemoryEntry]:
        """列出所有记忆条目"""
        entries = list(self._storage.values())

        # 应用过滤
        if memory_type:
            entries = [e for e in entries if e.memory_type == memory_type]
        if source:
            entries = [e for e in entries if e.source == source]

        # 按时间排序（最新的在前）
        entries.sort(key=lambda x: x.timestamp, reverse=True)

        return entries[:limit]

    async def count(self) -> int:
        """获取记忆条目总数"""
        return len(self._storage)

    async def clear(self) -> None:
        """清空所有记忆"""
        count = len(self._storage)
        self._storage.clear()
        # 清除索引
        if self._enable_index:
            self._index_by_type.clear()
            self._index_by_source.clear()
            self._vector_norms.clear()
        # 清除缓存
        if self._cache is not None:
            self._cache.clear()
        logger.info(f"Cleared {count} memory entries")

    async def close(self) -> None:
        """关闭存储（内存存储无需特殊处理）"""
        logger.info(f"SimpleVectorStore '{self.name}' closed")

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """
        计算余弦相似度

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            float: 相似度分数 [-1, 1]，越高越相似
        """
        if len(vec1) != len(vec2):
            raise ValueError(f"Vector dimensions mismatch: {len(vec1)} vs {len(vec2)}")

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def get_stats(self) -> dict[str, Any]:
        """获取存储统计信息"""
        entries = list(self._storage.values())

        stats = {
            "total": len(entries),
            "cache_enabled": self._cache is not None,
            "index_enabled": self._enable_index,
        }

        if self._cache is not None:
            stats["cache"] = {
                "size": self._cache.size(),
                "maxsize": self._cache.maxsize,
                "hits": self._cache.hits,
                "misses": self._cache.misses,
                "hit_rate": self._cache.hit_rate(),
            }

        if self._enable_index:
            stats["index"] = {
                "type_count": len(self._index_by_type),
                "source_count": len(self._index_by_source),
                "vector_norms_count": len(self._vector_norms),
            }

        if not entries:
            stats.update({
                "by_type": {},
                "by_source": {},
                "avg_importance": 0.0,
            })
            return stats

        by_type = {}
        by_source = {}
        total_importance = 0.0

        for entry in entries:
            by_type[entry.memory_type] = by_type.get(entry.memory_type, 0) + 1
            by_source[entry.source] = by_source.get(entry.source, 0) + 1
            total_importance += entry.importance

        stats.update({
            "by_type": by_type,
            "by_source": by_source,
            "avg_importance": total_importance / len(entries),
        })

        return stats
