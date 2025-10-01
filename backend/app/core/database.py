from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

sync_engine = create_engine(settings.SYNC_DATABASE_URL)

async_engine = create_async_engine(settings.DATABASE_URL)

AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)

SessionLocal = sessionmaker(bind=sync_engine)

Base = declarative_base()


async def get_async_db() -> AsyncSession:
    """Dependency to get an async database session."""
    async with AsyncSessionLocal() as session:
        yield session


def get_db():
    db = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)()
    try:
        yield db
    finally:
        db.close()
