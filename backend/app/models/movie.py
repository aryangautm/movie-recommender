from sqlalchemy import Column, Integer, String, Text, JSON
from app.core.database import Base


class Movie(Base):
    """
    SQLAlchemy model for the 'movies' table.
    """

    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)  # This is the TMDb ID
    title = Column(String, index=True)
    overview = Column(Text, nullable=True)
    release_year = Column(Integer, nullable=True)
    poster_path = Column(String, nullable=True)
    genres = Column(JSON, nullable=True)
