"""
Workspace Schema
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class WorkspaceSettings(BaseModel):
    """工作空间设置"""
    output_language: str = "中文"
    default_model_config_id: Optional[int] = None
    user_name: str = ""
    user_address: str = ""
    ai_name: str = "小助手"
    personality: str = "professional"
    custom_personality: str = ""


class WorkspaceCreate(BaseModel):
    name: str
    path: str = ""
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class WorkspaceSettingsUpdate(BaseModel):
    """工作空间设置更新"""
    output_language: Optional[str] = None
    default_model_config_id: Optional[int] = None
    user_name: Optional[str] = None
    user_address: Optional[str] = None
    ai_name: Optional[str] = None
    personality: Optional[str] = None
    custom_personality: Optional[str] = None


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    path: str
    description: Optional[str] = None
    owner_id: int
    organization_id: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_default: bool
    is_active: bool
    last_active_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkspaceBrief(BaseModel):
    """简要信息（用于下拉选择）"""
    id: int
    name: str
    is_default: bool
    is_active: bool
