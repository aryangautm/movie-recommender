from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.crud.crud_request_log import crud_request_log
from app.schemas.request_log import RequestLogResponse, RequestLogStats, TrafficStats

router = APIRouter()


@router.get("/recent", response_model=List[RequestLogResponse])
async def get_recent_logs(
    limit: int = Query(
        default=100, le=1000, description="Maximum number of logs to return"
    ),
    hours_back: int = Query(default=24, le=168, description="Hours to look back"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get recent request logs.

    Useful for monitoring recent API activity and debugging issues.
    """
    try:
        logs = await crud_request_log.get_recent_logs(
            db=db, limit=limit, hours_back=hours_back
        )
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch logs: {str(e)}")


@router.get("/errors", response_model=List[RequestLogResponse])
async def get_error_logs(
    limit: int = Query(
        default=100, le=1000, description="Maximum number of error logs to return"
    ),
    hours_back: int = Query(default=24, le=168, description="Hours to look back"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get recent error logs (status codes >= 400).

    Useful for monitoring API errors and debugging issues.
    """
    try:
        logs = await crud_request_log.get_error_logs(
            db=db, limit=limit, hours_back=hours_back
        )
        return logs
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch error logs: {str(e)}"
        )


@router.get("/stats/endpoints", response_model=List[RequestLogStats])
async def get_endpoint_stats(
    hours_back: int = Query(default=24, le=168, description="Hours to look back"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get request statistics grouped by endpoint.

    Provides insights into API usage patterns, performance, and error rates.
    """
    try:
        stats = await crud_request_log.get_stats_by_endpoint(
            db=db, hours_back=hours_back
        )
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch endpoint stats: {str(e)}"
        )


@router.get("/stats/traffic", response_model=List[TrafficStats])
async def get_traffic_stats(
    hours_back: int = Query(default=24, le=168, description="Hours to look back"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get request traffic statistics grouped by hour.

    Useful for understanding traffic patterns and peak usage times.
    """
    try:
        stats = await crud_request_log.get_traffic_by_hour(db=db, hours_back=hours_back)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch traffic stats: {str(e)}"
        )


@router.delete("/cleanup")
async def cleanup_old_logs(
    days_to_keep: int = Query(
        default=30, ge=1, le=365, description="Number of days of logs to keep"
    ),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Clean up old request logs to prevent database bloat.

    This endpoint should be called periodically (e.g., via a cron job) to maintain
    database performance. Only logs older than the specified number of days will be deleted.
    """
    try:
        deleted_count = await crud_request_log.cleanup_old_logs(
            db=db, days_to_keep=days_to_keep
        )
        return {
            "message": f"Successfully deleted {deleted_count} old log entries",
            "deleted_count": deleted_count,
            "days_kept": days_to_keep,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup logs: {str(e)}")

