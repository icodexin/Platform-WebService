from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin

class UserRole(Base, TimestampMixin):
    """用户-角色关系表"""
    __tablename__ = 'user_role'

    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'), primary_key=True, comment="用户ID"
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey('role.id', ondelete='CASCADE'), primary_key=True, comment="角色ID"
    )