"""
安全网关数据库模型
"""

import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime, Integer, JSON, Enum as SQLEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class WordType(str, enum.Enum):
    SENSITIVE = "sensitive"
    RISK = "risk"
    ALLOW = "allow"


class WordLibrary(Base):
    """词库管理表"""

    __tablename__ = "word_libraries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    word: Mapped[str] = mapped_column(String(500), index=True)
    word_type: Mapped[str] = mapped_column(SQLEnum(WordType), index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    severity: Mapped[int] = mapped_column(Integer, default=1)  # 1-5
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    scope: Mapped[str] = mapped_column(String(20), default="system")
    organization_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    creator_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class SecurityAuditLog(Base):
    """安全审计日志表"""

    __tablename__ = "security_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    check_point: Mapped[str] = mapped_column(String(50), index=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    risk_level: Mapped[str] = mapped_column(
        String(20), default="low", index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True
    )
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    agent_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content_preview: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    action: Mapped[str] = mapped_column(String(20))
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    matched_rules: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    request_trace_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )


class SecurityConfig(Base):
    """运行时配置表"""

    __tablename__ = "security_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scope_type: Mapped[str] = mapped_column(String(20), default="global")
    scope_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    config_key: Mapped[str] = mapped_column(String(100))
    config_value: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
