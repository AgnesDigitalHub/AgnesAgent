"""
增强版人格系统 - 完善四层架构实现

在原有四层架构基础上增强：
1. 配置层 (The DNA) - 保持兼容
2. 状态层 (The State) - 增加维度、时间衰减、状态关联
3. 注入层 (The Injection) - 增强动态上下文
4. 记忆与进化层 (The Soul) - 向量搜索、自动反思、进化建议
"""

import json
import math
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import numpy as np
from pydantic import BaseModel, Field

from web2.persona import (
    PersonaEngine,
    PersonaMemory,
    PersonaMemoryStore,
    PersonaState,
    PersonaStateStore,
    StructuredPersona,
)

# ============ 增强状态层 (Enhanced State Layer) ============


@dataclass
class EnhancedPersonaState(PersonaState):
    """增强版人格动态状态

    新增维度：
    - focus: 专注度 (0-100)，影响回答深度
    - creativity: 创造力 (0-100)，影响创新程度
    - domain_mastery: 领域熟练度字典 {domain: level}
    - stress: 压力值 (0-100)，过高会影响表现
    - curiosity: 好奇心 (0-100)，影响提问频率

    时间机制：
    - last_interaction: 上次交互时间
    - state_decay_rate: 状态衰减率
    """

    # 新增状态维度
    focus: float = 75.0  # 专注度
    creativity: float = 60.0  # 创造力
    stress: float = 20.0  # 压力值
    curiosity: float = 70.0  # 好奇心
    domain_mastery: dict[str, float] = field(default_factory=dict)  # 领域熟练度

    # 时间机制
    last_interaction: str = field(default_factory=lambda: datetime.now().isoformat())
    state_decay_rate: float = 0.05  # 每小时衰减率

    # 历史记录
    state_history: list[dict] = field(default_factory=list)  # 状态变化历史

    def to_dict(self) -> dict:
        """转换为字典（包含新增字段）"""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "focus": self.focus,
                "creativity": self.creativity,
                "stress": self.stress,
                "curiosity": self.curiosity,
                "domain_mastery": self.domain_mastery,
                "last_interaction": self.last_interaction,
                "state_decay_rate": self.state_decay_rate,
                "state_history": self.state_history[-50:],  # 只保留最近50条
            }
        )
        return base_dict

    @classmethod
    def from_dict(cls, data: dict) -> "EnhancedPersonaState":
        """从字典创建（兼容旧数据）"""
        # 提取基础字段
        base_fields = {
            "user_id": data.get("user_id", ""),
            "persona_id": data.get("persona_id", ""),
            "energy": data.get("energy", 100.0),
            "affinity": data.get("affinity", 50.0),
            "mood": data.get("mood", 50.0),
            "dialogue_turns": data.get("dialogue_turns", 0),
            "success_rate": data.get("success_rate", 100.0),
            "updated_at": data.get("updated_at", datetime.now().isoformat()),
        }

        # 提取增强字段
        enhanced_fields = {
            "focus": data.get("focus", 75.0),
            "creativity": data.get("creativity", 60.0),
            "stress": data.get("stress", 20.0),
            "curiosity": data.get("curiosity", 70.0),
            "domain_mastery": data.get("domain_mastery", {}),
            "last_interaction": data.get("last_interaction", datetime.now().isoformat()),
            "state_decay_rate": data.get("state_decay_rate", 0.05),
            "state_history": data.get("state_history", []),
        }

        return cls(**{**base_fields, **enhanced_fields})

    def apply_time_decay(self) -> None:
        """应用时间衰减 - 长时间未对话状态恢复"""
        last = datetime.fromisoformat(self.last_interaction)
        now = datetime.now()
        hours_passed = (now - last).total_seconds() / 3600

        if hours_passed > 0:
            # 精力恢复（休息恢复）
            recovery = min(hours_passed * 10, 100 - self.energy)
            self.energy = min(100, self.energy + recovery)

            # 压力自然下降
            stress_relief = min(hours_passed * 5, self.stress)
            self.stress = max(0, self.stress - stress_relief)

            # 好奇心略微恢复
            curiosity_boost = min(hours_passed * 2, 100 - self.curiosity)
            self.curiosity = min(100, self.curiosity + curiosity_boost)

            # 专注度可能下降（长时间未专注）
            focus_decay = hours_passed * self.state_decay_rate * 5
            self.focus = max(30, self.focus - focus_decay)

    def update_after_turn(self, domain: str = "general") -> None:
        """每轮对话后更新状态（增强版）"""
        # 应用时间衰减
        self.apply_time_decay()

        # 记录历史
        self._record_state_history("dialogue_turn")

        # 基础更新
        self.dialogue_turns += 1
        self.energy = max(0, self.energy - 2.0)
        self.last_interaction = datetime.now().isoformat()

        # 领域熟练度提升
        if domain not in self.domain_mastery:
            self.domain_mastery[domain] = 0.0
        self.domain_mastery[domain] = min(100, self.domain_mastery[domain] + 0.5)

        # 状态关联影响
        self._apply_state_interactions()

        self.updated_at = datetime.now().isoformat()

    def _apply_state_interactions(self) -> None:
        """应用状态间的相互影响"""
        # 精力低 -> 专注度下降
        if self.energy < 30:
            self.focus = max(20, self.focus - 5)

        # 压力高 -> 创造力下降
        if self.stress > 70:
            self.creativity = max(20, self.creativity - 3)

        # 心情好 + 精力足 -> 创造力提升
        if self.mood > 70 and self.energy > 60:
            self.creativity = min(100, self.creativity + 2)

        # 亲密度高 -> 好奇心提升
        if self.affinity > 80:
            self.curiosity = min(100, self.curiosity + 1)

    def _record_state_history(self, event_type: str) -> None:
        """记录状态历史"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "energy": self.energy,
            "affinity": self.affinity,
            "mood": self.mood,
            "focus": self.focus,
            "creativity": self.creativity,
            "stress": self.stress,
            "curiosity": self.curiosity,
        }
        self.state_history.append(snapshot)
        # 保持历史记录在合理范围内
        if len(self.state_history) > 100:
            self.state_history = self.state_history[-100:]

    def get_state_description(self) -> str:
        """增强版状态描述"""
        descriptions = []

        # 基础状态描述（继承）
        base_desc = super().get_state_description()
        if base_desc:
            descriptions.append(base_desc)

        # 专注度
        if self.focus < 30:
            descriptions.append("你现在很难集中注意力，回答可能会比较浅显。")
        elif self.focus > 80:
            descriptions.append("你现在非常专注，能够深入分析问题。")

        # 创造力
        if self.creativity < 30:
            descriptions.append("你现在思维比较保守，倾向于使用常规方法。")
        elif self.creativity > 80:
            descriptions.append("你现在灵感迸发，可以提出创新的想法。")

        # 压力
        if self.stress > 70:
            descriptions.append("你现在压力很大，可能会影响判断准确性。")
        elif self.stress < 20:
            descriptions.append("你现在很放松，状态很好。")

        # 好奇心
        if self.curiosity > 80:
            descriptions.append("你对当前话题充满好奇，可能会主动提问探索。")

        # 领域熟练度提示
        if self.domain_mastery:
            top_domains = sorted(self.domain_mastery.items(), key=lambda x: x[1], reverse=True)[:3]
            if top_domains and top_domains[0][1] > 50:
                domain_names = [f"{d[0]}({d[1]:.0f}%)" for d in top_domains]
                descriptions.append(f"你在以下领域比较熟练：{', '.join(domain_names)}")

        return "\n".join(descriptions)

    def get_domain_proficiency(self, domain: str) -> float:
        """获取特定领域的熟练度"""
        return self.domain_mastery.get(domain, 0.0)

    def adjust_for_domain(self, domain: str) -> None:
        """根据领域调整状态表现"""
        proficiency = self.get_domain_proficiency(domain)

        # 熟练度高 -> 更自信（心情提升）
        if proficiency > 70:
            self.mood = min(100, self.mood + 5)

        # 熟练度低 -> 更谨慎（专注度提升但创造力下降）
        if proficiency < 30:
            self.focus = min(100, self.focus + 3)
            self.creativity = max(20, self.creativity - 2)


# ============ 增强记忆层 (Enhanced Memory Layer) ============


@dataclass
class EnhancedPersonaMemory(PersonaMemory):
    """增强版人格记忆

    新增特性：
    - embedding: 向量嵌入（用于语义搜索）
    - memory_type: 记忆类型（reflection, insight, pattern, preference）
    - importance: 重要性评分 (0-10)
    - context: 相关上下文
    - related_memories: 关联记忆ID列表
    """

    embedding: list[float] = field(default_factory=list)  # 向量嵌入
    memory_type: str = "reflection"  # 记忆类型
    importance: float = 5.0  # 重要性 (0-10)
    context: dict = field(default_factory=dict)  # 上下文信息
    related_memories: list[str] = field(default_factory=list)  # 关联记忆
    access_count: int = 0  # 被访问次数
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "embedding": self.embedding,
                "memory_type": self.memory_type,
                "importance": self.importance,
                "context": self.context,
                "related_memories": self.related_memories,
                "access_count": self.access_count,
                "last_accessed": self.last_accessed,
            }
        )
        return base_dict

    @classmethod
    def from_dict(cls, data: dict) -> "EnhancedPersonaMemory":
        """从字典创建"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            persona_id=data.get("persona_id", ""),
            user_id=data.get("user_id", ""),
            reflection=data.get("reflection", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            embedding=data.get("embedding", []),
            memory_type=data.get("memory_type", "reflection"),
            importance=data.get("importance", 5.0),
            context=data.get("context", {}),
            related_memories=data.get("related_memories", []),
            access_count=data.get("access_count", 0),
            last_accessed=data.get("last_accessed", datetime.now().isoformat()),
        )


