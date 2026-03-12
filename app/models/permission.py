from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TimestampMixin


class Permission(Base, TimestampMixin):
    """权限表"""
    __tablename__ = 'permission'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, comment="权限唯一标识代码"
    )
    name: Mapped[str] = mapped_column(
        String(128), comment="权限名称"
    )

    roles = relationship(
        "Role", secondary="role_permission", back_populates="permissions", lazy="selectin"
    )
    rabbitmq_bindings = relationship(
        "RabbitMQPermissionBinding",
        back_populates="permission",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
