from datetime import datetime
import sys
from typing import Callable

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import settings

# 初始化异步数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,        # 连接池大小
    max_overflow=10,    # 连接池溢出大小
    pool_pre_ping=True, # 连接池预先ping
)

# 异步会话工厂
AsyncSessionLocal: Callable[[], AsyncSession] = async_sessionmaker(
    engine,
    autoflush=True,         # 在查询前，自动将内存中的修改刷新到数据库
    autocommit=False,       # 自动提交事务
    expire_on_commit=True,  # 在事务提交后使会话中的对象过期
)


# ORM基类
class Base(DeclarativeBase):
    metadata = MetaData()


# 时间戳混入
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="created time"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="updated time"
    )


# 数据库依赖注入
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
