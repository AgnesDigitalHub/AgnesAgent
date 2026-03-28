"""
YAML-based Skill Loader - P1 优先级
让用户通过编写 YAML 文件即可扩展框架功能，无需编写 Python 代码
支持定义 Skill 参数、描述和执行逻辑（使用 Jinja2 模板或 Python 表达式）
"""

import importlib
import json
import logging
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Template
from pydantic import BaseModel, Field, ValidationError

from agnes.skills.base import BaseSkill, SkillMetadata, SkillResult, SkillSchema

logger = logging.getLogger(__name__)


class YAMLSkillDefinition(BaseModel):
    """YAML Skill 定义结构"""

    name: str = Field(description="Skill 唯一名称")
    description: str = Field(description="Skill 功能描述")
    version: str = Field(default="1.0.0", description="版本号")
    category: str = Field(default="general", description="分类")
    tags: list[str] = Field(default_factory=list, description="标签")
    parameters: dict[str, Any] = Field(description="参数定义 JSON Schema")
    required: list[str] = Field(default_factory=list, description="必填参数")
    returns: dict[str, Any] = Field(default_factory=dict, description="返回值定义")
    execution: str = Field(description="执行逻辑，可以是 Python 表达式或 Jinja2 模板")
    execution_type: str = Field(default="python", description="执行类型: python/template")
    requires: list[str] = Field(default_factory=list, description="依赖的 Python 包")


class YAMLLoadResult(BaseModel):
    """YAML 加载结果"""

    success: bool
    skill_name: str
    message: str
    skill: Any | None = None
    errors: list[str] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}


class YAMLSkill(BaseSkill):
    """从 YAML 定义动态创建的 Skill"""

    def __init__(
        self,
        definition: YAMLSkillDefinition,
        source_path: Path | None = None,
    ):
        self._definition = definition
        self._source_path = source_path
        self.name = definition.name
        self.description = definition.description
        self.metadata = SkillMetadata(
            version=definition.version,
            category=definition.category,
            tags=definition.tags,
        )
        self._schema = SkillSchema(
            name=definition.name,
            description=definition.description,
            parameters=definition.parameters,
            required=definition.required,
            returns=definition.returns,
        )

    def get_schema(self) -> SkillSchema:
        return self._schema

    async def execute(self, parameters: dict[str, Any]) -> SkillResult:
        """执行 Skill，根据类型选择执行方式"""
        try:
            if self._definition.execution_type == "template":
                return self._execute_template(parameters)
            elif self._definition.execution_type == "python":
                return await self._execute_python(parameters)
            else:
                return SkillResult.error(
                    "invalid_execution_type",
                    f"不支持的执行类型: {self._definition.execution_type}",
                )
        except Exception as e:
            logger.error(f"执行 YAML Skill '{self.name}' 失败: {e}")
            return SkillResult.error("execution_error", str(e))

    def _execute_template(self, parameters: dict[str, Any]) -> SkillResult:
        """使用 Jinja2 模板执行，适合文本生成"""
        template = Template(self._definition.execution)
        result = template.render(**parameters)
        return SkillResult.ok({"result": result})

    async def _execute_python(self, parameters: dict[str, Any]) -> SkillResult:
        """使用 Python 表达式执行，适合计算和逻辑处理"""
        # 创建一个安全的执行环境，只暴露基本功能
        env: dict[str, Any] = {
            "__builtins__": {
                "abs": abs,
                "len": len,
                "max": max,
                "min": min,
                "sum": sum,
                "round": round,
                "int": int,
                "float": float,
                "str": str,
                "bool": bool,
                "list": list,
                "dict": dict,
                "json": json,
            },
            "params": parameters,
        }

        # 执行代码
        try:
            if "import" in self._definition.execution:
                # 支持导入依赖
                exec(self._definition.execution, env)
                if "result" in env:
                    return SkillResult.ok(env["result"])
                else:
                    return SkillResult.ok({"success": True})
            else:
                # 简单表达式求值
                result = eval(self._definition.execution, env)
                return SkillResult.ok(result)
        except Exception as e:
            return SkillResult.error("python_error", str(e))


