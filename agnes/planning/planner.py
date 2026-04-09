"""
规划器

整合任务分解和执行，提供高级规划接口
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from agnes.planning.decomposer import TaskDecomposer, TaskGraph
from agnes.planning.executor import ExecutionResult, PlanExecutor
from agnes.skills.engine import SkillCallEngine

logger = logging.getLogger(__name__)


@dataclass
class Plan:
    """计划定义"""

    id: str
    name: str
    description: str
    task_graph: TaskGraph
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "task_graph": self.task_graph.to_dict(),
            "metadata": self.metadata,
        }


class Planner:
    """
    规划器

    整合任务分解和执行的高级接口
    """

    def __init__(
        self,
        skill_engine: SkillCallEngine | None = None,
        llm_provider: Any | None = None,
    ):
        """
        初始化规划器

        Args:
            skill_engine: 技能调用引擎
            llm_provider: LLM 提供商
        """
        self.decomposer = TaskDecomposer(llm_provider)
        self.executor = PlanExecutor(skill_engine)

    async def plan_and_execute(
        self,
        task_description: str,
        context: dict[str, Any] | None = None,
        template: str | None = None,
    ) -> tuple[Plan, ExecutionResult]:
        """
        规划并执行任务

        Args:
            task_description: 任务描述
            context: 上下文
            template: 模板名称

        Returns:
            tuple[Plan, ExecutionResult]: 计划和执行结果
        """
        # 1. 分解任务
        if template:
            graph = self.decomposer.decompose_with_template(task_description, template)
        else:
            graph = self.decomposer.decompose(task_description, context)

        plan = Plan(
            id=graph.tasks[list(graph.tasks.keys())[0]].id if graph.tasks else "empty",
            name=task_description[:50],
            description=task_description,
            task_graph=graph,
            context=context or {},
        )

        # 2. 执行
        result = await self.executor.execute(graph, context)

        return plan, result

    async def execute_plan(
        self,
        plan: Plan,
        context: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """
        执行已有计划

        Args:
            plan: 计划
            context: 上下文

        Returns:
            ExecutionResult: 执行结果
        """
        merged_context = {**plan.context, **(context or {})}
        return await self.executor.execute(plan.task_graph, merged_context)

    def get_plan_progress(self, plan: Plan) -> dict[str, Any]:
        """获取计划进度"""
        return self.executor.get_progress(plan.task_graph)