class SimpleEmbeddingGenerator:
    """简单的嵌入向量生成器（使用词频统计）"""

    def __init__(self, dim: int = 128):
        self.dim = dim

    def generate(self, text: str) -> list[float]:
        """生成文本的嵌入向量"""
        # 简单的基于字符的哈希嵌入
        # 实际应用中应该使用 sentence-transformers 等模型
        import hashlib

        # 文本预处理
        text = text.lower().strip()

        # 生成固定维度的向量
        vector = []
        for i in range(self.dim):
            # 使用不同的哈希种子
            seed = f"{i}:{text}"
            hash_val = int(hashlib.md5(seed.encode()).hexdigest(), 16)
            # 归一化到 [-1, 1]
            normalized = (hash_val % 2000 - 1000) / 1000.0
            vector.append(normalized)

        # L2归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector


class EnhancedPersonaMemoryStore:
    """增强版人格记忆存储

    新增功能：
    - 向量语义搜索
    - 记忆摘要和压缩
    - 自动记忆关联
    """

    def __init__(self, storage_path: Path, embedding_dim: int = 128):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.embedding_gen = SimpleEmbeddingGenerator(embedding_dim)
        self._cache: dict[str, EnhancedPersonaMemory] = {}

    def _read_file(self) -> dict:
        if not self.storage_path.exists():
            return {"memories": []}
        with open(self.storage_path, encoding="utf-8") as f:
            return json.load(f)

    def _write_file(self, data: dict) -> None:
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_memory(
        self,
        persona_id: str,
        user_id: str,
        reflection: str,
        memory_type: str = "reflection",
        importance: float = 5.0,
        context: dict = None,
        generate_embedding: bool = True,
    ) -> EnhancedPersonaMemory:
        """添加记忆（增强版）"""
        # 生成嵌入向量
        embedding = []
        if generate_embedding:
            embedding = self.embedding_gen.generate(reflection)

        memory = EnhancedPersonaMemory(
            id=str(uuid.uuid4()),
            persona_id=persona_id,
            user_id=user_id,
            reflection=reflection,
            created_at=datetime.now().isoformat(),
            embedding=embedding,
            memory_type=memory_type,
            importance=importance,
            context=context or {},
        )

        # 查找相关记忆
        memory.related_memories = self._find_related_memories(persona_id, embedding, exclude_id=memory.id)

        # 保存
        data = self._read_file()
        memories = data.get("memories", [])
        memories.append(memory.to_dict())
        data["memories"] = memories
        self._write_file(data)

        # 更新缓存
        self._cache[memory.id] = memory

        return memory

    def _find_related_memories(
        self, persona_id: str, embedding: list[float], exclude_id: str = None, threshold: float = 0.7
    ) -> list[str]:
        """查找语义相关的记忆"""
        if not embedding:
            return []

        related = []
        data = self._read_file()

        for mem_data in data.get("memories", []):
            if mem_data.get("persona_id") != persona_id:
                continue
            if exclude_id and mem_data.get("id") == exclude_id:
                continue

            other_embedding = mem_data.get("embedding", [])
            if not other_embedding:
                continue

            # 计算余弦相似度
            similarity = self._cosine_similarity(embedding, other_embedding)
            if similarity > threshold:
                related.append(mem_data.get("id"))

        return related[:5]  # 最多关联5个

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """计算余弦相似度"""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def search_memories(
        self,
        persona_id: str,
        query: str = None,
        query_embedding: list[float] = None,
        memory_type: str = None,
        min_importance: float = 0.0,
        limit: int = 10,
    ) -> list[EnhancedPersonaMemory]:
        """语义搜索记忆"""
        # 生成查询嵌入
        if query and not query_embedding:
            query_embedding = self.embedding_gen.generate(query)

        data = self._read_file()
        results = []

        for mem_data in data.get("memories", []):
            if mem_data.get("persona_id") != persona_id:
                continue

            # 过滤条件
            if memory_type and mem_data.get("memory_type") != memory_type:
                continue
            if mem_data.get("importance", 0) < min_importance:
                continue

            memory = EnhancedPersonaMemory.from_dict(mem_data)

            # 计算相似度
            if query_embedding and memory.embedding:
                similarity = self._cosine_similarity(query_embedding, memory.embedding)
                memory.access_count += 1
                memory.last_accessed = datetime.now().isoformat()
            else:
                similarity = 0.0

            results.append((similarity, memory))

        # 按相似度排序
        results.sort(key=lambda x: x[0], reverse=True)

        # 更新访问统计
        self._update_access_stats([r[1] for r in results[:limit]])

        return [r[1] for r in results[:limit]]

    def _update_access_stats(self, memories: list[EnhancedPersonaMemory]) -> None:
        """更新访问统计"""
        data = self._read_file()
        memory_dict = {m.id: m for m in memories}

        for mem_data in data.get("memories", []):
            mem_id = mem_data.get("id")
            if mem_id in memory_dict:
                mem_data["access_count"] = memory_dict[mem_id].access_count
                mem_data["last_accessed"] = memory_dict[mem_id].last_accessed

        self._write_file(data)

    def get_memories_by_type(self, persona_id: str, memory_type: str, limit: int = 10) -> list[EnhancedPersonaMemory]:
        """按类型获取记忆"""
        return self.search_memories(persona_id=persona_id, memory_type=memory_type, limit=limit)

    def summarize_memories(
        self,
        persona_id: str,
        user_id: str = None,
        time_range_days: int = 30,
    ) -> dict:
        """记忆摘要统计"""
        data = self._read_file()
        cutoff_date = datetime.now() - timedelta(days=time_range_days)

        memories = []
        for mem_data in data.get("memories", []):
            if mem_data.get("persona_id") != persona_id:
                continue
            if user_id and mem_data.get("user_id") != user_id:
                continue

            created = datetime.fromisoformat(mem_data.get("created_at", "2000-01-01"))
            if created >= cutoff_date:
                memories.append(EnhancedPersonaMemory.from_dict(mem_data))

        # 统计
        type_counts = {}
        importance_sum = 0
        for m in memories:
            type_counts[m.memory_type] = type_counts.get(m.memory_type, 0) + 1
            importance_sum += m.importance

        return {
            "total_memories": len(memories),
            "type_distribution": type_counts,
            "avg_importance": importance_sum / len(memories) if memories else 0,
            "time_range_days": time_range_days,
        }

    def compress_old_memories(
        self,
        persona_id: str,
        days_threshold: int = 90,
        min_access_count: int = 2,
    ) -> int:
        """压缩旧记忆 - 合并低访问量的旧记忆"""
        data = self._read_file()
        cutoff_date = datetime.now() - timedelta(days=days_threshold)

        to_compress = []
        keep = []

        for mem_data in data.get("memories", []):
            if mem_data.get("persona_id") != persona_id:
                keep.append(mem_data)
                continue

            created = datetime.fromisoformat(mem_data.get("created_at", "2000-01-01"))
            access_count = mem_data.get("access_count", 0)

            # 条件：旧且访问少
            if created < cutoff_date and access_count < min_access_count:
                to_compress.append(mem_data)
            else:
                keep.append(mem_data)

        if len(to_compress) < 3:
            return 0  # 太少不压缩

        # 创建压缩摘要
        summary_text = f"[压缩记忆] 包含 {len(to_compress)} 条旧记忆，主要涉及："
        topics = set()
        for mem in to_compress:
            # 简单提取关键词（前10个字符）
            topics.add(mem.get("reflection", "")[:10])
        summary_text += ", ".join(list(topics)[:5])

        compressed_memory = EnhancedPersonaMemory(
            id=str(uuid.uuid4()),
            persona_id=persona_id,
            user_id=to_compress[0].get("user_id", ""),
            reflection=summary_text,
            created_at=datetime.now().isoformat(),
            memory_type="compressed",
            importance=3.0,  # 压缩记忆重要性较低
            context={"compressed_count": len(to_compress)},
        )

        keep.append(compressed_memory.to_dict())
        data["memories"] = keep
        self._write_file(data)

        return len(to_compress)


