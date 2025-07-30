from app.core.database import Base
from sqlalchemy import JSON, Column, Integer, String, Text, Date


class Movie(Base):
    """
    SQLAlchemy model for the 'movies' table.
    """

    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    overview = Column(Text, nullable=True)
    poster_path = Column(String, nullable=True)
    genres = Column(JSON, nullable=True)
    release_date = Column(Date, nullable=True)
    backdrop_path = Column(String, nullable=True)
