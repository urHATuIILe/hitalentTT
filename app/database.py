from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings


class Base(DeclarativeBase):
    pass


_async_engine = None
_async_session_local = None
_sync_engine = None
_sync_session_local = None


def _get_async_engine():
    global _async_engine
    if _async_engine is None:
        kwargs = {"echo": settings.DEBUG, "pool_pre_ping": True}
        if "sqlite" not in settings.DATABASE_URL:
            kwargs["pool_size"] = 10
            kwargs["max_overflow"] = 20
        _async_engine = create_async_engine(settings.DATABASE_URL, **kwargs)
    return _async_engine


def _get_async_session_local():
    global _async_session_local
    if _async_session_local is None:
        _async_session_local = async_sessionmaker(
            bind=_get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_local


def _get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(
            settings.SYNC_DATABASE_URL,
            echo=settings.DEBUG,
            pool_pre_ping=True,
        )
    return _sync_engine


def _get_sync_session_local():
    global _sync_session_local
    if _sync_session_local is None:
        _sync_session_local = sessionmaker(
            bind=_get_sync_engine(),
            autocommit=False,
            autoflush=False,
        )
    return _sync_session_local


async def get_db() -> AsyncSession:
    session_local = _get_async_session_local()
    async with session_local() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    engine = _get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    global _async_engine
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
