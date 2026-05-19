"""
Approval Schema
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

from app.models.approval import ApprovalStatus, ApprovalType


class ApprovalCreate(BaseModel):
    """创建审批请求"""
    approval_type: ApprovalType
    title: str
    description: Optional[str] = None
    resource_type: str  # skill / wiki / document
    resource_id: str
    target_scope: str   # org / system
    target_org_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ApprovalReview(BaseModel):
    """审批操作"""
    approved: bool
    review_comment: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: int
    approval_type: str
    status: str
    title: str
    description: Optional[str] = None
    requester_id: int
    requester_name: Optional[str] = None
    requester_org_id: Optional[str] = None
    reviewer_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_comment: Optional[str] = None
    resource_type: str
    resource_id: str
    target_scope: str
    target_org_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApprovalBrief(BaseModel):
    """审批简要"""
    id: int
    approval_type: str
    status: str
    title: str
    resource_type: str
    target_scope: str
    created_at: datetime
