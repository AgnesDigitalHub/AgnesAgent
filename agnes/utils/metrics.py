"""
性能监控和指标收集

提供性能指标收集、统计和报告功能
"""

import logging
import time
from collections import defaultdict
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class MetricValue:
    """指标值"""

    count: int = 0
    total: float = 0.0
    min_val: float = float("inf")
    max_val: float = float("-inf")
    values: list[float] = field(default_factory=list)

    def record(self, value: float) -> None:
        """记录值"""
        self.count += 1
        self.total += value
        self.min_val = min(self.min_val, value)
        self.max_val = max(self.max_val, value)
        # 只保留最近100个值用于计算百分位数
        self.values.append(value)
        if len(self.values) > 100:
            self.values.pop(0)

    @property
    def avg(self) -> float:
        """平均值"""
        return self.total / self.count if self.count > 0 else 0.0

    @property
    def p95(self) -> float:
        """95百分位数"""
        if not self.values:
            return 0.0
        sorted_values = sorted(self.values)
        idx = int(len(sorted_values) * 0.95)
        return sorted_values[min(idx, len(sorted_values) - 1)]

    @property
    def p99(self) -> float:
        """99百分位数"""
        if not self.values:
            return 0.0
        sorted_values = sorted(self.values)
        idx = int(len(sorted_values) * 0.99)
        return sorted_values[min(idx, len(sorted_values) - 1)]

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "count": self.count,
            "avg": round(self.avg, 4),
            "min": round(self.min_val, 4) if self.min_val != float("inf") else None,
            "max": round(self.max_val, 4) if self.max_val != float("-inf") else None,
            "p95": round(self.p95, 4),
            "p99": round(self.p99, 4),
        }


class MetricsCollector:
    """
    指标收集器

    收集和统计各种性能指标
    """

    _instance: "MetricsCollector | None" = None

    def __new__(cls) -> "MetricsCollector":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, MetricValue] = defaultdict(MetricValue)
        self._timers: dict[str, MetricValue] = defaultdict(MetricValue)
        self._initialized = True

    def increment(self, name: str, value: int = 1, tags: dict[str, str] | None = None) -> None:
        """
        增加计数器

        Args:
            name: 指标名称
            value: 增加值
            tags: 标签
        """
        key = self._make_key(name, tags)
        self._counters[key] += value

    def decrement(self, name: str, value: int = 1, tags: dict[str, str] | None = None) -> None:
        """减少计数器"""
        key = self._make_key(name, tags)
        self._counters[key] -= value

    def gauge(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """
        设置仪表盘值

        Args:
            name: 指标名称
            value: 当前值
            tags: 标签
        """
        key = self._make_key(name, tags)
        self._gauges[key] = value

    def histogram(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """
        记录直方图值

        Args:
            name: 指标名称
            value: 值
            tags: 标签
        """
        key = self._make_key(name, tags)
        self._histograms[key].record(value)

    def timer(self, name: str, duration_ms: float, tags: dict[str, str] | None = None) -> None:
        """
        记录计时器

        Args:
            name: 指标名称
            duration_ms: 耗时（毫秒）
            tags: 标签
        """
        key = self._make_key(name, tags)
        self._timers[key].record(duration_ms)

    @contextmanager
def measure_time(self, name: str, tags: dict[str, str] | None = None):
        """
        上下文管理器：测量代码块执行时间

        Example:
            >>> with metrics.measure_time("llm_call"):
            ...     result = await llm.chat(messages)
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self.timer(name, duration_ms, tags)

    def _make_key(self, name: str, tags: dict[str, str] | None = None) -> str:
        """生成指标键"""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"

    def get_report(self) -> dict[str, Any]:
        """获取指标报告"""
        return {
            "counters": dict(self._counters),
            "gauges": self._gauges.copy(),
            "histograms": {k: v.to_dict() for k, v in self._histograms.items()},
            "timers": {k: v.to_dict() for k, v in self._timers.items()},
        }

    def reset(self) -> None:
        """重置所有指标"""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._timers.clear()

    def log_summary(self) -> None:
        """记录指标摘要"""
        report = self.get_report()

        logger.info("=== Performance Metrics Summary ===")

        if report["counters"]:
            logger.info("Counters:")
            for name, value in report["counters"].items():
                logger.info(f"  {name}: {value}")

        if report["timers"]:
            logger.info("Timers (ms):")
            for name, stats in report["timers"].items():
                logger.info(
                    f"  {name}: avg={stats['avg']:.2f}, "
                    f"p95={stats['p95']:.2f}, p99={stats['p99']:.2f}, "
                    f"count={stats['count']}"
                )

        if report["histograms"]:
            logger.info("Histograms:")
            for name, stats in report["histograms"].items():
                logger.info(
                    f"  {name}: avg={stats['avg']:.2f}, "
                    f"min={stats['min']}, max={stats['max']}, "
                    f"count={stats['count']}"
                )


# 全局指标收集器实例
metrics = MetricsCollector()


def timed(name: str | None = None, tags: dict[str, str] | None = None):
    """
    装饰器：测量函数执行时间

    Args:
        name: 指标名称（默认为函数名）
        tags: 标签

    Example:
        >>> @timed("llm_call", {"model": "gpt-4"})
        ... async def chat_with_llm(messages):
        ...     return await llm.chat(messages)
    """

    def decorator(func: F) -> F:
        metric_name = name or func.__name__

        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with metrics.measure_time(metric_name, tags):
                return await func(*args, **kwargs)

        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with metrics.measure_time(metric_name, tags):
                return func(*args, **kwargs)

        import asyncio
        from functools import wraps

        if asyncio.iscoroutinefunction(func):
            return wraps(func)(async_wrapper)
        return wraps(func)(sync_wrapper)

    return decorator


def counted(name: str | None = None, tags: dict[str, str] | None = None):
    """
    装饰器：统计函数调用次数

    Args:
        name: 指标名称（默认为函数名）
        tags: 标签
    """

    def decorator(func: F) -> F:
        metric_name = name or f"{func.__name__}_calls"

        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            metrics.increment(metric_name, tags=tags)
            return await func(*args, **kwargs)

        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            metrics.increment(metric_name, tags=tags)
            return func(*args, **kwargs)

        import asyncio
        from functools import wraps

        if asyncio.iscoroutinefunction(func):
            return wraps(func)(async_wrapper)
        return wraps(func)(sync_wrapper)

    return decorator
