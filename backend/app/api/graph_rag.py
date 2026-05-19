"""
知识图谱 RAG API

端点:
- POST /graph-rag/index   索引文档到知识图谱
- POST /graph-rag/query   查询(指定模式)
- GET  /graph-rag/stats   图谱统计
- DELETE /graph-rag/clear 清空图谱
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models import User
from app.modules.graph_rag import GraphRAGClient, GraphRAGSettings

router = APIRouter(prefix="/graph-rag", tags=["知识图谱"])


# 全局客户端实例
_graph_rag_client: Optional[GraphRAGClient] = None


def get_graph_rag_client() -> GraphRAGClient:
    """获取 GraphRAG 客户端实例"""
    global _graph_rag_client
    if _graph_rag_client is None:
        _graph_rag_client = GraphRAGClient()
    return _graph_rag_client


# ==================== 请求/响应模型 ====================

class IndexRequest(BaseModel):
    """索引请求"""
    content: str
    doc_id: Optional[str] = None


class BatchIndexRequest(BaseModel):
    """批量索引请求"""
    documents: List[str]


class QueryRequest(BaseModel):
    """查询请求"""
    query: str
    mode: str = "hybrid"  # local, global, hybrid, naive, mix


class QueryResponse(BaseModel):
    """查询响应"""
    result: str
    mode: str


class StatsResponse(BaseModel):
    """统计响应"""
    working_dir: str
    graph_exists: bool
    vector_exists: bool
    nodes: Optional[int] = None
    edges: Optional[int] = None


class MessageResponse(BaseModel):
    """消息响应"""
    success: bool
    message: str


# ==================== 端点 ====================

@router.post("/index", response_model=MessageResponse)
async def index_document(
    data: IndexRequest,
    current_user: User = Depends(get_current_user),
):
    """索引文档到知识图谱"""
    client = get_graph_rag_client()
    result = await client.index_document(data.content, data.doc_id)
    return MessageResponse(
        success=result["success"],
        message=result["message"],
    )


@router.post("/index/batch", response_model=MessageResponse)
async def index_batch(
    data: BatchIndexRequest,
    current_user: User = Depends(get_current_user),
):
    """批量索引文档"""
    client = get_graph_rag_client()
    result = await client.index_batch(data.documents)
    return MessageResponse(
        success=result["success"],
        message=result["message"],
    )


@router.post("/query", response_model=QueryResponse)
async def query_graph(
    data: QueryRequest,
    current_user: User = Depends(get_current_user),
):
    """查询知识图谱"""
    client = get_graph_rag_client()
    result = await client.query(data.query, data.mode)
    return QueryResponse(
        result=result["result"],
        mode=result["mode"],
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    current_user: User = Depends(get_current_user),
):
    """获取知识图谱统计"""
    client = get_graph_rag_client()
    stats = await client.stats()
    return StatsResponse(
        working_dir=stats.get("working_dir", ""),
        graph_exists=stats.get("graph_exists", False),
        vector_exists=stats.get("vector_exists", False),
        nodes=stats.get("nodes"),
        edges=stats.get("edges"),
    )


@router.delete("/clear", response_model=MessageResponse)
async def clear_graph(
    current_user: User = Depends(get_current_user),
):
    """清空知识图谱"""
    client = get_graph_rag_client()
    result = await client.clear()
    return MessageResponse(
        success=result["success"],
        message=result["message"],
    )
