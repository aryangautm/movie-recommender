import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class VoteType(enum.Enum):
    DIRECT_LINK = "direct_link"
    LLM_AGREEMENT = "llm_agreement"


class VoteLog(Base):
    __tablename__ = "votes_log"

    id = Column(Integer, primary_key=True, index=True)
    fingerprint_id = Column(String, nullable=False, index=True)

    source_movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    target_movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)

    vote_type = Column(Enum(VoteType), nullable=False)
    reference_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