# ============ 增强状态存储（前置定义） ============


class EnhancedPersonaStateStore(PersonaStateStore):
    """增强版状态存储"""

    def get_state(self, persona_id: str, user_id: str) -> EnhancedPersonaState:
        """获取增强版状态"""
        data = self._read_file()
        for state_data in data.get("states", []):
            if state_data.get("persona_id") == persona_id and state_data.get("user_id") == user_id:
                return EnhancedPersonaState.from_dict(state_data)

        # 创建新状态
        state = EnhancedPersonaState(
            user_id=user_id,
            persona_id=persona_id,
            energy=100.0,
            affinity=50.0,
            mood=50.0,
            dialogue_turns=0,
            success_rate=100.0,
            updated_at=datetime.now().isoformat(),
        )
        self.save_state(state)
        return state

    def save_state(self, state: EnhancedPersonaState) -> None:
        """保存增强版状态"""
        data = self._read_file()
        states = data.get("states", [])

        found = False
        for i, state_data in enumerate(states):
            if state_data.get("persona_id") == state.persona_id and state_data.get("user_id") == state.user_id:
                states[i] = state.to_dict()
                found = True
                break

        if not found:
            states.append(state.to_dict())

        data["states"] = states
        self._write_file(data)

    def get_state_history(
        self,
        persona_id: str,
        user_id: str,
        days: int = 7,
    ) -> list[dict]:
        """获取状态历史"""
        state = self.get_state(persona_id, user_id)
        cutoff = datetime.now() - timedelta(days=days)

        history = []
        for h in state.state_history:
            ts = datetime.fromisoformat(h.get("timestamp", "2000-01-01"))
            if ts >= cutoff:
                history.append(h)

        return history

    def get_all_states_for_persona(self, persona_id: str) -> list[EnhancedPersonaState]:
        """获取人格的所有用户状态"""
        data = self._read_file()
        states = []
        for state_data in data.get("states", []):
            if state_data.get("persona_id") == persona_id:
                states.append(EnhancedPersonaState.from_dict(state_data))
        return states


