"""
文本嵌入器
将文本转换为向量表示

提供多种嵌入实现：
- SimpleEmbedder: 基于词频的简单实现，无需外部依赖
- OpenAIEmbedder: 使用 OpenAI API
- CachedEmbedder: 带缓存的嵌入器包装器
"""

import hashlib
import math
import re
from abc import ABC, abstractmethod
from typing import Any

from agnes.utils.cache import LRUCache
from agnes.utils.logger import get_logger

logger = get_logger(__name__)


class Embedder(ABC):
    """嵌入器抽象基类"""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """将文本转换为向量"""
        pass

    @abstractmethod
    def dimension(self) -> int:
        """返回向量维度"""
        pass


class SimpleEmbedder(Embedder):
    """
    简单文本嵌入器

    基于词频和哈希的简单实现，无需外部依赖
    适合测试和轻量级应用

    原理：
    1. 将文本分词
    2. 对每个词计算哈希值
    3. 统计词频并加权
    4. 归一化得到固定维度的向量
    """

    def __init__(self, dimension: int = 384):
        """
        初始化嵌入器

        Args:
            dimension: 向量维度（默认384，与all-MiniLM-L6-v2兼容）
        """
        self._dimension = dimension
        self._stopwords = {
            "的",
            "了",
            "在",
            "是",
            "我",
            "有",
            "和",
            "就",
            "不",
            "人",
            "都",
            "一",
            "一个",
            "上",
            "也",
            "很",
            "到",
            "说",
            "要",
            "去",
            "你",
            "会",
            "着",
            "没有",
            "看",
            "好",
            "自己",
            "这",
            "那",
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "need",
            "dare",
            "ought",
            "used",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "and",
            "but",
            "or",
            "yet",
            "so",
            "if",
            "because",
            "although",
            "though",
            "while",
            "where",
            "when",
            "that",
            "which",
            "who",
            "whom",
            "whose",
            "what",
            "this",
            "these",
            "those",
            "i",
            "me",
            "my",
            "myself",
            "we",
            "our",
            "you",
            "your",
            "he",
            "him",
            "his",
            "she",
            "her",
            "it",
            "its",
            "they",
            "them",
            "their",
            "what",
            "which",
            "who",
        }

    async def embed(self, text: str) -> list[float]:
        """将文本转换为向量"""
        if not text:
            return [0.0] * self._dimension

        # 分词
        tokens = self._tokenize(text)

        # 计算词频
        token_freq = {}
        for token in tokens:
            if token not in self._stopwords and len(token) > 1:
                token_freq[token] = token_freq.get(token, 0) + 1

        # 构建向量
        vector = [0.0] * self._dimension

        for token, freq in token_freq.items():
            # 使用哈希确定位置
            hash_value = hashlib.md5(token.encode()).hexdigest()

            # 将哈希转换为多个维度
            for i in range(0, min(48, len(hash_value)), 2):
                idx = int(hash_value[i : i + 2], 16) % self._dimension
                # TF-IDF 风格的加权
                weight = freq * (1 + math.log1p(len(token)))
                vector[idx] += weight

        # 归一化
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector

    def _tokenize(self, text: str) -> list[str]:
        """简单分词"""
        # 中文：按字符
        # 英文：按单词
        # 统一转小写
        text = text.lower()

        # 提取中文字符
        chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)

        # 提取英文单词
        english_words = re.findall(r"[a-z]+", text)

        return chinese_chars + english_words

    def dimension(self) -> int:
        """返回向量维度"""
        return self._dimension


