from app.core.database import Base
from sqlalchemy import JSON, Column, Float, ForeignKey, Integer, String


class LlmRecommendation(Base):
    __tablename__ = "llm_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    source_movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    trigger_keywords_hash = Column(String, nullable=False, index=True)
    recommended_movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    llm_justification = Column(JSON, nullable=False)
    llm_score = Column(Float)
    user_votes = Column(Integer, default=0, nullable=False)
