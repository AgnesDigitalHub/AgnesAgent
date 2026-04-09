"""
计划执行器

执行任务图，支持顺序执行、并行执行和动态调整
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable

from agnes.planning.decomposer import Task, TaskGraph, TaskStatus
from agnes.skills.engine import SkillCallEngine

logger = logging.getLogger(__name__)


class ExecutionStrategy(Enum):
    """执行策略"""

    SEQUENTIAL = auto()  # 顺序执行
    PARALLEL = auto()  # 并行执行（无依赖的任务）
    ADAPTIVE = auto()  # 自适应（根据任务特性决定）


@dataclass
class ExecutionResult:
    """执行结果"""

    success: bool
    completed_tasks: list[str] = field(default_factory=list)
    failed_tasks: list[str] = field(default_factory=list)
    skipped_tasks: list[str] = field(default_factory=list)
    results: dict[str, Any] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def completion_rate(self) -> float:
        """完成率"""
        total = len(self.completed_tasks) + len(self.failed_tasks) + len(self.skipped_tasks)
        if total == 0:
            return 0.0
        return len(self.completed_tasks) / total

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "skipped_tasks": self.skipped_tasks,
            "execution_time_ms": self.execution_time_ms,
            "completion_rate": self.completion_rate,
            "metadata": self.metadata,
        }


class PlanExecutor:
    """
    计划执行器

    执行任务图，支持：
    - 顺序执行
    - 并行执行
    - 失败重试
    - 动态调整
    """

    def __init__(
        self,
        skill_engine: SkillCallEngine | None = None,
        strategy: ExecutionStrategy = ExecutionStrategy.ADAPTIVE,
        max_retries: int = 2,
        continue_on_error: bool = False,
    ):
        """
        初始化执行器

        Args:
            skill_engine: 技能调用引擎
            strategy: 执行策略
            max_retries: 最大重试次数
            continue_on_error: 出错时是否继续
        """
        self.skill_engine = skill_engine
        self.strategy = strategy
        self.max_retries = max_retries
        self.continue_on_error = continue_on_error

        # 回调
        self._on_task_start: Callable[[Task], None] | None = None
        self._on_task_complete: Callable[[Task], None] | None = None
        self._on_task_fail: Callable[[Task, str], None] | None = None

    def on_task_start(self, callback: Callable[[Task], None]) -> "PlanExecutor":
        """注册任务开始回调"""
        self._on_task_start = callback
        return self

    def on_task_complete(self, callback: Callable[[Task], None]) -> "PlanExecutor":
        """注册任务完成回调"""
        self._on_task_complete = callback
        return self

    def on_task_fail(self, callback: Callable[[Task, str], None]) -> "PlanExecutor":
        """注册任务失败回调"""
        self._on_task_fail = callback
        return self

    async def execute(
        self,
        graph: TaskGraph,
        context: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """
        执行任务图

        Args:
            graph: 任务依赖图
            context: 执行上下文

        Returns:
            ExecutionResult: 执行结果
        """
        start_time = time.time()
        result = ExecutionResult(success=True)

        try:
            if self.strategy == ExecutionStrategy.SEQUENTIAL:
                await self._execute_sequential(graph, result, context)
            elif self.strategy == ExecutionStrategy.PARALLEL:
                await self._execute_parallel(graph, result, context)
            else:  # ADAPTIVE
                await self._execute_adaptive(graph, result, context)
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            result.success = False
            result.metadata["error"] = str(e)

        result.execution_time_ms = (time.time() - start_time) * 1000
        return result

    async def _execute_sequential(
        self,
        graph: TaskGraph,
        result: ExecutionResult,
        context: dict[str, Any] | None,
    ) -> None:
        """顺序执行"""
        order = graph.get_execution_order()

        for task_id in order:
            task = graph.tasks[task_id]
            success = await self._execute_task(task, context)

            if not success:
                result.failed_tasks.append(task_id)
                if not self.continue_on_error:
                    result.success = False
                    break
            else:
                result.completed_tasks.append(task_id)
                result.results[task_id] = task.result

    async def _execute_parallel(
        self,
        graph: TaskGraph,
        result: ExecutionResult,
        context: dict[str, Any] | None,
    ) -> None:
        """并行执行"""
        groups = graph.get_parallel_groups()

        for group in groups:
            # 并行执行组内任务
            tasks = [graph.tasks[tid] for tid in group]
            results = await asyncio.gather(
                *[self._execute_task_wrapper(t, context) for t in tasks],
                return_exceptions=True,
            )

            for task, task_result in zip(tasks, results):
                if isinstance(task_result, Exception):
                    result.failed_tasks.append(task.id)
                    result.errors[task.id] = str(task_result)
                    if self._on_task_fail:
                        self._on_task_fail(task, str(task_result))
                elif task_result:
                    result.completed_tasks.append(task.id)
                    result.results[task.id] = task.result
                    if self._on_task_complete:
                        self._on_task_complete(task)
                else:
                    result.failed_tasks.append(task.id)

            # 检查是否继续
            if result.failed_tasks and not self.continue_on_error:
                result.success = False
                break

    async def _execute_adaptive(
        self,
        graph: TaskGraph,
        result: ExecutionResult,
        context: dict[str, Any] | None,
    ) -> None:
        """自适应执行"""
        # 简单实现：小图顺序，大图并行
        if len(graph.tasks) <= 3:
            await self._execute_sequential(graph, result, context)
        else:
            await self._execute_parallel(graph, result, context)

    async def _execute_task_wrapper(
        self,
        task: Task,
        context: dict[str, Any] | None,
    ) -> bool:
        """任务执行包装器"""
        try:
            return await self._execute_task(task, context)
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            return False

    async def _execute_task(
        self,
        task: Task,
        context: dict[str, Any] | None,
    ) -> bool:
        """
        执行单个任务

        Args:
            task: 任务
            context: 上下文

        Returns:
            bool: 是否成功
        """
        if task.status == TaskStatus.COMPLETED:
            return True

        task.status = TaskStatus.RUNNING

        if self._on_task_start:
            self._on_task_start(task)

        start_time = time.time()
        retries = 0

        while retries <= self.max_retries:
            try:
                # 如果有工具，调用工具
                if task.tool_name and self.skill_engine:
                    skill_result = await self.skill_engine.call(
                        task.tool_name,
                        task.tool_params,
                    )
                    if skill_result.success:
                        task.result = skill_result.data
                        task.status = TaskStatus.COMPLETED
                    else:
                        raise Exception(skill_result.error_message)
                else:
                    # 无工具任务，标记为完成（由外部处理）
                    task.result = {"status": "pending_external"}
                    task.status = TaskStatus.COMPLETED

                task.execution_time_ms = (time.time() - start_time) * 1000

                if self._on_task_complete:
                    self._on_task_complete(task)

                return True

            except Exception as e:
                retries += 1
                if retries > self.max_retries:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task.execution_time_ms = (time.time() - start_time) * 1000

                    if self._on_task_fail:
                        self._on_task_fail(task, str(e))

                    return False

                await asyncio.sleep(0.5 * retries)  # 指数退避

        return False

    async def execute_step(
        self,
        graph: TaskGraph,
        context: dict[str, Any] | None = None,
    ) -> list[str]:
        """
        单步执行（执行一批就绪任务）

        Returns:
            list[str]: 执行的任务ID列表
        """
        ready_tasks = graph.get_ready_tasks()
        executed = []

        for task in ready_tasks:
            success = await self._execute_task(task, context)
            executed.append(task.id)

            if not success and not self.continue_on_error:
                break

        return executed

    def get_progress(self, graph: TaskGraph) -> dict[str, Any]:
        """获取执行进度"""
        total = len(graph.tasks)
        completed = sum(1 for t in graph.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in graph.tasks.values() if t.status == TaskStatus.FAILED)
        running = sum(1 for t in graph.tasks.values() if t.status == TaskStatus.RUNNING)
        pending = sum(1 for t in graph.tasks.values() if t.status == TaskStatus.PENDING)

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "progress_percent": (completed / total * 100) if total > 0 else 0,
        }
