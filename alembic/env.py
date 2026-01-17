"""
Alembic Environment Configuration.

Настроен для работы с NEW-VOICE 2.0:
- Читает DATABASE_URL из .env
- Подключает все SQLAlchemy модели для autogenerate
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Добавляем src в путь для импорта моделей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Загружаем .env
from dotenv import load_dotenv
load_dotenv()

# Импортируем Base и все модели
from database.models import Base

# Alembic Config object
config = context.config

# Настраиваем логирование
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Подключаем метаданные моделей для autogenerate
target_metadata = Base.metadata


def get_url() -> str:
    """Получить URL базы данных из переменных окружения."""
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Alembic использует синхронный драйвер
        if "+asyncpg" in database_url:
            return database_url.replace("+asyncpg", "+psycopg2")
        if database_url.startswith("postgresql://"):
            return database_url.replace("postgresql://", "postgresql+psycopg2://")
        return database_url
    
    # Собираем из отдельных параметров
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "newvoice")
    password = os.getenv("DB_PASSWORD", "newvoice_secret_2026")
    database = os.getenv("DB_NAME", "newvoice")
    
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    Генерирует SQL без подключения к БД.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    Подключается к БД и применяет миграции.
    """
    # Переопределяем URL из .env
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Отслеживать изменения типов колонок
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