class YAMLSkillLoader:
    """YAML Skill 加载器，从目录加载所有 YAML Skill"""

    def __init__(self, skills_dir: Path | None = None):
        from agnes.config import get_project_root

        if skills_dir is None:
            root = get_project_root()
            skills_dir = root / "config" / "skills"
        self.skills_dir = skills_dir
        self._loaded_skills: dict[str, YAMLSkill] = {}

    def load_all(self) -> list[YAMLLoadResult]:
        """加载目录下所有 YAML Skill"""
        if not self.skills_dir.exists():
            logger.info(f"YAML Skill 目录不存在: {self.skills_dir}，跳过加载")
            return []

        results = []
        for yaml_file in self.skills_dir.glob("*.yaml"):
            if yaml_file.name.startswith("."):
                continue
            result = self.load_from_file(yaml_file)
            results.append(result)

        logger.info(f"YAML Skill 加载完成，成功: {sum(1 for r in results if r.success)}/{len(results)}")
        return results

    def load_from_file(self, path: Path) -> YAMLLoadResult:
        """从单个文件加载 Skill"""
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                return YAMLLoadResult(
                    success=False,
                    skill_name=path.stem,
                    message="文件为空或格式错误",
                )

            # 使用 Pydantic 验证结构，这本身就是 JSON Schema 校验
            definition = YAMLSkillDefinition(**data)

            # 检查依赖
            errors = self._check_dependencies(definition.requires)
            if errors:
                return YAMLLoadResult(
                    success=False,
                    skill_name=definition.name,
                    message="依赖检查失败",
                    errors=errors,
                )

            # 创建 Skill
            skill = YAMLSkill(definition, path)

            # 保存
            self._loaded_skills[skill.name] = skill

            logger.info(f"成功加载 YAML Skill: {skill.name} v{definition.version} from {path}")

            return YAMLLoadResult(
                success=True,
                skill_name=skill.name,
                message=f"成功加载 YAML Skill: {skill.name}",
                skill=skill,
            )

        except ValidationError as e:
            errors = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            return YAMLLoadResult(
                success=False,
                skill_name=data.get("name", path.stem) if "data" in locals() else path.stem,
                message="Schema 验证失败",
                errors=errors,
            )
        except yaml.YAMLError as e:
            return YAMLLoadResult(
                success=False,
                skill_name=path.stem,
                message=f"YAML 解析错误: {str(e)}",
                errors=[str(e)],
            )
        except Exception as e:
            logger.error(f"加载 YAML Skill 失败 {path}: {e}", exc_info=True)
            return YAMLLoadResult(
                success=False,
                skill_name=path.stem,
                message=f"加载失败: {str(e)}",
                errors=[str(e)],
            )

    def _check_dependencies(self, requires: list[str]) -> list[str]:
        """检查依赖是否满足"""
        errors = []
        for req in requires:
            try:
                importlib.import_module(req)
            except ImportError:
                errors.append(f"缺少依赖: {req}")
        return errors

    def get_loaded_skills(self) -> list[YAMLSkill]:
        """获取所有已加载的 Skill"""
        return list(self._loaded_skills.values())

    def get_skill(self, name: str) -> YAMLSkill | None:
        """获取指定 Skill"""
        return self._loaded_skills.get(name)

    def reload(self, name: str) -> YAMLLoadResult | None:
        """重新加载单个 Skill"""
        if name not in self._loaded_skills:
            return None

        skill = self._loaded_skills[name]
        if not skill._source_path:
            return YAMLLoadResult(
                success=False,
                skill_name=name,
                message="无法重载: 没有源文件路径",
            )

        return self.load_from_file(skill._source_path)


# 全局加载器实例
_loader: YAMLSkillLoader | None = None


def get_yaml_loader(skills_dir: Path | None = None) -> YAMLSkillLoader:
    """获取全局 YAML 加载器"""
    global _loader
    if _loader is None:
        _loader = YAMLSkillLoader(skills_dir)
    return _loader


def load_and_register_all(skills_dir: Path | None = None) -> list[YAMLLoadResult]:
    """加载所有 YAML Skill 并注册到全局注册表"""
    from agnes.skills.registry import registry

    loader = get_yaml_loader(skills_dir)
    results = loader.load_all()

    for result in results:
        if result.success and result.skill is not None:
            registry.register(result.skill)

    return results
