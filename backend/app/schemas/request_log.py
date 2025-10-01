from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict

from app.models.request_log import RequestMethod


class RequestLogBase(BaseModel):
    """Base schema for request logs."""

    method: RequestMethod
    path: str
    query_params: Optional[Dict] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    referer: Optional[str] = None
    headers: Optional[Dict] = None
    status_code: int
    response_size: Optional[int] = None
    processing_time: Optional[float] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_size: Optional[int] = None
    error_message: Optional[str] = None


class RequestLogCreate(RequestLogBase):
    """Schema for creating request logs."""

    pass


class RequestLogResponse(RequestLogBase):
    """Schema for request log responses."""

    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class RequestLogStats(BaseModel):
    """Schema for request log statistics by endpoint."""

    path: str
    method: RequestMethod
    request_count: int
    avg_processing_time: Optional[float] = None
    max_processing_time: Optional[float] = None
    error_count: int
    error_rate: float  # Percentage


class TrafficStats(BaseModel):
    """Schema for traffic statistics by hour."""

    hour: datetime
    request_count: int
    error_count: int

