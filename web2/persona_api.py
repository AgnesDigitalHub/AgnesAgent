"""
人格系统 API 层 - 提供完整的 REST API 接口

支持功能：
- 人格 CRUD 操作
- 状态管理（查询、修改、历史）
- 记忆管理（搜索、添加、压缩）
- 进化建议
- 批量操作
- 对比分析
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from web2.persona_enhanced import (
    EnhancedPersonaEngine,
    EnhancedPersonaMemory,
    EnhancedPersonaState,
    EvolutionSuggestion,
    create_enhanced_engine,
)

# ============ Pydantic 模型 ============


class PersonaStateUpdateRequest(BaseModel):
    """状态更新请求"""

    key: str = Field(..., description="状态键名")
    value: float = Field(..., description="状态值")


class PersonaStateResponse(BaseModel):
    """状态响应"""

    user_id: str
    persona_id: str
    energy: float
    affinity: float
    mood: float
    focus: float
    creativity: float
    stress: float
    curiosity: float
    domain_mastery: dict[str, float]
    dialogue_turns: int
    success_rate: float
    last_interaction: str
    updated_at: str


class MemoryCreateRequest(BaseModel):
    """创建记忆请求"""

    reflection: str = Field(..., description="反思内容")
    memory_type: str = Field(default="reflection", description="记忆类型")
    importance: float = Field(default=5.0, ge=0, le=10, description="重要性")
    context: dict = Field(default_factory=dict, description="上下文")


class MemoryResponse(BaseModel):
    """记忆响应"""

    id: str
    persona_id: str
    user_id: str
    reflection: str
    memory_type: str
    importance: float
    created_at: str
    access_count: int
    context: dict


class MemorySearchRequest(BaseModel):
    """记忆搜索请求"""

    query: str | None = Field(None, description="搜索关键词")
    memory_type: str | None = Field(None, description="记忆类型过滤")
    min_importance: float = Field(default=0.0, ge=0, le=10)
    limit: int = Field(default=10, ge=1, le=50)


class EvolutionSuggestionResponse(BaseModel):
    """进化建议响应"""

    category: str
    suggestion: str
    confidence: float
    evidence: list[str]
    priority: int


class PersonaAnalyticsResponse(BaseModel):
    """人格分析响应"""

    persona_id: str
    user_id: str
    state: dict
    memory_summary: dict
    domain_mastery: dict[str, float]
    total_interactions: int
    current_effectiveness: float


class BatchStateUpdateRequest(BaseModel):
    """批量状态更新请求"""

    updates: list[PersonaStateUpdateRequest]


class PersonaComparisonRequest(BaseModel):
    """人格对比请求"""

    persona_ids: list[str] = Field(..., min_length=2, max_length=5)
    metrics: list[str] = Field(default=["energy", "affinity", "success_rate"], description="对比指标")


class PersonaComparisonResponse(BaseModel):
    """人格对比响应"""

    comparison_data: dict[str, dict[str, Any]]
    analysis: str


# ============ API Router ============

router = APIRouter(prefix="/api/personas-enhanced", tags=["personas-enhanced"])

# 全局引擎实例（实际应用中应使用依赖注入）
_engine: EnhancedPersonaEngine | None = None


def get_engine() -> EnhancedPersonaEngine:
    """获取或创建引擎实例"""
    global _engine
    if _engine is None:
        _engine = create_enhanced_engine()
        # 加载所有人格
        _engine.load_all_from_dir()
    return _engine


# ============ 状态管理 API ============


@router.get("/{persona_id}/state/{user_id}", response_model=PersonaStateResponse)
async def get_persona_state(persona_id: str, user_id: str):
    """获取人格状态"""
    engine = get_engine()
    state = engine.get_enhanced_state(user_id, persona_id)
    return PersonaStateResponse(**state.to_dict())


@router.post("/{persona_id}/state/{user_id}/update")
async def update_persona_state(
    persona_id: str,
    user_id: str,
    request: PersonaStateUpdateRequest,
):
    """更新人格状态"""
    engine = get_engine()
    success = engine.state_store.set_state(persona_id, user_id, request.key, request.value)

    if not success:
        raise HTTPException(status_code=400, detail=f"无效的状态键: {request.key}")

    return {"success": True, "message": f"状态 {request.key} 已更新为 {request.value}"}


@router.post("/{persona_id}/state/{user_id}/batch-update")
async def batch_update_persona_state(
    persona_id: str,
    user_id: str,
    request: BatchStateUpdateRequest,
):
    """批量更新人格状态"""
    engine = get_engine()
    results = []

    for update in request.updates:
        success = engine.state_store.set_state(persona_id, user_id, update.key, update.value)
        results.append(
            {
                "key": update.key,
                "value": update.value,
                "success": success,
            }
        )

    success_count = sum(1 for r in results if r["success"])
    return {
        "success": success_count == len(results),
        "updated": success_count,
        "total": len(results),
        "details": results,
    }


@router.get("/{persona_id}/state/{user_id}/history")
async def get_state_history(
    persona_id: str,
    user_id: str,
    days: int = Query(default=7, ge=1, le=30),
):
    """获取状态历史"""
    engine = get_engine()
    history = engine.state_store.get_state_history(persona_id, user_id, days)
    return {
        "persona_id": persona_id,
        "user_id": user_id,
        "days": days,
        "history": history,
        "count": len(history),
    }


@router.post("/{persona_id}/state/{user_id}/apply-decay")
async def apply_state_decay(persona_id: str, user_id: str):
    """手动应用时间衰减"""
    engine = get_engine()
    state = engine.get_enhanced_state(user_id, persona_id)

    old_energy = state.energy
    state.apply_time_decay()
    engine.state_store.save_state(state)

    return {
        "success": True,
        "energy_before": old_energy,
        "energy_after": state.energy,
        "hours_since_last": (datetime.now() - datetime.fromisoformat(state.last_interaction)).total_seconds() / 3600,
    }


# ============ 记忆管理 API ============


@router.post("/{persona_id}/memories/{user_id}", response_model=MemoryResponse)
async def add_memory(
    persona_id: str,
    user_id: str,
    request: MemoryCreateRequest,
):
    """添加记忆"""
    engine = get_engine()
    memory = engine.memory_store.add_memory(
        persona_id=persona_id,
        user_id=user_id,
        reflection=request.reflection,
        memory_type=request.memory_type,
        importance=request.importance,
        context=request.context,
    )
    return MemoryResponse(**memory.to_dict())


@router.post("/{persona_id}/memories/{user_id}/search")
async def search_memories(
    persona_id: str,
    user_id: str,
    request: MemorySearchRequest,
):
    """搜索记忆"""
    engine = get_engine()
    memories = engine.memory_store.search_memories(
        persona_id=persona_id,
        query=request.query,
        memory_type=request.memory_type,
        min_importance=request.min_importance,
        limit=request.limit,
    )

    return {
        "persona_id": persona_id,
        "query": request.query,
        "results": [m.to_dict() for m in memories],
        "count": len(memories),
    }


@router.get("/{persona_id}/memories/{user_id}/by-type/{memory_type}")
async def get_memories_by_type(
    persona_id: str,
    user_id: str,
    memory_type: str,
    limit: int = Query(default=10, ge=1, le=50),
):
    """按类型获取记忆"""
    engine = get_engine()
    memories = engine.memory_store.get_memories_by_type(persona_id, memory_type, limit)

    return {
        "persona_id": persona_id,
        "memory_type": memory_type,
        "results": [m.to_dict() for m in memories],
        "count": len(memories),
    }


@router.get("/{persona_id}/memories/{user_id}/summary")
async def get_memory_summary(
    persona_id: str,
    user_id: str,
    days: int = Query(default=30, ge=1, le=365),
):
    """获取记忆摘要"""
    engine = get_engine()
    summary = engine.memory_store.summarize_memories(persona_id, user_id, days)
    return summary


@router.post("/{persona_id}/memories/compress")
async def compress_old_memories(
    persona_id: str,
    days_threshold: int = Query(default=90, ge=30, le=365),
    min_access_count: int = Query(default=2, ge=0, le=10),
):
    """压缩旧记忆"""
    engine = get_engine()
    compressed_count = engine.memory_store.compress_old_memories(
        persona_id=persona_id,
        days_threshold=days_threshold,
        min_access_count=min_access_count,
    )

    return {
        "success": True,
        "compressed_count": compressed_count,
        "message": f"已压缩 {compressed_count} 条旧记忆",
    }


# ============ 进化建议 API ============


@router.get("/{persona_id}/evolution/{user_id}", response_model=list[EvolutionSuggestionResponse])
async def get_evolution_suggestions(
    persona_id: str,
    user_id: str,
    days_range: int = Query(default=30, ge=7, le=90),
):
    """获取人格进化建议"""
    engine = get_engine()
    suggestions = engine.get_evolution_suggestions(persona_id, user_id, days_range)

    return [
        EvolutionSuggestionResponse(
            category=s.category,
            suggestion=s.suggestion,
            confidence=s.confidence,
            evidence=s.evidence,
            priority=s.priority,
        )
        for s in suggestions
    ]


# ============ 分析 API ============


@router.get("/{persona_id}/analytics/{user_id}", response_model=PersonaAnalyticsResponse)
async def get_persona_analytics(persona_id: str, user_id: str):
    """获取人格分析数据"""
    engine = get_engine()
    analytics = engine.get_persona_analytics(persona_id, user_id)

    return PersonaAnalyticsResponse(
        persona_id=persona_id,
        user_id=user_id,
        state=analytics["state"],
        memory_summary=analytics["memory_summary"],
        domain_mastery=analytics["domain_mastery"],
        total_interactions=analytics["total_interactions"],
        current_effectiveness=analytics["current_effectiveness"],
    )


# ============ 批量操作 API ============


@router.post("/batch/state-reset")
async def batch_reset_states(persona_ids: list[str], user_id: str):
    """批量重置人格状态"""
    engine = get_engine()
    results = []

    for persona_id in persona_ids:
        # 创建新状态（重置）
        new_state = EnhancedPersonaState(
            user_id=user_id,
            persona_id=persona_id,
        )
        engine.state_store.save_state(new_state)
        results.append({"persona_id": persona_id, "reset": True})

    return {
        "success": True,
        "reset_count": len(results),
        "results": results,
    }


@router.get("/batch/states/{user_id}")
async def get_all_states_for_user(user_id: str):
    """获取用户的所有人格状态"""
    engine = get_engine()

    # 获取所有已加载的人格
    all_states = []
    for persona_id in engine._loaded_personas.keys():
        state = engine.get_enhanced_state(user_id, persona_id)
        all_states.append(
            {
                "persona_id": persona_id,
                "state": state.to_dict(),
            }
        )

    return {
        "user_id": user_id,
        "states": all_states,
        "count": len(all_states),
    }


# ============ 对比分析 API ============


@router.post("/compare")
async def compare_personas(request: PersonaComparisonRequest):
    """对比多个人格"""
    engine = get_engine()

    comparison_data = {}

    for persona_id in request.persona_ids:
        persona = engine.get_persona(persona_id)
        if not persona:
            raise HTTPException(status_code=404, detail=f"人格 {persona_id} 不存在")

        # 收集所有用户的状态数据
        all_states = engine.state_store.get_all_states_for_persona(persona_id)

        # 计算平均值
        metrics_data = {}
        for metric in request.metrics:
            values = [getattr(s, metric, 0) for s in all_states if hasattr(s, metric)]
            if values:
                metrics_data[metric] = {
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                }

        # 获取记忆统计
        memory_summary = engine.memory_store.summarize_memories(persona_id, None, 30)

        comparison_data[persona_id] = {
            "name": persona.identity.name,
            "metrics": metrics_data,
            "memory_summary": memory_summary,
            "total_users": len(all_states),
        }

    # 生成分析文本
    analysis_parts = []
    analysis_parts.append(f"对比了 {len(request.persona_ids)} 个人格:")
    for pid, data in comparison_data.items():
        analysis_parts.append(f"- {data['name']} ({pid}): {data['total_users']} 用户")

    # 找出差异最大的指标
    for metric in request.metrics:
        values = [(pid, data["metrics"].get(metric, {}).get("avg", 0)) for pid, data in comparison_data.items()]
        if len(values) > 1:
            values.sort(key=lambda x: x[1], reverse=True)
            if values[0][1] - values[-1][1] > 20:
                analysis_parts.append(
                    f"- {metric}: {comparison_data[values[0][0]]['name']} 最高 ({values[0][1]:.1f}), "
                    f"{comparison_data[values[-1][0]]['name']} 最低 ({values[-1][1]:.1f})"
                )

    return PersonaComparisonResponse(
        comparison_data=comparison_data,
        analysis="\n".join(analysis_parts),
    )


# ============ 提示词生成 API ============


@router.get("/{persona_id}/prompt/{user_id}")
async def generate_persona_prompt(
    persona_id: str,
    user_id: str,
    domain: str = Query(default="general"),
):
    """生成人格提示词"""
    engine = get_engine()

    try:
        prompt = engine.get_persona_prompt(persona_id, user_id, domain)
        return {
            "persona_id": persona_id,
            "user_id": user_id,
            "domain": domain,
            "prompt": prompt,
            "length": len(prompt),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============ 自动反思 API ============


@router.post("/{persona_id}/auto-reflection/{user_id}")
async def generate_auto_reflection(
    persona_id: str,
    user_id: str,
    dialogue_history: list[dict],
    outcome: str = Query(default="neutral", regex="^(success|failure|neutral)$"),
):
    """自动生成反思"""
    engine = get_engine()

    memory = engine.auto_generate_reflection(
        persona_id=persona_id,
        user_id=user_id,
        dialogue_history=dialogue_history,
        outcome=outcome,
    )

    if memory:
        return MemoryResponse(**memory.to_dict())
    else:
        raise HTTPException(status_code=400, detail="无法生成反思，对话历史为空")


# ============ 导出函数 ============


def register_persona_api_routes(app, prefix: str = "/api"):
    """注册人格 API 路由到 FastAPI 应用"""
    app.include_router(router, prefix=prefix)
