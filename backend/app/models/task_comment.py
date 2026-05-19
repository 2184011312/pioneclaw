"""
任务评论模型
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, ForeignKey, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import uuid


def generate_uuid() -> str:
    return str(uuid.uuid4())


class TaskComment(Base):
    """任务评论"""
    __tablename__ = "task_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[Optional[str]] = mapped_column(ForeignKey("task_comments.id"), nullable=True)  # 回复

    # @提及
    mentions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)  # 用户ID列表

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(default=False)

    # 关系
    task: Mapped["Task"] = relationship(back_populates="comments")
    user: Mapped["User"] = relationship()
    parent: Mapped[Optional["TaskComment"]] = relationship(
        "TaskComment",
        back_populates="replies",
        remote_side=[id],
        foreign_keys=[parent_id]
    )
    replies: Mapped[List["TaskComment"]] = relationship(
        "TaskComment",
        back_populates="parent",
        foreign_keys=[parent_id]
    )

    def __repr__(self):
        return f"<TaskComment(id={self.id}, task_id={self.task_id})>"