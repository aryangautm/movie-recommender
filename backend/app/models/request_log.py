import enum
from datetime import datetime

from app.core.database import Base
from sqlalchemy import Column, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.sql import func


class RequestMethod(str, enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class RequestLog(Base):
    """
    SQLAlchemy model for logging HTTP requests to the API.

    This model captures comprehensive request information for monitoring,
    analytics, and debugging purposes.
    """

    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Request details
    method = Column(
        Enum(RequestMethod, name="requestmethod", create_type=False),
        nullable=False,
        index=True,
    )
    path = Column(String(512), nullable=False, index=True)
    query_params = Column(JSONB, nullable=True)

    # Client information
    client_ip = Column(INET, nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    referer = Column(String(512), nullable=True)

    # Request headers (filtered for security)
    headers = Column(JSONB, nullable=True)

    # Response details
    status_code = Column(Integer, nullable=False, index=True)
    response_size = Column(Integer, nullable=True)  # in bytes

    # Performance metrics
    processing_time = Column(Float, nullable=True)  # in seconds

    # Timestamps
    timestamp = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), index=True
    )

    # Optional: User identification (if you have authentication)
    user_id = Column(String(64), nullable=True, index=True)
    session_id = Column(String(128), nullable=True, index=True)

    # Request body size (for monitoring large requests)
    request_size = Column(Integer, nullable=True)  # in bytes

    # Error tracking
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<RequestLog(id={self.id}, method={self.method}, path={self.path}, status={self.status_code})>"
