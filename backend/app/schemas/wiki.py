"""
Wiki 相关的 Pydantic Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class WikiBase(BaseModel):
    """Wiki 基础 Schema"""
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    content: str = Field(default="", description="内容")
    path: str = Field(..., min_length=1, max_length=500, description="路径")
    parent_id: Optional[str] = Field(None, description="父Wiki ID")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")
    status: str = Field(default="published", description="状态: draft/published/archived")
    doc_type: str = Field(default="markdown", description="文档类型: markdown/text/pdf/url")
    source: Optional[str] = Field(None, description="来源 URL 或文件路径")
    scope: str = Field(default="user", description="权限范围: system/org/user")


class WikiCreate(WikiBase):
    """创建 Wiki Schema"""
    organization_id: Optional[str] = None


class WikiUpdate(BaseModel):
    """更新 Wiki Schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    path: Optional[str] = Field(None, min_length=1, max_length=500)
    parent_id: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    doc_type: Optional[str] = None
    source: Optional[str] = None
    scope: Optional[str] = None
    change_summary: Optional[str] = Field(None, max_length=500, description="变更摘要")


class WikiInDB(WikiBase):
    """数据库中的 Wiki Schema"""
    id: str
    version: int
    scope: str = "user"
    chunk_count: int = 0
    is_indexed: bool = False
    created_by: int
    organization_id: Optional[str] = None
    meta_data: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WikiDetail(WikiInDB):
    """Wiki 详情（包含作者信息）"""
    author_name: Optional[str] = None
    organization_name: Optional[str] = None


class WikiTree(WikiInDB):
    """Wiki 树 Schema"""
    children: List["WikiTree"] = []


class WikiVersionInDB(BaseModel):
    """Wiki 版本 Schema"""
    id: str
    wiki_id: str
    version: int
    title: str
    content: str
    change_summary: Optional[str] = None
    created_by: int
    created_at: datetime
    author_name: Optional[str] = None

    class Config:
        from_attributes = True


class WikiVersionListResponse(BaseModel):
    """Wiki 版本列表响应"""
    items: List[WikiVersionInDB]
    total: int


class WikiListResponse(BaseModel):
    """Wiki 列表响应"""
    items: List[WikiInDB]
    total: int


class WikiSearchResult(BaseModel):
    """Wiki 搜索结果"""
    id: str
    title: str
    path: str
    highlight: Optional[str] = None  # 高亮摘要
    score: Optional[float] = None  # 搜索得分


class WikiSearchResponse(BaseModel):
    """Wiki 搜索响应"""
    items: List[WikiSearchResult]
    total: int


class WikiSemanticSearchRequest(BaseModel):
    """Wiki 语义搜索请求"""
    query: str = Field(..., min_length=1, description="搜索查询")
    top_k: int = Field(default=10, ge=1, le=100, description="返回数量")
    threshold: float = Field(default=0.5, ge=0, le=1, description="相似度阈值")


class WikiSemanticSearchResult(BaseModel):
    """Wiki 语义搜索结果"""
    id: str
    title: str
    path: str
    content_snippet: str  # 内容片段
    score: float  # 相似度得分
    doc_type: str
    tags: List[str] = []


class WikiSemanticSearchResponse(BaseModel):
    """Wiki 语义搜索响应"""
    items: List[WikiSemanticSearchResult]
    total: int


class WikiImportRequest(BaseModel):
    """Wiki 导入请求"""
    path: str = Field(..., description="目标路径")
    title: Optional[str] = Field(None, description="标题（不指定则从内容提取）")
    content: str = Field(..., description="Markdown 内容")
    tags: Optional[List[str]] = Field(default_factory=list)
    doc_type: str = Field(default="markdown", description="文档类型")
    source: Optional[str] = Field(None, description="来源")
    scope: str = Field(default="user", description="权限范围")


class WikiChunkRequest(BaseModel):
    """Wiki 分块请求"""
    chunk_size: int = Field(default=500, ge=100, le=2000, description="分块大小（字符）")
    chunk_overlap: int = Field(default=50, ge=0, le=200, description="分块重叠")


class WikiChunkResponse(BaseModel):
    """Wiki 分块响应"""
    wiki_id: str
    chunk_count: int
    chunks: List[dict]  # [{index, content, start, end}]


# 解决循环引用
WikiTree.model_rebuild()