import datetime
import enum
from zoneinfo import ZoneInfo

from app.core.database import Base
from sqlalchemy import Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB


class TriggerSource(str, enum.Enum):
    MANUAL = "MANUAL"
    RECOMMENDATION = "RECOMMENDATION"
    TRENDING = "TRENDING"


class ProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    PROCESSING = "PROCESSING"


class ProcessingQueue(Base):
    """
    SQLAlchemy model for the 'processing_queue' table.
    """

    __tablename__ = "processing_queue"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source_movie_id = Column(Integer, nullable=True)
    title = Column(String, index=True)
    release_year = Column(Integer, nullable=True, default=None)
    properties = Column(JSONB, nullable=True)
    trigger_source = Column(
        Enum(TriggerSource),
        nullable=True,
        index=True,
    )
    status = Column(
        Enum(ProcessingStatus),
        nullable=False,
        default=ProcessingStatus.PENDING,
        index=True,
    )
    failure_reason = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(ZoneInfo("Asia/Kolkata")),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.now(ZoneInfo("Asia/Kolkata")),
        onupdate=datetime.datetime.now(ZoneInfo("Asia/Kolkata")),
        nullable=False,
    )
