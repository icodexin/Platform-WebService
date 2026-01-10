from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TimestampMixin

class Role(Base, TimestampMixin):
    """角色表"""
    __tablename__ = 'role'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, comment="角色唯一标识代码"
    )
    name: Mapped[str] = mapped_column(
        String(128), comment="角色名称"
    )

    users = relationship(
        "User", secondary="user_role", back_populates="roles", lazy="selectin"
    )
    permissions = relationship(
        "Permission", secondary="role_permission", back_populates="roles", lazy="selectin"
    )