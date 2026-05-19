"""
聊天会话 API — 列表、消息历史、删除
"""
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core import get_db
from app.models import User, Session, SessionMessage
from app.api.auth import get_current_active_user

router = APIRouter(prefix="/chat/sessions", tags=["会话管理"])


@router.get("")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取当前用户的会话列表"""
    result = await db.execute(
        select(Session)
        .where(Session.user_id == current_user.id, Session.status == "active")
        .order_by(desc(Session.updated_at))
    )
    sessions = result.scalars().all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "agent_id": s.agent_id,
            "runner_id": s.runner_id,
            "message_count": s.message_count,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        }
        for s in sessions
    ]


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取会话详情（含消息）"""
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    msgs_result = await db.execute(
        select(SessionMessage)
        .where(SessionMessage.session_id == session_id)
        .order_by(SessionMessage.created_at)
    )
    messages = msgs_result.scalars().all()

    return {
        "id": session.id,
        "title": session.title,
        "workspace_path": session.workspace_path,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "tool_calls": m.tool_calls,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }


@router.post("")
async def create_session(
    title: str = "新对话",
    agent_id: Optional[int] = None,
    runner_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建新会话"""
    session = Session(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=title,
        agent_id=agent_id,
        runner_id=runner_id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {"id": session.id, "title": session.title, "created_at": session.created_at.isoformat()}


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除会话"""
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # Soft delete — mark as archived
    session.status = "archived"
    await db.commit()
    return {"message": "会话已删除"}


@router.post("/{session_id}/messages")
async def save_message(
    session_id: str,
    role: str = Query(...),
    content: str = Query(default=""),
    tool_calls: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """保存消息到会话"""
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    import json as _json

    msg = SessionMessage(
        session_id=session_id,
        role=role,
        content=content or "",
        tool_calls=_json.loads(tool_calls) if tool_calls else None,
    )
    db.add(msg)
    session.message_count = (session.message_count or 0) + 1

    # Auto-title from first user message
    if role == "user" and session.title == "新对话":
        session.title = content[:50] + ("..." if len(content) > 50 else "")

    await db.commit()
    return {"id": msg.id, "role": msg.role, "created_at": msg.created_at.isoformat()}
