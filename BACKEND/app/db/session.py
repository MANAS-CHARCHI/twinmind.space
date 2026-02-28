from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Async engine (used by FastAPI)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base model class
class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session