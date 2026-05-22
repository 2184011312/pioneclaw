"""
组织相关的 Pydantic Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class OrganizationBase(BaseModel):
    """组织基础 Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="组织名称")
    code: str = Field(..., min_length=1, max_length=50, description="组织代码")
    description: Optional[str] = Field(None, max_length=500, description="组织描述")
    type: str = Field(default="department", description="组织类型: company/department/team")
    parent_id: Optional[str] = Field(None, description="父组织ID")
    manager_id: Optional[int] = Field(None, description="管理者ID")


class OrganizationCreate(OrganizationBase):
    """创建组织 Schema"""
    pass


class OrganizationUpdate(BaseModel):
    """更新组织 Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    type: Optional[str] = None
    parent_id: Optional[str] = None
    manager_id: Optional[int] = None
    status: Optional[str] = None
    meta_data: Optional[dict] = None


class OrganizationInDB(OrganizationBase):
    """数据库中的组织 Schema"""
    id: str
    level: int
    path: str
    status: str
    meta_data: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationTree(OrganizationInDB):
    """组织树 Schema"""
    children: List["OrganizationTree"] = []
    user_count: int = 0


class OrganizationSimple(BaseModel):
    """简化组织 Schema（用于下拉选择）"""
    id: str
    name: str
    code: str
    level: int
    parent_id: Optional[str] = None

    class Config:
        from_attributes = True


class OrganizationListResponse(BaseModel):
    """组织列表响应"""
    items: List[OrganizationInDB]
    total: int


# 解决循环引用
OrganizationTree.model_rebuild()