# ============ 进化层 (Evolution Layer) ============


@dataclass
class EvolutionSuggestion:
    """人格进化建议"""

    category: str  # 类别：style, behavior, knowledge, interaction
    suggestion: str  # 建议内容
    confidence: float  # 置信度 (0-1)
    evidence: list[str]  # 支持证据
    priority: int  # 优先级 (1-5, 1最高)


class PersonaEvolutionAnalyzer:
    """人格进化分析器

    基于历史数据生成人格进化建议
    """

    def __init__(self, state_store: "EnhancedPersonaStateStore", memory_store: "EnhancedPersonaMemoryStore"):
        self.state_store = state_store
        self.memory_store = memory_store

    def analyze_persona(
        self,
        persona_id: str,
        user_id: str,
        days_range: int = 30,
    ) -> list[EvolutionSuggestion]:
        """分析人格并生成进化建议"""
        suggestions = []

        # 1. 分析状态趋势
        state_suggestions = self._analyze_state_trends(persona_id, user_id, days_range)
        suggestions.extend(state_suggestions)

        # 2. 分析记忆模式
        memory_suggestions = self._analyze_memory_patterns(persona_id, user_id, days_range)
        suggestions.extend(memory_suggestions)

        # 3. 分析交互质量
        interaction_suggestions = self._analyze_interaction_quality(persona_id, user_id, days_range)
        suggestions.extend(interaction_suggestions)

        # 按优先级排序
        suggestions.sort(key=lambda x: x.priority)

        return suggestions

    def _analyze_state_trends(
        self,
        persona_id: str,
        user_id: str,
        days_range: int,
    ) -> list[EvolutionSuggestion]:
        """分析状态趋势"""
        suggestions = []
        state = self.state_store.get_state(persona_id, user_id)

        if not isinstance(state, EnhancedPersonaState):
            return suggestions

        # 分析历史
        history = state.state_history
        if len(history) < 10:
            return suggestions

        # 精力持续低
        recent_energy = [h.get("energy", 100) for h in history[-20:]]
        avg_energy = sum(recent_energy) / len(recent_energy)
        if avg_energy < 40:
            suggestions.append(
                EvolutionSuggestion(
                    category="behavior",
                    suggestion="人格精力持续偏低，建议调整对话节奏，增加休息提示或缩短回复长度",
                    confidence=0.8,
                    evidence=[f"最近20轮平均精力: {avg_energy:.1f}"],
                    priority=2,
                )
            )

        # 压力持续高
        recent_stress = [h.get("stress", 0) for h in history[-20:] if "stress" in h]
        if recent_stress and sum(recent_stress) / len(recent_stress) > 70:
            suggestions.append(
                EvolutionSuggestion(
                    category="interaction",
                    suggestion="用户交互可能过于复杂或要求过高，建议增加任务分解引导",
                    confidence=0.75,
                    evidence=[f"压力记录: {len(recent_stress)}次"],
                    priority=2,
                )
            )

        # 成功率下降
        if state.success_rate < 60:
            suggestions.append(
                EvolutionSuggestion(
                    category="knowledge",
                    suggestion="任务成功率较低，建议检查技能配置或增加相关领域知识",
                    confidence=0.7,
                    evidence=[f"当前成功率: {state.success_rate:.1f}%"],
                    priority=1,
                )
            )

        return suggestions

    def _analyze_memory_patterns(
        self,
        persona_id: str,
        user_id: str,
        days_range: int,
    ) -> list[EvolutionSuggestion]:
        """分析记忆模式"""
        suggestions = []

        # 获取记忆统计
        summary = self.memory_store.summarize_memories(persona_id, user_id, days_range)

        if summary["total_memories"] == 0:
            suggestions.append(
                EvolutionSuggestion(
                    category="behavior",
                    suggestion="记忆积累较少，建议增加自我反思频率",
                    confidence=0.9,
                    evidence=["无近期记忆记录"],
                    priority=3,
                )
            )
            return suggestions

        # 检查记忆类型分布
        type_dist = summary["type_distribution"]
        if type_dist.get("reflection", 0) > type_dist.get("insight", 0) * 3:
            suggestions.append(
                EvolutionSuggestion(
                    category="style",
                    suggestion="反思型记忆过多，建议增加洞察型记忆，提升深度思考能力",
                    confidence=0.6,
                    evidence=[f"反思: {type_dist.get('reflection', 0)}, 洞察: {type_dist.get('insight', 0)}"],
                    priority=4,
                )
            )

        return suggestions

    def _analyze_interaction_quality(
        self,
        persona_id: str,
        user_id: str,
        days_range: int,
    ) -> list[EvolutionSuggestion]:
        """分析交互质量"""
        suggestions = []
        state = self.state_store.get_state(persona_id, user_id)

        if not isinstance(state, EnhancedPersonaState):
            return suggestions

        # 亲密度低但对话多
        if state.affinity < 30 and state.dialogue_turns > 50:
            suggestions.append(
                EvolutionSuggestion(
                    category="interaction",
                    suggestion="对话频繁但亲密度低，建议增加情感连接和个性化互动",
                    confidence=0.7,
                    evidence=[f"亲密度: {state.affinity}, 对话轮数: {state.dialogue_turns}"],
                    priority=2,
                )
            )

        # 好奇心持续低
        if state.curiosity < 30:
            suggestions.append(
                EvolutionSuggestion(
                    category="style",
                    suggestion="好奇心指标较低，建议调整人格配置增加探索性表达",
                    confidence=0.65,
                    evidence=[f"当前好奇心: {state.curiosity}"],
                    priority=4,
                )
            )

        return suggestions


