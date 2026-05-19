"""
TaskFlow API - 持久化工作流接口

功能：
- 创建/启动工作流
- 执行步骤、暂停/恢复
- 完成/失败
- 列表查询、恢复未完成流程
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.core import get_db
from app.api.auth import get_current_active_user
from app.models import User
from app.modules.agent.taskflow import (
    TaskFlowManager,
    RevisionConflictError,
    InvalidStateTransition,
)

router = APIRouter(prefix="/taskflow", tags=["持久化工作流"])


# ==================== 请求/响应模型 ====================

class FlowCreateRequest(BaseModel):
    name: str
    goal: str
    owner_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class FlowStartRequest(BaseModel):
    initial_step: str = ""


class FlowStepRequest(BaseModel):
    step_name: str
    step_result: Optional[Dict[str, Any]] = None


class FlowWaitRequest(BaseModel):
    wait_reason: str
    checkpoint: Optional[Dict[str, Any]] = None


class FlowResumeRequest(BaseModel):
    resume_input: Optional[Dict[str, Any]] = None
    expected_revision: Optional[int] = None


class FlowFinishRequest(BaseModel):
    final_result: Optional[Dict[str, Any]] = None


class FlowFailRequest(BaseModel):
    error: str


class FlowAddChildRequest(BaseModel):
    child_task_id: str


class FlowResponse(BaseModel):
    id: str
    name: str
    goal: str
    current_step: str
    state: str
    owner_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Dict[str, Any] = {}
    wait_reason: Optional[str] = None
    revision: int = 1
    child_task_ids: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class FlowListResponse(BaseModel):
    flows: List[FlowResponse]
    total: int


class FlowRecoverResponse(BaseModel):
    recovered: List[FlowResponse]
    count: int


def _flow_to_response(flow) -> FlowResponse:
    return FlowResponse(
        id=flow.id,
        name=flow.name,
        goal=flow.goal,
        current_step=flow.current_step,
        state=flow.state,
        owner_id=flow.owner_id,
        session_id=flow.session_id,
        context=flow.context or {},
        wait_reason=flow.wait_reason,
        revision=flow.revision,
        child_task_ids=flow.child_task_ids or [],
        created_at=flow.created_at,
        updated_at=flow.updated_at,
        completed_at=flow.completed_at,
    )


# ==================== 接口 ====================

@router.post("", response_model=FlowResponse)
async def create_flow(
    req: FlowCreateRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_active_user),
):
    mgr = TaskFlowManager(db)
    flow = await mgr.create(
        name=req.name,
        goal=req.goal,
        owner_id=req.owner_id,
        session_id=req.session_id,
        context=req.context,
    )
    return _flow_to_response(flow)


@router.post("/{flow_id}/start", response_model=FlowResponse)
async def start_flow(
    flow_id: str,
    req: FlowStartRequest = FlowStartRequest(),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_active_user),
):
    mgr = TaskFlowManager(db)
    try:
        flow = await mgr.start(flow_id, initial_step=req.initial_step)
    except InvalidStateTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _flow_to_response(flow)


@router.post("/{flow_id}/step", response_model=FlowResponse)
async def run_step(
    flow_id: str,
    req: FlowStepRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_active_user),
):
    mgr = TaskFlowManager(db)
    try:
        flow = await mgr.run_step(flow_id, step_name=req.step_name, step_result=req.step_result)
    except InvalidStateTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _flow_to_response(flow)


@router.post("/{flow_id}/wait", response_model=FlowResponse)
async def set_waiting(
    flow_id: str,
    req: FlowWaitRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_active_user),
):
    mgr = TaskFlowManager(db)
    try:
        flow = await mgr.set_waiting(flow_id, wait_reason=req.wait_reason, checkpoint=req.checkpoint)
    except InvalidStateTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _flow_to_response(flow)


@router.post("/{flow_id}/resume", response_model=FlowResponse)
async def resume_flow(
    flow_id: str,
    req: FlowResumeRequest = FlowResumeRequest(),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_active_user),
):
    mgr = TaskFlowManager(db)
    try:
        flow = await mgr.resume(
            flow_id,
            resume_input=req.resume_input,
            expected_revision=req.expected_revision,
        )
    except RevisionConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except InvalidStateTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _flow_to_response(flow)


@router.post("/{flow_id}/finish", response_model=FlowResponse)
async def finish_flow(
    flow_id: str,
    req: FlowFinishRequest = FlowFinishRequest(),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_active_user),
):
    mgr = TaskFlowManager(db)
    try:
        flow = await mgr.finish(flow_id, final_result=req.final_result)
    except InvalidStateTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _flow_to_response(flow)


@router.post("/{flow_id}/fail", response_model=FlowResponse)
async def fail_flow(
    flow_id: str,
    req: FlowFailRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_active_user),
):
    mgr = TaskFlowManager(db)
    try:
        flow = await mgr.fail(flow_id, error=req.error)
    except InvalidStateTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _flow_to_response(flow)


@router.post("/{flow_id}/child", response_model=FlowResponse)
async def add_child_task(
    flow_id: str,
    req: FlowAddChildRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_active_user),
):
    mgr = TaskFlowManager(db)
    try:
        flow = await mgr.add_child_task(flow_id, child_task_id=req.child_task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _flow_to_response(flow)


@router.get("/{flow_id}", response_model=FlowResponse)
async def get_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_active_user),
):
    mgr = TaskFlowManager(db)
    flow = await mgr.get_flow(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="TaskFlow not found")
    return _flow_to_response(flow)


@router.get("", response_model=FlowListResponse)
async def list_flows(
    owner_id: Optional[str] = None,
    state: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_active_user),
):
    mgr = TaskFlowManager(db)
    flows, total = await mgr.list_flows(
        owner_id=owner_id,
        state=state,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )
    return FlowListResponse(
        flows=[_flow_to_response(f) for f in flows],
        total=total,
    )


@router.post("/recover", response_model=FlowRecoverResponse)
async def recover_pending(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_active_user),
):
    mgr = TaskFlowManager(db)
    recovered = await mgr.recover_pending()
    return FlowRecoverResponse(
        recovered=[_flow_to_response(f) for f in recovered],
        count=len(recovered),
    )
