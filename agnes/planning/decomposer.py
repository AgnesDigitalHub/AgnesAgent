"""
任务分解器

将复杂任务分解为可执行的子任务，构建任务依赖图
"""

import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""

    PENDING = auto()      # 等待执行
    RUNNING = auto()      # 执行中
    COMPLETED = auto()    # 已完成
    FAILED = auto()       # 失败
    SKIPPED = auto()      # 跳过


class TaskPriority(Enum):
    """任务优先级"""

    CRITICAL = 1    # 关键
    HIGH = 2        # 高
    NORMAL = 3      # 正常
    LOW = 4         # 低


@dataclass
class Task:
    """
    任务定义

    表示一个可执行的子任务
    """

    id: str
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL

    # 执行相关
    tool_name: str | None = None          # 使用的工具
    tool_params: dict[str, Any] = field(default_factory=dict)  # 工具参数
    expected_output: str = ""             # 预期输出描述

    # 依赖关系
    dependencies: list[str] = field(default_factory=list)  # 依赖的任务ID
    dependents: list[str] = field(default_factory=list)  # 依赖此任务的任务ID

    # 结果
    result: Any = None
    error: str | None = None
    execution_time_ms: float = 0.0

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.name,
            "priority": self.priority.name,
            "tool_name": self.tool_name,
            "tool_params": self.tool_params,
            "expected_output": self.expected_output,
            "dependencies": self.dependencies,
            "result": self.result,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
        }

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        tool_name: str | None = None,
        tool_params: dict[str, Any] | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: list[str] | None = None,
    ) -> "Task":
        """创建新任务"""
        return cls(
            id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            tool_name=tool_name,
            tool_params=tool_params or {},
            priority=priority,
            dependencies=dependencies or [],
        )


class TaskGraph:
    """
    任务依赖图

    管理任务之间的依赖关系，提供拓扑排序等功能
    """

    def __init__(self):
        self.tasks: dict[str, Task] = {}
        self._execution_order: list[str] | None = None

    def add_task(self, task: Task) -> None:
        """添加任务"""
        self.tasks[task.id] = task
        self._execution_order = None  # 重置缓存

    def add_dependency(self, task_id: str, depends_on: str) -> bool:
        """
        添加依赖关系

        Args:
            task_id: 任务ID
            depends_on: 依赖的任务ID

        Returns:
            bool: 是否成功
        """
        if task_id not in self.tasks or depends_on not in self.tasks:
            return False

        if depends_on not in self.tasks[task_id].dependencies:
            self.tasks[task_id].dependencies.append(depends_on)
            self.tasks[depends_on].dependents.append(task_id)
            self._execution_order = None

        return True

    def get_ready_tasks(self) -> list[Task]:
        """
        获取可以执行的任务

        返回所有依赖已完成的 PENDING 任务
        """
        ready = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                # 检查所有依赖是否已完成
                deps_completed = all(
                    self.tasks[dep_id].status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                    if dep_id in self.tasks
                )
                if deps_completed:
                    ready.append(task)

        # 按优先级排序
        ready.sort(key=lambda t: t.priority.value)
        return ready

    def get_execution_order(self) -> list[str]:
        """
        获取执行顺序（拓扑排序）

        Returns:
            list[str]: 任务ID列表
        """
        if self._execution_order is not None:
            return self._execution_order

        # Kahn算法
        in_degree = {tid: 0 for tid in self.tasks}
        for task in self.tasks.values():
            for dep in task.dependencies:
                if dep in in_degree:
                    in_degree[task.id] += 1

        # 找到入度为0的任务
        queue = [tid for tid, degree in in_degree.items() if degree == 0]
        queue.sort(key=lambda tid: self.tasks[tid].priority.value)

        result = []
        while queue:
            # 取优先级最高的
            current = queue.pop(0)
            result.append(current)

            # 更新依赖此任务的入度
            for task in self.tasks.values():
                if current in task.dependencies:
                    in_degree[task.id] -= 1
                    if in_degree[task.id] == 0:
                        queue.append(task.id)
                        queue.sort(key=lambda tid: self.tasks[tid].priority.value)

        if len(result) != len(self.tasks):
            raise ValueError("Task graph has circular dependencies")

        self._execution_order = result
        return result

    def get_parallel_groups(self) -> list[list[str]]:
        """
        获取可并行执行的任务组

        Returns:
            list[list[str]]: 每组任务ID列表
        """
        order = self.get_execution_order()
        groups = []
        completed = set()

        while len(completed) < len(order):
            # 找到当前可以执行的任务
            group = []
            for tid in order:
                if tid in completed:
                    continue
                task = self.tasks[tid]
                deps_satisfied = all(
                    dep in completed for dep in task.dependencies
                )
                if deps_satisfied:
                    group.append(tid)

            if not group:
                break

            groups.append(group)
            completed.update(group)

        return groups

    def to_dict(self) -> dict[str, Any]:
        return {
            "tasks": {tid: task.to_dict() for tid, task in self.tasks.items()},
            "execution_order": self.get_execution_order(),
        }