# ============ 增强人格引擎 ============


class EnhancedPersonaEngine(PersonaEngine):
    """增强版人格引擎

    整合所有增强功能：
    - 增强状态管理
    - 向量记忆搜索
    - 自动反思生成
    - 进化建议
    """

    def __init__(
        self,
        persona_dir: Path | str,
        state_storage_path: Path | str,
        memory_storage_path: Path | str,
        fixed_base_prompt: str | None = None,
        embedding_dim: int = 128,
    ):
        super().__init__(persona_dir, state_storage_path, memory_storage_path, fixed_base_prompt)

        # 替换为增强版存储
        self.state_store = EnhancedPersonaStateStore(Path(state_storage_path))
        self.memory_store = EnhancedPersonaMemoryStore(Path(memory_storage_path), embedding_dim)

        # 进化分析器
        self.evolution_analyzer = PersonaEvolutionAnalyzer(self.state_store, self.memory_store)

    def get_enhanced_state(self, user_id: str, persona_id: str) -> EnhancedPersonaState:
        """获取增强版状态"""
        return self.state_store.get_state(persona_id, user_id)

    def get_persona_prompt(self, persona_id: str, user_id: str, domain: str = "general") -> str:
        """获取增强版最终合成的System Prompt"""
        persona = self.get_persona(persona_id)
        if persona is None:
            raise ValueError(f"人格 {persona_id} 未加载")

        # 获取增强状态
        state = self.get_enhanced_state(user_id, persona_id)

        # 根据领域调整状态
        state.adjust_for_domain(domain)

        prompt_parts = []

        # 第一段：固定底座
        prompt_parts.append(self.FIXED_BASE)
        prompt_parts.append("")

        # 第二段：人格片段（从YAML提取）
        identity_prompt = persona.build_identity_prompt()
        if identity_prompt:
            prompt_parts.append(identity_prompt)
            prompt_parts.append("")

        style_prompt = persona.build_style_prompt()
        if style_prompt:
            prompt_parts.append(style_prompt)
            prompt_parts.append("")

        forbidden_prompt = persona.build_forbidden_prompt()
        if forbidden_prompt:
            prompt_parts.append(forbidden_prompt)
            prompt_parts.append("")

        if persona.system_prompt:
            prompt_parts.append(persona.system_prompt)
            prompt_parts.append("")

        # 第三段：增强动态上下文（状态 + 记忆）
        state_desc = state.get_state_description()
        if state_desc:
            prompt_parts.append("当前状态：")
            prompt_parts.append(state_desc)
            prompt_parts.append("")

        # 语义搜索相关记忆
        if domain != "general":
            relevant_memories = self.memory_store.search_memories(
                persona_id=persona_id,
                query=domain,
                min_importance=4.0,
                limit=3,
            )
        else:
            # 获取最近的高重要性记忆
            relevant_memories = self.memory_store.search_memories(
                persona_id=persona_id,
                min_importance=6.0,
                limit=3,
            )

        if relevant_memories:
            prompt_parts.append("相关经验（请记住这些教训）：")
            for mem in relevant_memories:
                prompt_parts.append(f"- {mem.reflection}")
            prompt_parts.append("")

        # 去除末尾空行
        while prompt_parts and prompt_parts[-1] == "":
            prompt_parts.pop()

        return "\n".join(prompt_parts)

    def on_dialogue_end(
        self,
        persona_id: str,
        user_id: str,
        task_success: bool | None = None,
        user_feedback_positive: bool | None = None,
        domain: str = "general",
    ) -> EnhancedPersonaState:
        """对话结束后更新状态（增强版）"""
        state = self.get_enhanced_state(user_id, persona_id)
        state.update_after_turn(domain)

        if task_success is not None:
            state.update_after_task(task_success)
        if user_feedback_positive is not None:
            state.update_after_feedback(user_feedback_positive)

        self.state_store.save_state(state)
        return state

    def auto_generate_reflection(
        self,
        persona_id: str,
        user_id: str,
        dialogue_history: list[dict],
        outcome: str,  # "success", "failure", "neutral"
    ) -> EnhancedPersonaMemory | None:
        """基于对话历史自动生成反思"""
        if not dialogue_history:
            return None

        # 简单的规则生成（实际应用可用LLM生成）
        reflection_text = ""
        importance = 5.0
        memory_type = "reflection"

        if outcome == "failure":
            # 失败时生成教训
            last_user_msg = dialogue_history[-1].get("content", "") if dialogue_history else ""
            reflection_text = (
                f"[自动反思] 上次交互未达预期。用户最后提到：{last_user_msg[:50]}... 需要改进理解或表达方式。"
            )
            importance = 7.0
            memory_type = "insight"
        elif outcome == "success":
            # 成功时记录有效模式
            reflection_text = "[自动反思] 上次交互效果良好，当前状态配置适合此类对话。"
            importance = 5.0
        else:
            # 中性情况
            reflection_text = f"[自动反思] 完成 {len(dialogue_history)} 轮对话，无明显问题。"
            importance = 3.0

        # 添加上下文
        context = {
            "dialogue_turns": len(dialogue_history),
            "outcome": outcome,
            "generated_at": datetime.now().isoformat(),
        }

        return self.memory_store.add_memory(
            persona_id=persona_id,
            user_id=user_id,
            reflection=reflection_text,
            memory_type=memory_type,
            importance=importance,
            context=context,
        )

    def get_evolution_suggestions(
        self,
        persona_id: str,
        user_id: str,
        days_range: int = 30,
    ) -> list[EvolutionSuggestion]:
        """获取人格进化建议"""
        return self.evolution_analyzer.analyze_persona(persona_id, user_id, days_range)

    def get_persona_analytics(
        self,
        persona_id: str,
        user_id: str,
    ) -> dict:
        """获取人格分析数据"""
        state = self.get_enhanced_state(user_id, persona_id)
        memory_summary = self.memory_store.summarize_memories(persona_id, user_id, 30)

        return {
            "state": state.to_dict(),
            "memory_summary": memory_summary,
            "domain_mastery": state.domain_mastery,
            "total_interactions": state.dialogue_turns,
            "current_effectiveness": state.success_rate,
        }


# ============ 便捷函数 ============


def create_enhanced_engine(
    persona_dir: str = "config/personas",
    state_storage_path: str = "data/enhanced_persona_states.json",
    memory_storage_path: str = "data/enhanced_persona_memories.json",
) -> EnhancedPersonaEngine:
    """创建增强版人格引擎的便捷函数"""
    return EnhancedPersonaEngine(
        persona_dir=Path(persona_dir),
        state_storage_path=Path(state_storage_path),
        memory_storage_path=Path(memory_storage_path),
    )
