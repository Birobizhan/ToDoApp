from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime, func, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base, engine
from enum import Enum
from sqlalchemy.dialects.postgresql import ENUM


class task_status(Enum):
    DONE = 'Выполнено'
    IN_PROGRESS = 'В процсессе'
    PLANNED = 'В планах'


status_enum = ENUM(task_status, name='task_status', create_type=True, validate_strings=True)


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    hash_password: Mapped[str] = mapped_column(String(200))
    todos: Mapped["ToDo"] = relationship('ToDo', back_populates='owner')


class ToDo(Base):
    __tablename__ = 'todos'
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(status_enum, default=task_status.PLANNED)
    description: Mapped[str] = mapped_column(String(1000))
    created: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    plan_date:  Mapped[Date] = mapped_column(Date)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    owner: Mapped[User] = relationship('User', back_populates='todos')


async def create_tables():
    async with engine.begin() as conn:
        # Создание таблиц
        await conn.run_sync(Base.metadata.create_all)


