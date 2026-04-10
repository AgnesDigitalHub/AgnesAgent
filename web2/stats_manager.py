#!/usr/bin/env python3
"""
统计管理器 - 用于持久化存储各种统计数据
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil

from agnes.utils.logger import get_logger

logger = get_logger("agnes.stats")


class StatsManager:
    """统计数据管理器"""

    def __init__(self, storage_path: str = "config/stats/stats.json"):
        """
        初始化统计管理器

        Args:
            storage_path: 统计数据存储路径
        """
        self.storage_path = Path(storage_path)
        # 确保目录存在
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # 统计数据
        self.stats = {
            "start_time": time.time(),
            "total_messages": 0,
            "daily_messages": {},  # 按日期存储消息数
            "active_connections": 0,
            "max_connections": 0,
        }

        # 线程锁
        self._lock = threading.Lock()

        # 加载现有统计数据
        self._load_stats()

        # 启动时间
        self.start_time = time.time()

    def _load_stats(self):
        """加载统计数据"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, encoding="utf-8") as f:
                    data = json.load(f)
                    self.stats.update(data)
        except Exception as e:
            logger.error(f"加载统计数据失败: {e}")

    def _save_stats(self):
        """保存统计数据"""
        try:
            with self._lock:
                with open(self.storage_path, "w", encoding="utf-8") as f:
                    json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存统计数据失败: {e}")

    def increment_messages(self, count: int = 1):
        """增加消息计数"""
        with self._lock:
            self.stats["total_messages"] += count

            # 按天统计
            today = datetime.now().strftime("%Y-%m-%d")
            if today not in self.stats["daily_messages"]:
                self.stats["daily_messages"][today] = 0
            self.stats["daily_messages"][today] += count

            self._save_stats()

    def get_today_messages(self) -> int:
        """获取今天的消息数"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.stats["daily_messages"].get(today, 0)

    def get_total_messages(self) -> int:
        """获取总消息数"""
        return self.stats["total_messages"]

    def set_active_connections(self, count: int):
        """设置活跃连接数"""
        with self._lock:
            self.stats["active_connections"] = count
            self.stats["max_connections"] = max(self.stats["max_connections"], count)
            self._save_stats()

    def get_active_connections(self) -> int:
        """获取活跃连接数"""
        return self.stats["active_connections"]

    def get_max_connections(self) -> int:
        """获取最大连接数"""
        return self.stats["max_connections"]

    def get_uptime(self) -> str:
        """获取运行时间（格式化字符串）"""
        uptime_seconds = time.time() - self.start_time
        return self._format_uptime(uptime_seconds)

    def get_memory_usage(self) -> dict[str, Any]:
        """获取内存使用情况"""
        try:
            # 获取当前进程内存使用
            process = psutil.Process()
            memory_info = process.memory_info()

            # 获取系统总内存和可用内存
            system_memory = psutil.virtual_memory()

            return {
                "process_rss": memory_info.rss / 1024 / 1024,  # MB
                "process_vms": memory_info.vms / 1024 / 1024,  # MB
                "system_total": system_memory.total / 1024 / 1024 / 1024,  # GB
                "system_available": system_memory.available / 1024 / 1024 / 1024,  # GB
                "system_percent": system_memory.percent,
            }
        except Exception as e:
            logger.error(f"获取内存使用情况失败: {e}")
            return {"process_rss": 0, "process_vms": 0, "system_total": 0, "system_available": 0, "system_percent": 0}

    def get_all_stats(self) -> dict[str, Any]:
        """获取所有统计数据"""
        return {
            "start_time": self.stats["start_time"],
            "total_messages": self.get_total_messages(),
            "today_messages": self.get_today_messages(),
            "active_connections": self.get_active_connections(),
            "max_connections": self.get_max_connections(),
            "uptime": self.get_uptime(),
            "memory_usage": self.get_memory_usage(),
            "daily_messages": self.stats["daily_messages"],
        }

    def _format_uptime(self, seconds: float) -> str:
        """格式化运行时间"""
        if seconds < 60:
            return f"{int(seconds)}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            seconds = int(seconds % 60)
            return f"{minutes}分{seconds}秒"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}小时{minutes}分"
        else:
            days = int(seconds // 86400)
            hours = int((seconds % 86400) // 3600)
            return f"{days}天{hours}小时"


# 全局统计管理器实例
_stats_manager: StatsManager | None = None


def get_stats_manager() -> StatsManager:
    """获取全局统计管理器实例"""
    global _stats_manager
    if _stats_manager is None:
        _stats_manager = StatsManager()
    return _stats_manager
