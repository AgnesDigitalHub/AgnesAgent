"""
异步工具集

提供异步批处理、并发控制、超时处理等工具
"""

import asyncio
import logging
from collections.abc import AsyncGenerator, Callable, Coroutine, Iterable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


async def batch_process(
    items: Iterable[T],
    processor: Callable[[T], Coroutine[Any, Any, R]],
    batch_size: int = 10,
    concurrency: int = 5,
    timeout: float | None = None,
) -> list[R]:
    """
    批量异步处理

    Args:
        items: 待处理的项目列表
        processor: 异步处理函数
        batch_size: 每批处理的数量
        concurrency: 并发数限制
        timeout: 每个项目的超时时间

    Returns:
        list[R]: 处理结果列表

    Example:
        >>> async def process_item(item: str) -> str:
        ...     await asyncio.sleep(0.1)
        ...     return item.upper()
        >>>
        >>> results = await batch_process(
        ...     ["a", "b", "c"],
        ...     process_item,
        ...     batch_size=2,
        ...     concurrency=2
        ... )
    """
    semaphore = asyncio.Semaphore(concurrency)
    results: list[R] = []

    async def process_with_limit(item: T) -> R:
        async with semaphore:
            if timeout:
                return await asyncio.wait_for(processor(item), timeout=timeout)
            return await processor(item)

    # 分批处理
    item_list = list(items)
    for i in range(0, len(item_list), batch_size):
        batch = item_list[i : i + batch_size]
        batch_results = await asyncio.gather(
            *[process_with_limit(item) for item in batch],
            return_exceptions=True,
        )

        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Batch processing error: {result}")
                raise result
            results.append(result)

    return results


async def gather_with_concurrency(
    *coroutines: Coroutine[Any, Any, R],
    concurrency: int = 10,
    return_exceptions: bool = False,
) -> list[R]:
    """
    带并发限制的 gather

    Args:
        *coroutines: 协程列表
        concurrency: 最大并发数
        return_exceptions: 是否返回异常而不是抛出

    Returns:
        list[R]: 结果列表
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def with_limit(coro: Coroutine[Any, Any, R]) -> R:
        async with semaphore:
            return await coro

    return await asyncio.gather(
        *[with_limit(coro) for coro in coroutines],
        return_exceptions=return_exceptions,
    )


async def async_iter_with_timeout(
    async_iter: AsyncGenerator[T, None],
    timeout: float,
) -> AsyncGenerator[T, None]:
    """
    带超时的异步迭代器

    Args:
        async_iter: 异步迭代器
        timeout: 每次迭代的超时时间

    Yields:
        T: 迭代值
    """
    try:
        while True:
            try:
                item = await asyncio.wait_for(async_iter.__anext__(), timeout=timeout)
                yield item
            except StopAsyncIteration:
                break
    except asyncio.TimeoutError:
        logger.warning(f"Async iteration timeout after {timeout}s")
        raise


class AsyncRateLimiter:
    """
    异步速率限制器

    用于控制 API 调用频率
    """

    def __init__(self, max_calls: int, period: float = 60.0):
        """
        初始化速率限制器

        Args:
            max_calls: 周期内最大调用次数
            period: 周期长度（秒）
        """
        self.max_calls = max_calls
        self.period = period
        self._calls: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """获取调用许可"""
        async with self._lock:
            now = asyncio.get_event_loop().time()

            # 清理过期的调用记录
            cutoff = now - self.period
            self._calls = [t for t in self._calls if t > cutoff]

            # 检查是否超过限制
            if len(self._calls) >= self.max_calls:
                # 等待最早的调用过期
                sleep_time = self._calls[0] + self.period - now
                if sleep_time > 0:
                    logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)

            # 记录本次调用
            self._calls.append(asyncio.get_event_loop().time())

    async def __aenter__(self) -> "AsyncRateLimiter":
        await self.acquire()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass


class AsyncTaskQueue:
    """
    异步任务队列

    用于管理后台任务，支持优先级和并发控制
    """

    def __init__(self, max_concurrency: int = 5):
        self.max_concurrency = max_concurrency
        self._queue: asyncio.PriorityQueue[tuple[int, int, Callable[[], Coroutine[Any, Any, Any]]]] = (
            asyncio.PriorityQueue()
        )
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._task_count = 0
        self._running = False
        self._worker_task: asyncio.Task | None = None

    async def start(self) -> None:
        """启动任务队列处理器"""
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        """停止任务队列处理器"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def submit(
        self,
        task: Callable[[], Coroutine[Any, Any, T]],
        priority: int = 0,
    ) -> None:
        """
        提交任务到队列

        Args:
            task: 异步任务函数
            priority: 优先级（越小越优先）
        """
        self._task_count += 1
        await self._queue.put((priority, self._task_count, task))

    async def _worker(self) -> None:
        """工作协程"""
        while self._running:
            try:
                priority, _, task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                async with self._semaphore:
                    try:
                        await task()
                    except Exception as e:
                        logger.error(f"Task execution error: {e}")
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")


async def retry_with_backoff(
    func: Callable[[], Coroutine[Any, Any, T]],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """
    带指数退避的重试

    Args:
        func: 异步函数
        max_retries: 最大重试次数
        base_delay: 基础延迟（秒）
        max_delay: 最大延迟（秒）
        exceptions: 需要重试的异常类型

    Returns:
        T: 函数返回值

    Raises:
        Exception: 重试耗尽后抛出最后一次异常
    """
    import random

    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                # 指数退避 + 随机抖动
                delay = min(base_delay * (2**attempt), max_delay)
                delay = delay * (0.5 + random.random())  # 添加抖动
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {max_retries + 1} attempts failed")

    raise last_exception or RuntimeError("Retry failed")


def run_sync(coro: Coroutine[Any, Any, T]) -> T:
    """
    在同步上下文中运行异步协程

    Args:
        coro: 协程

    Returns:
        T: 协程返回值
    """
    try:
        loop = asyncio.get_running_loop()
        # 已经在事件循环中，创建任务
        return loop.run_until_complete(coro)
    except RuntimeError:
        # 没有事件循环，创建新的
        return asyncio.run(coro)
