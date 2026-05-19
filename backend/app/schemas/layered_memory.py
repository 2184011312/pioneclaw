"""
分层记忆 Pydantic Schema — L0/L1/L2 三级记忆体系
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.layered_memory import MemoryLayer, ContextType


# ==================== 存储/创建 ====================
class LayeredMemoryStore(BaseModel):
    """存储记忆请求 — 自动生成 L0/L1"""
    content: str = Field(..., min_length=1, description="L2 全文内容")
    name: str = Field(..., min_length=1, max_length=200, description="记忆名称")
    context_type: str = Field(default="memory", description="上下文类型: memory/resource/skill")
    uri: Optional[str] = Field(None, description="自定义 URI，不填则自动生成")
    parent_uri: Optional[str] = Field(None, description="父 URI（用于关联）")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    source: Optional[str] = Field(None, description="来源")
    importance: int = Field(default=3, ge=1, le=5, description="重要性 1-5")
    session_id: Optional[str] = Field(None, description="所属会话 ID")
    agent_id: Optional[int] = Field(None, description="关联 Agent ID")


class LayeredMemoryUpdate(BaseModel):
    """更新记忆请求"""
    content: Optional[str] = Field(None, min_length=1)
    name: Optional[str] = Field(None, max_length=200)
    context_type: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    importance: Optional[int] = Field(None, ge=1, le=5)
    is_active: Optional[bool] = None
    regenerate_tiers: bool = Field(default=True, description="是否重新生成 L0/L1")


# ==================== 检索 ====================
class LayeredMemoryRecall(BaseModel):
    """语义检索请求"""
    query: str = Field(..., min_length=1, description="查询文本")
    context_type: str = Field(default="all", description="类型筛选: all/memory/resource/skill")
    layers: Optional[List[int]] = Field(default=[2, 1], description="搜索层级，默认 L2+L1")
    top_k: int = Field(default=10, ge=1, le=50, description="返回数量")
    session_id: Optional[str] = Field(None, description="限定会话范围")
    agent_id: Optional[int] = Field(None, description="限定 Agent 范围")


class LayeredMemoryPromote(BaseModel):
    """L1→L2 提升请求"""
    uri: str = Field(..., description="L1 记忆 URI")


class LayeredMemoryEvict(BaseModel):
    """清理 L0 请求"""
    session_id: str = Field(..., description="要清理的会话 ID")


# ==================== 响应 ====================
class LayeredMemoryResponse(BaseModel):
    """单条记忆响应"""
    id: int
    uri: str
    parent_uri: Optional[str] = None
    layer: int
    context_type: str
    name: str
    abstract: Optional[str] = None
    overview: Optional[str] = None
    content: str
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    importance: int = 3
    access_count: int = 0
    session_id: Optional[str] = None
    user_id: int
    agent_id: Optional[int] = None
    vector_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LayeredMemoryBrief(BaseModel):
    """记忆简要（列表用，不含全文）"""
    id: int
    uri: str
    layer: int
    context_type: str
    name: str
    abstract: Optional[str] = None
    overview: Optional[str] = None
    importance: int = 3
    access_count: int = 0
    source: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LayeredMemoryStats(BaseModel):
    """分层记忆统计"""
    total: int = 0
    l0_count: int = 0
    l1_count: int = 0
    l2_count: int = 0
    by_type: dict = {}
    by_source: dict = {}
    vector_count: int = 0


class LayeredMemoryListResponse(BaseModel):
    """记忆列表响应"""
    items: List[LayeredMemoryBrief]
    total: int


class RecallResultItem(BaseModel):
    """检索结果单项"""
    uri: str
    name: str
    layer: int
    context_type: str
    text: str
    score: float
    abstract: Optional[str] = None
    overview: Optional[str] = None


class LayeredMemoryRecallResponse(BaseModel):
    """检索响应"""
    results: List[RecallResultItem]
    intent: Optional[str] = None
    total: int
