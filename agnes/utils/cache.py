"""
缓存工具

提供内存缓存和LRU缓存实现
"""

import functools
import hashlib
import logging
import time
from collections import OrderedDict
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class LRUCache:
    """
    LRU (Least Recently Used) 缓存

    固定大小的缓存，自动淘汰最少使用的条目
    """

    def __init__(self, maxsize: int = 128):
        """
        初始化缓存

        Args:
            maxsize: 最大缓存条目数
        """
        self.maxsize = maxsize
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        """获取缓存值"""
        if key in self._cache:
            # 移动到末尾（最近使用）
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
        self._misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        if key in self._cache:
            # 更新并移动到末尾
            self._cache.move_to_end(key)
        self._cache[key] = value

        # 淘汰最旧的条目
        if len(self._cache) > self.maxsize:
            self._cache.popitem(last=False)

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "maxsize": self.maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0.0,
        }


class TimedCache:
    """
    带过期时间的缓存
    """

    def __init__(self, ttl_seconds: float = 300.0):
        """
        初始化缓存

        Args:
            ttl_seconds: 默认过期时间（秒）
        """
        self.ttl = ttl_seconds
        self._cache: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any | None:
        """获取缓存值（自动检查过期）"""
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                return value
            # 过期，删除
            del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        """设置缓存值"""
        expiry = time.time() + (ttl or self.ttl)
        self._cache[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()

    def cleanup_expired(self) -> int:
        """清理过期条目，返回清理数量"""
        now = time.time()
        expired = [k for k, (_, expiry) in self._cache.items() if expiry < now]
        for k in expired:
            del self._cache[k]
        return len(expired)


def cached(maxsize: int = 128):
    """
    缓存装饰器

    用于缓存函数结果

    Example:
        @cached(maxsize=256)
        def expensive_function(x, y):
            return x * y
    """
    cache = LRUCache(maxsize)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # 构建缓存键
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key = hashlib.md5("|".join(key_parts).encode()).hexdigest()

            # 尝试从缓存获取
            result = cache.get(key)
            if result is not None:
                return result

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        # 附加缓存操作方法
        wrapper.cache = cache
        wrapper.cache_clear = cache.clear
        wrapper.cache_stats = cache.get_stats

        return wrapper

    return decorator


def async_cached(maxsize: int = 128):
    """
    异步缓存装饰器

    用于缓存异步函数结果
    """
    cache = LRUCache(maxsize)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 构建缓存键
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key = hashlib.md5("|".join(key_parts).encode()).hexdigest()

            # 尝试从缓存获取
            result = cache.get(key)
            if result is not None:
                return result

            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            cache.set(key, result)
            return result

        # 附加缓存操作方法
        wrapper.cache = cache
        wrapper.cache_clear = cache.clear
        wrapper.cache_stats = cache.get_stats

        return wrapper

    return decorator