class TaskDecomposer:
    """
    任务分解器

    将复杂任务分解为子任务图
    """

    def __init__(self, llm_provider: Any | None = None):
        """
        初始化分解器

        Args:
            llm_provider: LLM 提供商（用于智能分解）
        """
        self.llm = llm_provider

    def decompose(
        self,
        task_description: str,
        context: dict[str, Any] | None = None,
    ) -> TaskGraph:
        """
        分解任务

        Args:
            task_description: 任务描述
            context: 上下文信息

        Returns:
            TaskGraph: 任务依赖图
        """
        # 如果没有LLM，使用简单的规则分解
        if self.llm is None:
            return self._rule_based_decompose(task_description, context)

        # 使用LLM智能分解
        return self._llm_based_decompose(task_description, context)

    def _rule_based_decompose(
        self,
        task_description: str,
        context: dict[str, Any] | None = None,
    ) -> TaskGraph:
        """基于规则的简单分解"""
        graph = TaskGraph()

        # 创建分析任务
        analysis = Task.create(
            name="分析需求",
            description=f"分析任务: {task_description}",
            priority=TaskPriority.CRITICAL,
        )
        graph.add_task(analysis)

        # 创建执行任务
        execution = Task.create(
            name="执行任务",
            description="执行主要任务",
            priority=TaskPriority.HIGH,
            dependencies=[analysis.id],
        )
        graph.add_task(execution)

        # 创建验证任务
        verification = Task.create(
            name="验证结果",
            description="验证执行结果",
            priority=TaskPriority.NORMAL,
            dependencies=[execution.id],
        )
        graph.add_task(verification)

        return graph

    def _llm_based_decompose(
        self,
        task_description: str,
        context: dict[str, Any] | None = None,
    ) -> TaskGraph:
        """基于LLM的智能分解"""
        # TODO: 实现LLM驱动的任务分解
        # 1. 构建分解提示词
        # 2. 调用LLM获取子任务列表
        # 3. 解析依赖关系
        # 4. 构建任务图
        return self._rule_based_decompose(task_description, context)

    def decompose_with_template(
        self,
        task_description: str,
        template: str,
    ) -> TaskGraph:
        """
        使用模板分解

        Args:
            task_description: 任务描述
            template: 模板名称 (research/code/analysis)

        Returns:
            TaskGraph: 任务依赖图
        """
        templates = {
            "research": self._research_template,
            "code": self._code_template,
            "analysis": self._analysis_template,
        }

        if template in templates:
            return templates[template](task_description)

        return self._rule_based_decompose(task_description)

    def _research_template(self, description: str) -> TaskGraph:
        """研究任务模板"""
        graph = TaskGraph()

        # 1. 信息收集
        collect = Task.create(
            name="信息收集",
            description="收集相关信息和数据",
            priority=TaskPriority.CRITICAL,
        )
        graph.add_task(collect)

        # 2. 信息整理
        organize = Task.create(
            name="信息整理",
            description="整理收集到的信息",
            priority=TaskPriority.HIGH,
            dependencies=[collect.id],
        )
        graph.add_task(organize)

        # 3. 分析
        analyze = Task.create(
            name="分析",
            description="分析整理后的信息",
            priority=TaskPriority.HIGH,
            dependencies=[organize.id],
        )
        graph.add_task(analyze)

        # 4. 总结
        summarize = Task.create(
            name="总结",
            description="总结分析结果",
            priority=TaskPriority.NORMAL,
            dependencies=[analyze.id],
        )
        graph.add_task(summarize)

        return graph

    def _code_template(self, description: str) -> TaskGraph:
        """编程任务模板"""
        graph = TaskGraph()

        # 1. 需求分析
        analyze = Task.create(
            name="需求分析",
            description="分析代码需求",
            priority=TaskPriority.CRITICAL,
        )
        graph.add_task(analyze)

        # 2. 设计
        design = Task.create(
            name="设计",
            description="设计代码结构",
            priority=TaskPriority.HIGH,
            dependencies=[analyze.id],
        )
        graph.add_task(design)

        # 3. 编码
        code = Task.create(
            name="编码",
            description="编写代码",
            priority=TaskPriority.HIGH,
            dependencies=[design.id],
        )
        graph.add_task(code)

        # 4. 测试
        test = Task.create(
            name="测试",
            description="测试代码",
            priority=TaskPriority.NORMAL,
            dependencies=[code.id],
        )
        graph.add_task(test)

        return graph

    def _analysis_template(self, description: str) -> TaskGraph:
        """分析任务模板"""
        graph = TaskGraph()

        # 1. 数据收集
        collect = Task.create(
            name="数据收集",
            description="收集分析所需数据",
            priority=TaskPriority.CRITICAL,
        )
        graph.add_task(collect)

        # 2. 数据清洗
        clean = Task.create(
            name="数据清洗",
            description="清洗和预处理数据",
            priority=TaskPriority.HIGH,
            dependencies=[collect.id],
        )
        graph.add_task(clean)

        # 3. 数据分析
        analyze = Task.create(
            name="数据分析",
            description="执行数据分析",
            priority=TaskPriority.HIGH,
            dependencies=[clean.id],
        )
        graph.add_task(analyze)

        # 4. 可视化
        visualize = Task.create(
            name="可视化",
            description="创建可视化图表",
            priority=TaskPriority.NORMAL,
            dependencies=[analyze.id],
        )
        graph.add_task(visualize)

        return graph
