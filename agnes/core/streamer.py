import asyncio
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass
class StreamEvent[T]:
    data: T
    event_type: str = "data"
    is_final: bool = False


class Streamer[T]:
    """通用流式输出处理器"""

    def __init__(self):
        self._queue: asyncio.Queue[StreamEvent[T] | None] = asyncio.Queue()
        self._closed = False
        self._callbacks: list[Callable[[StreamEvent[T]], None]] = []

    def on_data(self, callback: Callable[[StreamEvent[T]], None]) -> None:
        """注册数据回调函数"""
        self._callbacks.append(callback)

    def emit(self, data: T, is_final: bool = False) -> None:
        """发送数据到流"""
        if self._closed:
            raise RuntimeError("Streamer is closed")

        event = StreamEvent(data=data, is_final=is_final)
        asyncio.create_task(self._queue.put(event))

        for callback in self._callbacks:
            try:
                callback(event)
            except Exception:
                pass

    def close(self) -> None:
        """关闭流"""
        if not self._closed:
            self._closed = True
            asyncio.create_task(self._queue.put(None))

    async def __aiter__(self) -> AsyncGenerator[StreamEvent[T], None]:
        """异步迭代器"""
        while True:
            item = await self._queue.get()
            if item is None:
                break
            yield item


class TextStreamer(Streamer[str]):
    """文本流式输出处理器"""

    def __init__(self):
        super().__init__()
        self._buffer: list[str] = []

    def emit_token(self, token: str) -> None:
        """发送单个 token"""
        self._buffer.append(token)
        self.emit(token, is_final=False)

    def end(self) -> str:
        """结束流并返回完整文本"""
        full_text = "".join(self._buffer)
        self.emit(full_text, is_final=True)
        self.close()
        return full_text

    def get_full_text(self) -> str:
        """获取当前完整文本"""
        return "".join(self._buffer)
