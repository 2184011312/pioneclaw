"""
权限相关的 Pydantic Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PermissionBase(BaseModel):
    """权限基础 Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="权限名称")
    code: str = Field(..., min_length=1, max_length=100, description="权限代码")
    description: Optional[str] = Field(None, max_length=500, description="权限描述")
    type: str = Field(default="app", description="权限类型: menu/system/app/api")
    resource: str = Field(default="", max_length=50, description="资源名称")
    action: str = Field(default="", max_length=20, description="操作类型")
    parent_id: Optional[str] = Field(None, description="父权限ID")
    sort_order: int = Field(default=0, description="排序")


class PermissionCreate(PermissionBase):
    """创建权限 Schema"""
    pass


class PermissionUpdate(BaseModel):
    """更新权限 Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    type: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    parent_id: Optional[str] = None
    menu_id: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class PermissionInDB(PermissionBase):
    """数据库中的权限 Schema"""
    id: str
    menu_id: Optional[str] = None
    is_system: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PermissionTree(PermissionInDB):
    """权限树 Schema"""
    children: List["PermissionTree"] = []


class PermissionSimple(BaseModel):
    """简化权限 Schema"""
    id: str
    name: str
    code: str
    resource: str
    action: str

    class Config:
        from_attributes = True


class PermissionListResponse(BaseModel):
    """权限列表响应"""
    items: List[PermissionInDB]
    total: int


class RolePermissionsUpdate(BaseModel):
    """角色权限更新 Schema"""
    permission_ids: List[str] = Field(..., description="权限ID列表")


class UserPermissionsResponse(BaseModel):
    """用户权限响应"""
    user_id: int
    permissions: List[str] = Field(default_factory=list, description="权限代码列表")
    is_super_admin: bool = False
    is_org_admin: bool = False


# 解决循环引用
PermissionTree.model_rebuild()