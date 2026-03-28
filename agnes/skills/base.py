"""
Skill 基础抽象类
定义 Skill 的标准接口和数据结构
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class SkillSchema(BaseModel):
    """Skill 的 JSON Schema 定义，用于 Function Calling"""
    name: str = Field(description="Skill 唯一名称")
    description: str = Field(description="Skill 功能描述")
    parameters: Dict[str, Any] = Field(description="参数 JSON Schema")
    required: List[str] = Field(default_factory=list, description="必填参数列表")
    returns: Dict[str, Any] = Field(description="返回值 Schema 描述")


class SkillResult(BaseModel):
    """Skill 执行结果的标准化返回"""
    success: bool = Field(description="是否成功")
    data: Optional[Any] = Field(default=None, description="返回数据")
    error_type: Optional[str] = Field(default=None, description="错误类型")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    execution_time_ms: float = Field(default=0.0, description="执行耗时（毫秒）")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    @classmethod
    def ok(cls, data: Any = None, execution_time_ms: float = 0.0, metadata: Optional[Dict[str, Any]] = None) -> "SkillResult":
        """创建成功结果"""
        return cls(
            success=True,
            data=data,
            execution_time_ms=execution_time_ms,
            metadata=metadata or {}
        )

    @classmethod
    def error(cls, error_type: str, message: str, execution_time_ms: float = 0.0) -> "SkillResult":
        """创建错误结果"""
        return cls(
            success=False,
            error_type=error_type,
            error_message=message,
            execution_time_ms=execution_time_ms
        )


class SkillMetadata(BaseModel):
    """Skill 元数据"""
    version: str = Field(default="1.0.0", description="技能版本")
    category: str = Field(default="general", description="技能分类：perception/action/inference/record")
    permission_level: str = Field(default="public", description="权限级别：public/safe/restricted")
    cost: float = Field(default=0.0, description="预估调用成本（货币单位）")
    tags: List[str] = Field(default_factory=list, description="标签")


class BaseSkill(ABC):
    """Skill 抽象基类，所有具体 Skill 都应继承此类"""

    name: str
    description: str
    metadata: SkillMetadata

    @abstractmethod
    def get_schema(self) -> SkillSchema:
        """获取 Skill 的 JSON Schema 定义"""
        pass

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> SkillResult:
        """执行 Skill，异步方法"""
        pass

    def get_metadata(self) -> SkillMetadata:
        """获取 Skill 元数据"""
        return self.metadata

    def __str__(self) -> str:
        return f"{self.name} v{self.metadata.version}: {self.description}"