"""
Database connection management.

Подключение к PostgreSQL через SQLAlchemy.
Поддерживает синхронный и асинхронный режимы.
"""

import os
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session

from .models import Base


# =============================================================================
# Конфигурация
# =============================================================================

def get_database_url(async_mode: bool = False) -> str:
    """
    Получить URL базы данных из переменных окружения.
    
    Переменные:
    - DATABASE_URL — полный URL (приоритет)
    - DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME — отдельные параметры
    """
    # Проверяем полный URL
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Для async нужен asyncpg драйвер
        if async_mode and database_url.startswith("postgresql://"):
            return database_url.replace("postgresql://", "postgresql+asyncpg://")
        return database_url
    
    # Собираем из отдельных параметров
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "newvoice")
    password = os.getenv("DB_PASSWORD", "newvoice_secret_2026")
    database = os.getenv("DB_NAME", "newvoice")
    
    driver = "postgresql+asyncpg" if async_mode else "postgresql+psycopg2"
    return f"{driver}://{user}:{password}@{host}:{port}/{database}"


# =============================================================================
# Синхронное подключение
# =============================================================================

_engine = None
_SessionLocal = None


def get_engine():
    """Получить синхронный engine (singleton)."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            get_database_url(async_mode=False),
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Проверка соединения перед использованием
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )
    return _engine


def get_session_factory():
    """Получить фабрику сессий (singleton)."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
        )
    return _SessionLocal


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Контекстный менеджер для получения сессии БД.
    
    Использование:
        with get_db() as db:
            company = db.query(Company).first()
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# =============================================================================
# Асинхронное подключение
# =============================================================================

_async_engine = None
_AsyncSessionLocal = None


def get_async_engine():
    """Получить асинхронный engine (singleton)."""
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine(
            get_database_url(async_mode=True),
            pool_size=5,
            max_overflow=10,
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )
    return _async_engine


def get_async_session_factory():
    """Получить асинхронную фабрику сессий (singleton)."""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            bind=get_async_engine(),
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _AsyncSessionLocal


@asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронный контекстный менеджер для получения сессии БД.
    
    Использование:
        async with get_async_db() as db:
            result = await db.execute(select(Company))
            company = result.scalar_one_or_none()
    """
    AsyncSessionLocal = get_async_session_factory()
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# =============================================================================
# Инициализация
# =============================================================================

def init_db():
    """
    Создать все таблицы в базе данных.
    
    Обычно не нужно — таблицы создаются через init_db.sql при старте Docker.
    Но полезно для тестов или локальной разработки.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


async def init_async_db():
    """Асинхронная версия init_db."""
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created (async)")


# =============================================================================
# Утилиты
# =============================================================================

def check_connection() -> bool:
    """Проверить подключение к БД."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def check_async_connection() -> bool:
    """Асинхронная проверка подключения."""
    try:
        engine = get_async_engine()
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
