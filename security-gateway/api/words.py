"""
词库管理 API

提供词库的增删改查和批量导入功能。
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from schemas.security import WordCreate, WordUpdate, WordResponse
from services.word_service import WordService
from services.filter_service import FilterService
from core.deps import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["words"])


@router.get("/words")
async def list_words(
    word_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    scope: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """词库列表"""
    service = WordService()
    words, total = await service.list_words(
        db, word_type=word_type, is_active=is_active, scope=scope,
        skip=skip, limit=limit
    )
    return {"items": words, "total": total}


@router.post("/words", response_model=WordResponse, status_code=201)
async def create_word(
    data: WordCreate,
    db: AsyncSession = Depends(get_db),
):
    """新增词"""
    service = WordService()
    word = await service.create(
        db,
        word=data.word,
        word_type=data.word_type,
        category=data.category,
        severity=data.severity,
        description=data.description,
        is_active=data.is_active,
        scope=data.scope,
        organization_id=data.organization_id,
    )
    # 热加载词库
    try:
        await FilterService().reload_engines(db)
    except Exception as e:
        logger.warning(f"词库热重载失败: {e}")
    return word


@router.get("/words/{word_id}", response_model=WordResponse)
async def get_word(
    word_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取单个词"""
    service = WordService()
    word = await service.get_by_id(db, word_id)
    if not word:
        raise HTTPException(status_code=404, detail="词不存在")
    return word


@router.put("/words/{word_id}", response_model=WordResponse)
async def update_word(
    word_id: int,
    data: WordUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新词"""
    service = WordService()
    update_data = data.model_dump(exclude_unset=True)
    word = await service.update(db, word_id, **update_data)
    if not word:
        raise HTTPException(status_code=404, detail="词不存在")
    # 热加载词库
    try:
        await FilterService().reload_engines(db)
    except Exception as e:
        logger.warning(f"词库热重载失败: {e}")
    return word


@router.delete("/words/{word_id}")
async def delete_word(
    word_id: int,
    db: AsyncSession = Depends(get_db),
):
    """删除词"""
    service = WordService()
    success = await service.delete(db, word_id)
    if not success:
        raise HTTPException(status_code=404, detail="词不存在")
    # 热加载词库
    try:
        await FilterService().reload_engines(db)
    except Exception as e:
        logger.warning(f"词库热重载失败: {e}")
    return {"success": True}


@router.post("/words/batch", response_model=list[WordResponse])
async def batch_import_words(
    words: list[WordCreate],
    db: AsyncSession = Depends(get_db),
):
    """批量导入词"""
    service = WordService()
    words_data = [w.model_dump() for w in words]
    imported = await service.batch_create(db, words_data)
    # 热加载词库
    try:
        await FilterService().reload_engines(db)
    except Exception as e:
        logger.warning(f"词库热重载失败: {e}")
    return imported
