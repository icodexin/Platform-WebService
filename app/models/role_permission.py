from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class RolePermission(Base, TimestampMixin):
    """角色权限关联表"""
    __tablename__ = 'role_permission'

    role_id: Mapped[int] = mapped_column(
        ForeignKey('role.id', ondelete='CASCADE'), primary_key=True, comment="角色ID"
    )
    permission_id: Mapped[int] = mapped_column(
        ForeignKey('permission.id', ondelete='CASCADE'), primary_key=True, comment="权限ID"
    )
