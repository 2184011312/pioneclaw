"""
审计日志 API

提供审计日志的查询和统计功能。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from schemas.security import AuditLogResponse, AuditLogListResponse
from services.audit_service import AuditService
from core.deps import get_db

router = APIRouter(tags=["audit"])


@router.get("/audit-logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    check_point: Optional[str] = None,
    risk_level: Optional[str] = None,
    user_id: Optional[int] = None,
    event_type: Optional[str] = None,
    action: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """审计日志查询

    支持按检查点、风险级别、用户、时间范围等维度筛选。
    """
    service = AuditService()
    logs, total = await service.list_logs(
        db,
        check_point=check_point,
        risk_level=risk_level,
        user_id=user_id,
        event_type=event_type,
        action=action,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit,
    )

    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
    )
