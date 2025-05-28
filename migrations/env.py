from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from database import Base  # Импортируем Base из ваших моделей
from models import ToDo, User
import asyncio

# Ваши модели должны быть импортированы для autogenerate
from models import *  # Импорт всех моделей

# Настройка для асинхронной работы
config = context.config
fileConfig(config.config_file_name) if config.config_file_name else None
target_metadata = Base.metadata  # Указываем метаданные моделей

def run_migrations_offline():
    """Синхронные миграции для офлайн-режима"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    """Асинхронные миграции для онлайн-режима"""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        future=True
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

def do_run_migrations(connection):
    # Синхронный контекст для Alembic
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True
    )
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    # Запуск асинхронного кода в event loop
    asyncio.run(run_migrations_online())