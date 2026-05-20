"""
审计日志服务

负责安全审计日志的写入和查询。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from models.security import SecurityAuditLog
from config import settings


class AuditService:
    """审计服务"""

    async def log(
        self,
        session: AsyncSession,
        check_point: str,
        result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> SecurityAuditLog:
        """写入审计日志

        Args:
            session: 数据库会话
            check_point: 检查点 (input/output/tool)
            result: 安全检测结果 {action, reason, risk_level, matched_rules}
            context: 上下文信息 {user_id, username, session_id, agent_id, request_trace_id}
        """
        context = context or {}

        # 内容摘要：取前 200 字符
        content_preview = context.get("content_preview", "")
        if not content_preview:
            text = context.get("text", "")
            content_preview = text[:200] if text else ""

        log = SecurityAuditLog(
            check_point=check_point,
            event_type=self._infer_event_type(result.get("matched_rules", [])),
            risk_level=result.get("risk_level", "low"),
            user_id=context.get("user_id"),
            username=context.get("username"),
            session_id=context.get("session_id"),
            agent_id=context.get("agent_id"),
            content_preview=content_preview,
            action=result.get("action", "allow"),
            reason=result.get("reason"),
            matched_rules=result.get("matched_rules"),
            request_trace_id=context.get("request_trace_id"),
            extra_data=context.get("extra_data"),
        )

        session.add(log)
        # TODO: 高并发场景下，同步 commit 可能成为瓶颈。
        # 后续优化：使用后台批量写入（如 asyncio.Queue + 定时刷盘），
        # 或使用 asyncio.create_task 异步写入（牺牲一定一致性换取吞吐量）。
        await session.commit()
        await session.refresh(log)
        return log

    async def list_logs(
        self,
        session: AsyncSession,
        check_point: Optional[str] = None,
        risk_level: Optional[str] = None,
        user_id: Optional[int] = None,
        event_type: Optional[str] = None,
        action: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[SecurityAuditLog], int]:
        """分页查询审计日志"""
        query = select(SecurityAuditLog)
        count_query = select(func.count()).select_from(SecurityAuditLog)

        conditions = []
        if check_point:
            conditions.append(SecurityAuditLog.check_point == check_point)
        if risk_level:
            conditions.append(SecurityAuditLog.risk_level == risk_level)
        if user_id:
            conditions.append(SecurityAuditLog.user_id == user_id)
        if event_type:
            conditions.append(SecurityAuditLog.event_type == event_type)
        if action:
            conditions.append(SecurityAuditLog.action == action)
        if start_time:
            conditions.append(SecurityAuditLog.created_at >= start_time)
        if end_time:
            conditions.append(SecurityAuditLog.created_at <= end_time)

        if conditions:
            condition = and_(*conditions)
            query = query.where(condition)
            count_query = count_query.where(condition)

        # 清理过期日志
        cutoff = datetime.now(timezone.utc) - timedelta(
            days=settings.LOG_RETENTION_DAYS
        )
        query = query.where(SecurityAuditLog.created_at >= cutoff)
        count_query = count_query.where(SecurityAuditLog.created_at >= cutoff)

        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        query = (
            query.order_by(SecurityAuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(query)
        logs = result.scalars().all()
        return list(logs), total

    @staticmethod
    def _infer_event_type(matched_rules: List[Dict[str, Any]]) -> str:
        """从匹配规则推断事件类型"""
        if not matched_rules:
            return "pass"
        types = set(r.get("type", "") for r in matched_rules)
        if "model_detection" in types:
            return "model_detection"
        if any(t in types for t in ["sensitive", "risk"]):
            return "word_match"
        if any(t in types for t in ["id_card", "phone", "bank_card"]):
            return "regex_match"
        return "unknown"