class OpenAIEmbedder(Embedder):
    """
    OpenAI API 嵌入器

    使用 OpenAI 的 text-embedding-ada-002 或其他嵌入模型
    需要 API key
    """

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-ada-002",
        base_url: str | None = None,
    ):
        """
        初始化 OpenAI 嵌入器

        Args:
            api_key: OpenAI API key
            model: 嵌入模型名称
            base_url: 自定义 base URL（用于兼容 API）
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
        self._client = None

    async def embed(self, text: str) -> list[float]:
        """使用 OpenAI API 嵌入文本（带连接池优化）"""
        if not self._client:
            try:
                from openai import AsyncOpenAI
                import httpx

                # 配置连接池
                limits = httpx.Limits(
                    max_keepalive_connections=5,
                    max_connections=10,
                )
                http_client = httpx.AsyncClient(
                    timeout=60.0,
                    limits=limits,
                )

                self._client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    http_client=http_client,
                )
            except ImportError:
                raise ImportError("openai package is required for OpenAIEmbedder")

        try:
            response = await self._client.embeddings.create(
                model=self.model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise

    def dimension(self) -> int:
        """返回向量维度"""
        # text-embedding-ada-002 是 1536 维
        # text-embedding-3-small 是 1536 维
        # text-embedding-3-large 是 3072 维
        dimensions = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
        }
        return dimensions.get(self.model, 1536)


class MockEmbedder(Embedder):
    """
    模拟嵌入器

    用于测试，返回随机向量
    """

    def __init__(self, dimension: int = 384, seed: int = 42):
        self._dimension = dimension
        self._seed = seed

    async def embed(self, text: str) -> list[float]:
        """生成确定性随机向量"""
        import random

        # 使用文本哈希作为种子，确保相同文本得到相同向量
        hash_value = hashlib.md5(text.encode()).hexdigest()
        seed = int(hash_value[:8], 16) + self._seed
        rng = random.Random(seed)

        vector = [rng.uniform(-1, 1) for _ in range(self._dimension)]

        # 归一化
        norm = math.sqrt(sum(x * x for x in vector))
        return [x / norm for x in vector]

    def dimension(self) -> int:
        return self._dimension


class CachedEmbedder(Embedder):
    """
    带缓存的嵌入器包装器

    缓存相同文本的嵌入结果，避免重复计算或 API 调用
    特别适用于：
    - 频繁查询相同或相似文本
    - 需要减少 API 调用次数的场景
    """

    def __init__(
        self,
        embedder: Embedder,
        cache_size: int = 1000,
        enable_stats: bool = True,
    ):
        """
        初始化缓存嵌入器

        Args:
            embedder: 底层嵌入器实例
            cache_size: 缓存大小
            enable_stats: 是否启用统计信息
        """
        self._embedder = embedder
        self._cache = LRUCache(maxsize=cache_size)
        self._enable_stats = enable_stats

    async def embed(self, text: str) -> list[float]:
        """嵌入文本（带缓存）"""
        if not text:
            return [0.0] * self.dimension()

        # 生成缓存键（文本的 MD5 哈希）
        cache_key = hashlib.md5(text.encode()).hexdigest()

        # 检查缓存
        cached_result = self._cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Embedder cache hit for text: {text[:50]}...")
            return cached_result

        # 缓存未命中，调用底层嵌入器
        logger.debug(f"Embedder cache miss for text: {text[:50]}...")
        result = await self._embedder.embed(text)

        # 存入缓存
        self._cache.set(cache_key, result)

        return result

    def dimension(self) -> int:
        """返回向量维度"""
        return self._embedder.dimension()

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        if not self._enable_stats:
            return {"enabled": False}

        return {
            "enabled": True,
            "size": self._cache.size(),
            "maxsize": self._cache.maxsize,
            "hits": self._cache.hits,
            "misses": self._cache.misses,
            "hit_rate": self._cache.hit_rate(),
        }

    def clear_cache(self) -> None:
        """清除缓存"""
        self._cache.clear()
        logger.info("Embedder cache cleared")


def create_embedder(
    embedder_type: str = "simple",
    enable_cache: bool = True,
    cache_size: int = 1000,
    **kwargs: Any,
) -> Embedder:
    """
    工厂函数：创建嵌入器

    Args:
        embedder_type: 嵌入器类型 (simple/openai/mock)
        enable_cache: 是否启用缓存
        cache_size: 缓存大小
        **kwargs: 额外参数

    Returns:
        Embedder: 嵌入器实例
    """
    if embedder_type == "simple":
        embedder = SimpleEmbedder(**kwargs)
    elif embedder_type == "openai":
        embedder = OpenAIEmbedder(**kwargs)
    elif embedder_type == "mock":
        embedder = MockEmbedder(**kwargs)
    else:
        raise ValueError(f"Unknown embedder type: {embedder_type}")

    # 包装缓存层
    if enable_cache:
        embedder = CachedEmbedder(embedder, cache_size=cache_size)

    return embedder
