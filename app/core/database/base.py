from datetime import datetime
from typing import Callable

from sqlalchemy import Column, TIMESTAMP
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# 初始化数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL,  # 数据库连接字符串
    pool_size=20,  # 连接池大小
    max_overflow=30,  # 连接池溢出大小
    pool_pre_ping=True  # 连接池预先ping
)


class TimestampMixin:
    """
    时间戳字段混入类
    用于自动添加创建和更新时间戳
    """
    created_at = Column(TIMESTAMP, default=datetime.now, comment="创建时间")
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now, comment="更新时间")


# 声明式基类配置
Base = declarative_base(
    cls=TimestampMixin,  # 自定义基类
)

# 会话工厂配置
AsyncSessionLocal: Callable[..., AsyncSession] = sessionmaker(
    bind=engine,  # 绑定引擎
    class_=AsyncSession,  # 使用异步会话
    autoflush=False,  # 在每次查询前自动刷新会话中的对象
    autocommit=False,  # 自动提交事务
    expire_on_commit=True  # 在事务提交后使对象过期
)


# 数据库依赖注入
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
