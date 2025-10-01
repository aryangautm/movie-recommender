from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.request_log import RequestLog, RequestMethod


class CRUDRequestLog:
    """
    CRUD operations for RequestLog model.

    Provides both sync and async methods for logging and querying request data.
    """

    async def create_async(
        self,
        db: AsyncSession,
        *,
        method: RequestMethod,
        path: str,
        query_params: Optional[Dict] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        referer: Optional[str] = None,
        headers: Optional[Dict] = None,
        status_code: int,
        response_size: Optional[int] = None,
        processing_time: Optional[float] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_size: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> RequestLog:
        """Create a new request log entry asynchronously."""
        db_obj = RequestLog(
            method=method,
            path=path,
            query_params=query_params,
            client_ip=client_ip,
            user_agent=user_agent,
            referer=referer,
            headers=headers,
            status_code=status_code,
            response_size=response_size,
            processing_time=processing_time,
            user_id=user_id,
            session_id=session_id,
            request_size=request_size,
            error_message=error_message,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    def create_sync(
        self,
        db: Session,
        *,
        method: RequestMethod,
        path: str,
        query_params: Optional[Dict] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        referer: Optional[str] = None,
        headers: Optional[Dict] = None,
        status_code: int,
        response_size: Optional[int] = None,
        processing_time: Optional[float] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_size: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> RequestLog:
        """Create a new request log entry synchronously."""
        db_obj = RequestLog(
            method=method,
            path=path,
            query_params=query_params,
            client_ip=client_ip,
            user_agent=user_agent,
            referer=referer,
            headers=headers,
            status_code=status_code,
            response_size=response_size,
            processing_time=processing_time,
            user_id=user_id,
            session_id=session_id,
            request_size=request_size,
            error_message=error_message,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    async def get_recent_logs(
        self,
        db: AsyncSession,
        *,
        limit: int = 100,
        hours_back: int = 24,
    ) -> List[RequestLog]:
        """Get recent request logs."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        result = await db.execute(
            select(RequestLog)
            .filter(RequestLog.timestamp >= cutoff_time)
            .order_by(desc(RequestLog.timestamp))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_error_logs(
        self,
        db: AsyncSession,
        *,
        limit: int = 100,
        hours_back: int = 24,
    ) -> List[RequestLog]:
        """Get recent error logs (status codes >= 400)."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        result = await db.execute(
            select(RequestLog)
            .filter(
                and_(RequestLog.timestamp >= cutoff_time, RequestLog.status_code >= 400)
            )
            .order_by(desc(RequestLog.timestamp))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_stats_by_endpoint(
        self,
        db: AsyncSession,
        *,
        hours_back: int = 24,
    ) -> List[Dict]:
        """Get request statistics grouped by endpoint."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        result = await db.execute(
            select(
                RequestLog.path,
                RequestLog.method,
                func.count(RequestLog.id).label("request_count"),
                func.avg(RequestLog.processing_time).label("avg_processing_time"),
                func.max(RequestLog.processing_time).label("max_processing_time"),
                func.count(func.case([(RequestLog.status_code >= 400, 1)])).label(
                    "error_count"
                ),
            )
            .filter(RequestLog.timestamp >= cutoff_time)
            .group_by(RequestLog.path, RequestLog.method)
            .order_by(desc("request_count"))
        )

        return [
            {
                "path": row.path,
                "method": row.method,
                "request_count": row.request_count,
                "avg_processing_time": (
                    float(row.avg_processing_time) if row.avg_processing_time else None
                ),
                "max_processing_time": (
                    float(row.max_processing_time) if row.max_processing_time else None
                ),
                "error_count": row.error_count,
                "error_rate": (
                    (row.error_count / row.request_count) * 100
                    if row.request_count > 0
                    else 0
                ),
            }
            for row in result.fetchall()
        ]

    async def get_traffic_by_hour(
        self,
        db: AsyncSession,
        *,
        hours_back: int = 24,
    ) -> List[Dict]:
        """Get request traffic grouped by hour."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        result = await db.execute(
            select(
                func.date_trunc("hour", RequestLog.timestamp).label("hour"),
                func.count(RequestLog.id).label("request_count"),
                func.count(func.case([(RequestLog.status_code >= 400, 1)])).label(
                    "error_count"
                ),
            )
            .filter(RequestLog.timestamp >= cutoff_time)
            .group_by(func.date_trunc("hour", RequestLog.timestamp))
            .order_by("hour")
        )

        return [
            {
                "hour": row.hour,
                "request_count": row.request_count,
                "error_count": row.error_count,
            }
            for row in result.fetchall()
        ]

    async def cleanup_old_logs(
        self,
        db: AsyncSession,
        *,
        days_to_keep: int = 30,
    ) -> int:
        """Clean up old request logs to prevent database bloat."""
        cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)
        from sqlalchemy import delete

        result = await db.execute(
            delete(RequestLog).filter(RequestLog.timestamp < cutoff_time)
        )
        await db.commit()
        return result.rowcount


# Create a singleton instance
crud_request_log = CRUDRequestLog()
