"""
Workflow API - 工作流执行接口

提供三种工作流模式：
- Pipeline: 顺序执行
- Graph: 依赖 DAG 并行
- Council: 多视角审议
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.core import get_db
from app.models import AIModelConfig
from app.api.auth import get_current_active_user
from app.models import User

router = APIRouter(prefix="/workflow", tags=["工作流"])


# ==================== 请求/响应模型 ====================

class PipelineStage(BaseModel):
    """Pipeline 阶段"""
    id: Optional[str] = None
    role: str
    task: str
    system_prompt: Optional[str] = None


class GraphSlot(BaseModel):
    """Graph 节点"""
    id: str
    role: str
    task: str
    depends_on: List[str] = []
    system_prompt: Optional[str] = None
    condition: Optional[dict] = None


class CouncilMember(BaseModel):
    """Council 成员"""
    id: str
    perspective: str
    system_prompt: Optional[str] = None


class PipelineRequest(BaseModel):
    """Pipeline 请求"""
    goal: str
    stages: List[PipelineStage]
    model_config_id: Optional[int] = None


class GraphRequest(BaseModel):
    """Graph 请求"""
    goal: str
    slots: List[GraphSlot]
    model_config_id: Optional[int] = None


class CouncilRequest(BaseModel):
    """Council 请求"""
    question: str
    members: List[CouncilMember]
    cross_review: bool = True
    model_config_id: Optional[int] = None


class WorkflowResponse(BaseModel):
    """工作流响应"""
    success: bool
    message: str
    result: Optional[str] = None
    latency_ms: Optional[int] = None


# ==================== 辅助函数 ====================

async def get_model_config(
    db: AsyncSession,
    model_config_id: Optional[int],
    current_user: User,
) -> AIModelConfig:
    """获取模型配置"""
    if model_config_id:
        result = await db.execute(
            select(AIModelConfig).where(AIModelConfig.id == model_config_id)
        )
        config = result.scalar_one_or_none()
    else:
        result = await db.execute(
            select(AIModelConfig).where(AIModelConfig.is_default == True)
        )
        config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=400, detail="没有可用的 AI 模型配置")
    
    return config


# ==================== API 端点 ====================

@router.post("/pipeline", response_model=WorkflowResponse)
async def run_pipeline(
    request: PipelineRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Pipeline 工作流 - 顺序执行
    
    每个阶段继承前序输出，适合需要逐步处理的任务
    """
    import time
    import logging
    logger = logging.getLogger(__name__)
    
    start_time = time.time()
    
    try:
        config = await get_model_config(db, request.model_config_id, current_user)
        
        # 创建 AgentLoop
        from app.modules.agent import AgentLoop
        from app.modules.tools import ToolRegistry, register_builtin_tools
        
        tool_registry = ToolRegistry()
        register_builtin_tools(tool_registry)
        
        # 简单的 Provider
        from app.api.chat import SimpleLLMProvider
        provider = SimpleLLMProvider(config=config)
        
        agent_loop = AgentLoop(
            provider=provider,
            tools=tool_registry,
            model=config.model_name,
            max_iterations=10,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            user_role=current_user.role,
        )
        
        # 创建 WorkflowEngine
        from app.modules.agent import WorkflowEngine
        engine = WorkflowEngine(agent_loop=agent_loop)
        
        # 执行 Pipeline
        stages = [s.dict() for s in request.stages]
        result = await engine.run_pipeline(request.goal, stages)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return WorkflowResponse(
            success=True,
            message="Pipeline 执行成功",
            result=result,
            latency_ms=latency_ms,
        )
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return WorkflowResponse(
            success=False,
            message=f"执行失败: {str(e)}",
            latency_ms=int((time.time() - start_time) * 1000),
        )


@router.post("/graph", response_model=WorkflowResponse)
async def run_graph(
    request: GraphRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Graph 工作流 - 依赖 DAG 并行执行
    
    自动并行调度，适合有依赖关系的任务
    """
    import time
    import logging
    logger = logging.getLogger(__name__)
    
    start_time = time.time()
    
    try:
        config = await get_model_config(db, request.model_config_id, current_user)
        
        # 创建 AgentLoop
        from app.modules.agent import AgentLoop
        from app.modules.tools import ToolRegistry, register_builtin_tools
        
        tool_registry = ToolRegistry()
        register_builtin_tools(tool_registry)
        
        from app.api.chat import SimpleLLMProvider
        provider = SimpleLLMProvider(config=config)
        
        agent_loop = AgentLoop(
            provider=provider,
            tools=tool_registry,
            model=config.model_name,
            max_iterations=10,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            user_role=current_user.role,
        )
        
        # 创建 WorkflowEngine
        from app.modules.agent import WorkflowEngine
        engine = WorkflowEngine(agent_loop=agent_loop)
        
        # 执行 Graph
        slots = [s.dict() for s in request.slots]
        result = await engine.run_graph(request.goal, slots)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return WorkflowResponse(
            success=True,
            message="Graph 执行成功",
            result=result,
            latency_ms=latency_ms,
        )
        
    except Exception as e:
        logger.error(f"Graph failed: {e}")
        return WorkflowResponse(
            success=False,
            message=f"执行失败: {str(e)}",
            latency_ms=int((time.time() - start_time) * 1000),
        )


@router.post("/council", response_model=WorkflowResponse)
async def run_council(
    request: CouncilRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Council 工作流 - 多视角审议
    
    多个成员从不同视角分析问题，可选交叉评审
    """
    import time
    import logging
    logger = logging.getLogger(__name__)
    
    start_time = time.time()
    
    try:
        config = await get_model_config(db, request.model_config_id, current_user)
        
        # 创建 AgentLoop
        from app.modules.agent import AgentLoop
        from app.modules.tools import ToolRegistry, register_builtin_tools
        
        tool_registry = ToolRegistry()
        register_builtin_tools(tool_registry)
        
        from app.api.chat import SimpleLLMProvider
        provider = SimpleLLMProvider(config=config)
        
        agent_loop = AgentLoop(
            provider=provider,
            tools=tool_registry,
            model=config.model_name,
            max_iterations=10,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            user_role=current_user.role,
        )
        
        # 创建 WorkflowEngine
        from app.modules.agent import WorkflowEngine
        engine = WorkflowEngine(agent_loop=agent_loop)
        
        # 执行 Council
        members = [m.dict() for m in request.members]
        result = await engine.run_council(
            question=request.question,
            members=members,
            cross_review=request.cross_review,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return WorkflowResponse(
            success=True,
            message="Council 执行成功",
            result=result,
            latency_ms=latency_ms,
        )
        
    except Exception as e:
        logger.error(f"Council failed: {e}")
        return WorkflowResponse(
            success=False,
            message=f"执行失败: {str(e)}",
            latency_ms=int((time.time() - start_time) * 1000),
        )
